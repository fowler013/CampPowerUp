"""Synthetic, isolated tests: never import the app's startup database initializer."""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from functools import wraps
from types import SimpleNamespace

import pytest
from flask import Flask, jsonify, request, session

from registration_form import discord_attendance as attendance


DAY = "2026-11-23"
LABEL = "Camp Power-Up Thanksgiving 2026 - November 23-24, 2026"
PARENT = "1" * 32
STAFF = "2" * 32


@pytest.fixture
def camp(tmp_path, monkeypatch):
    database = tmp_path / "synthetic.db"
    with sqlite3.connect(database) as connection:
        connection.execute("""CREATE TABLE registrations
            (id INTEGER PRIMARY KEY, submission_id TEXT UNIQUE, camp_session TEXT,
             child_first_name TEXT, parent_email TEXT)""")
        connection.executemany("INSERT INTO registrations VALUES (?,?,?,?,?)", [
            (1, "REG_ONE", LABEL, "Secret camper", "secret@example.test"),
            (2, "REG_TWO", LABEL, "Other family", "other@example.test"),
            (3, "HIST_OLD", LABEL, "Historical", "old@example.test"),
            (4, "REG_OTHER", "Other session", "Wrong session", "wrong@example.test"),
        ])
        connection.execute("""CREATE TABLE attendance
            (submission_id TEXT, date TEXT, status TEXT, checked_in_at TEXT)""")
        connection.execute("INSERT INTO attendance VALUES ('REG_ONE',?,'present','legacy')", (DAY,))
    monkeypatch.setenv("DISCORD_ATTENDANCE_ENABLED", "true")
    monkeypatch.setenv("DISCORD_ATTENDANCE_PARENT_TOKEN", PARENT)
    monkeypatch.setenv("DISCORD_ATTENDANCE_STAFF_TOKEN", STAFF)
    monkeypatch.setenv("DISCORD_ATTENDANCE_GUILD_ID", "100")
    monkeypatch.setenv("DISCORD_ATTENDANCE_DATABASE_PATH", str(database))
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    monkeypatch.setenv("DISCORD_ATTENDANCE_STAFF_IDS", '["900"]')
    monkeypatch.setenv("DISCORD_ATTENDANCE_SESSIONS", json.dumps({
        "thanksgiving-2026": {"label": LABEL, "dates": [DAY, "2026-11-24"]},
    }))
    monkeypatch.setattr(attendance, "utc_now",
                        lambda: datetime(2026, 11, 23, 18, 0, tzinfo=timezone.utc))
    app = Flask(__name__)
    app.secret_key = "synthetic-only-session-signing-key-32"
    app.testing = True

    def admin_auth(function):
        @wraps(function)
        def guarded(*args, **kwargs):
            if not session.get("admin_logged_in"):
                return jsonify(error="admin_required"), 401
            return function(*args, **kwargs)
        return guarded

    def admin_csrf(function):
        @wraps(function)
        def guarded(*args, **kwargs):
            if request.headers.get("X-CSRF-Token") != session.get("admin_csrf_token"):
                return jsonify(error="csrf_required"), 400
            return function(*args, **kwargs)
        return guarded

    attendance.register_discord_attendance(
        app, lambda: str(database), admin_auth, admin_csrf, lambda: "synthetic-admin")
    client = app.test_client()
    with client.session_transaction() as browser:
        browser["admin_logged_in"] = True
        browser["admin_csrf_token"] = "synthetic-csrf"
    return SimpleNamespace(app=app, client=client, database=database)


def headers(staff=False, user=None, key=None):
    result = {"Authorization": "Bearer " + (STAFF if staff else PARENT),
              "X-Discord-User-ID": user or ("900" if staff else "101"),
              "X-Discord-Guild-ID": "100"}
    if key:
        result["Idempotency-Key"] = key
    return result


def admin(camp, route, data):
    return camp.client.post(attendance.ADMIN_PREFIX + route, json=data,
                            headers={"X-CSRF-Token": "synthetic-csrf"})


def link(camp, registration=1, user="10101010101010101", active=True):
    return admin(camp, "/links", {
        "registration_id": registration, "session_id": "thanksgiving-2026",
        "discord_user_id": user, "active": active,
        "verification_reference": "manual-record-001",
    })


def camper_id(camp):
    response = link(camp)
    assert response.status_code == 200
    return response.json["camper_id"]


def payload(camper, action="arrival", **extra):
    return {"camper_id": camper, "session_id": "thanksgiving-2026",
            "date": DAY, "action": action, **extra}


def post(camp, data, staff=False, key="interaction-1", user=None):
    return camp.client.post(attendance.PREFIX + ("/confirmations" if staff else "/requests"),
                            json=data, headers=headers(staff, user, key))


def query(camper, day=DAY):
    return {"camper_id": camper, "session_id": "thanksgiving-2026", "date": day}


def read(camp, sql):
    with sqlite3.connect(camp.database) as connection:
        return connection.execute(sql).fetchall()


def roster(camp, camper, name="Synthetic authorized pickup"):
    return admin(camp, "/pickup-roster", {
        "camper_id": camper, "session_id": "thanksgiving-2026",
        "active": True, "display_name": name,
        "parent_confirmation_reference": "parent-confirmed-001",
    })


def test_disabled_and_malformed_configuration_fail_closed(camp, monkeypatch):
    monkeypatch.delenv("DISCORD_ATTENDANCE_ENABLED")
    response = camp.client.get(attendance.PREFIX + "/campers", headers=headers())
    assert response.status_code == 503
    assert response.json == {"error": {"code": "attendance_disabled"}}
    assert read(camp, "SELECT name FROM sqlite_master WHERE name LIKE 'discord_%'") == []
    monkeypatch.setenv("DISCORD_ATTENDANCE_ENABLED", "true")
    monkeypatch.setenv("DISCORD_ATTENDANCE_STAFF_IDS", "{}")
    assert camp.client.get(attendance.PREFIX + "/campers", headers=headers()).status_code == 503


def test_credentials_scopes_guild_staff_allowlist(camp):
    camper = camper_id(camp)
    for changed, expected in [
        ({"Authorization": ""}, 401),
        ({"X-Discord-Guild-ID": "999"}, 403),
        ({"X-Discord-User-ID": "not-a-user"}, 401),
    ]:
        assert camp.client.get(attendance.PREFIX + "/status",
            query_string=query(camper), headers={**headers(), **changed}).status_code == expected
    assert post(camp, payload(camper), staff=True, user="101").status_code == 403
    assert camp.client.post(attendance.PREFIX + "/confirmations",
        json=payload(camper, expected_version=0), headers=headers(key="x")).status_code == 401
    assert camp.client.post(attendance.PREFIX + "/requests",
        json=payload(camper), headers=headers(staff=True, key="x")).status_code == 401


def test_no_self_linking_no_family_leak_and_revocation(camp):
    camper = camper_id(camp)
    assert camp.client.get(attendance.PREFIX + "/campers",
        query_string={"session_id": "thanksgiving-2026"}, headers=headers(user="202")).json == {"campers": []}
    for handle in [camper, "unknown"]:
        response = camp.client.get(attendance.PREFIX + "/status",
            query_string=query(handle), headers=headers(user="202"))
        assert response.status_code == 404
        assert response.json == {"error": {"code": "not_found"}}
    assert post(camp, payload(camper), user="202").status_code == 404
    assert camp.client.get(attendance.PREFIX + "/pickup-roster",
        query_string=query(camper), headers=headers()).status_code == 401
    assert link(camp, registration=3).status_code == 404
    assert link(camp, registration=4).status_code == 404
    assert post(camp, payload(camper)).status_code == 200
    assert link(camp, active=False).status_code == 200
    assert post(camp, payload(camper)).status_code == 404  # no cached replay after revocation
    with camp.client.session_transaction() as browser:
        browser.clear()
    assert link(camp).status_code == 401


def test_admin_csrf_and_secure_signing_key(camp):
    assert camp.client.post(attendance.ADMIN_PREFIX + "/links", json={}).status_code == 400
    assert admin(camp, "/links", {
        "registration_id": 1, "session_id": "thanksgiving-2026",
        "discord_user_id": "12345", "active": True,
        "verification_reference": "manual-record-001",
    }).status_code == 400
    assert admin(camp, "/links", {
        "registration_id": 1, "session_id": "thanksgiving-2026",
        "discord_user_id": "10101010101010101", "active": True,
    }).status_code == 400
    assert camp.client.post(attendance.ADMIN_PREFIX + "/links", json={
        "registration_id": 1, "session_id": "thanksgiving-2026",
        "discord_user_id": "10101010101010101", "active": True,
        "verification_reference": "manual-record-001",
    }).status_code == 400
    camp.app.secret_key = "dev-key-change-in-production"
    with camp.client.session_transaction() as browser:
        browser["admin_logged_in"] = True
        browser["admin_csrf_token"] = "synthetic-csrf"
    assert link(camp).status_code == 503


def test_full_flow_requires_explicit_staff_and_current_pickup_roster(camp):
    camper = camper_id(camp)
    initial = camp.client.get(attendance.PREFIX + "/status",
        query_string=query(camper), headers=headers()).json
    assert initial["state"] == "not_arrived"  # legacy 'present' is not a trusted arrival
    response = post(camp, payload(camper))
    assert response.json["state"] == "arrival_requested"
    assert response.json["version"] == 1
    pending = camp.client.get(attendance.PREFIX + "/pending",
        query_string=query(camper), headers=headers(staff=True))
    assert pending.json["items"] == [response.json]
    assert post(camp, payload(camper, "pickup"), key="too-early").status_code == 409
    assert post(camp, payload(camper, expected_version=1), staff=True, key="staff-arrival").json["state"] == "present"
    assert post(camp, payload(camper, "pickup"), key="pickup").json["state"] == "pickup_requested"
    release = payload(camper, "release", expected_version=3)
    assert post(camp, release, staff=True, key="release").status_code == 400
    pickup = roster(camp, camper).json["pickup_id"]
    release.update(pickup_id=pickup, roster_verified=True)
    released = post(camp, release, staff=True, key="release")
    assert released.json["state"] == "released"
    assert released.json["version"] == 4
    assert post(camp, release, staff=True, key="release").json == released.json
    assert post(camp, payload(camper), key="after-release").status_code == 409
    events = read(camp, "SELECT actor_id,action,before_state,after_state,occurred_at FROM discord_attendance_audit WHERE date IS NOT NULL")
    assert [row[1] for row in events] == ["arrival", "arrival", "pickup", "release"]
    assert [row[0] for row in events] == ["101", "900", "101", "900"]
    assert all(row[4].endswith("+00:00") for row in events)
    assert read(camp, "SELECT * FROM attendance") == [("REG_ONE", DAY, "present", "legacy")]
    assert not any(word in released.get_data(as_text=True) for word in ["Secret", "example.test", "Synthetic authorized"])
    assert released.headers["Cache-Control"] == "no-store"


def test_roster_must_match_camper_and_not_be_revoked(camp):
    first = camper_id(camp)
    second = link(camp, registration=2, user="20202020202020202").json["camper_id"]
    pickup = roster(camp, second).json["pickup_id"]
    assert post(camp, payload(first, expected_version=0), staff=True).status_code == 200
    release = payload(first, "release", expected_version=1, pickup_id=pickup, roster_verified=True)
    assert post(camp, release, staff=True, key="release").status_code == 404
    pickup = roster(camp, first).json["pickup_id"]
    listing = camp.client.get(attendance.PREFIX + "/pickup-roster",
        query_string=query(first), headers=headers(staff=True)).json
    assert listing == {"entries": [{"pickup_id": pickup, "display_name": "Synthetic authorized pickup"}]}
    assert admin(camp, "/pickup-roster", {
        "camper_id": first, "session_id": "thanksgiving-2026", "active": False,
        "pickup_id": pickup, "parent_confirmation_reference": "parent-revoked-001",
    }).status_code == 200
    release["pickup_id"] = pickup
    assert post(camp, release, staff=True, key="release").status_code == 404


def test_idempotency_content_binding_and_duplicate_noop(camp):
    camper = camper_id(camp)
    first = post(camp, payload(camper))
    assert post(camp, payload(camper)).json == first.json
    assert post(camp, payload(camper, "pickup")).json == {"error": {"code": "idempotency_conflict"}}
    assert post(camp, payload(camper), key="new-interaction").json == first.json
    assert len(read(camp, "SELECT * FROM discord_attendance_audit WHERE date IS NOT NULL")) == 1
    assert post(camp, payload(camper, expected_version=0), staff=True, key="stale").json == {"error": {"code": "stale_version"}}


def test_simultaneous_parent_and_staff_operations(camp):
    camper = camper_id(camp)

    def parent(_):
        with camp.app.test_client() as client:
            return client.post(attendance.PREFIX + "/requests", json=payload(camper),
                               headers=headers(key="same-interaction"))

    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(parent, range(4)))
    assert all(result.status_code == 200 and result.json["version"] == 1 for result in results)
    assert len(read(camp, "SELECT * FROM discord_attendance_audit WHERE date IS NOT NULL")) == 1

    def staff(number):
        with camp.app.test_client() as client:
            return client.post(attendance.PREFIX + "/confirmations",
                json=payload(camper, expected_version=1),
                headers=headers(staff=True, key=f"staff-{number}"))

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(staff, range(2)))
    assert sorted(result.status_code for result in results) == [200, 409]
    assert len(read(camp, "SELECT * FROM discord_attendance_audit WHERE date IS NOT NULL")) == 2


@pytest.mark.parametrize("extra", [
    {"date": "2026-11-24"}, {"date": "2026-11-25"}, {"session_id": "unknown"},
    {"action": []}, {"action": "release"}, {"camper_id": 1}, {"unrecognized": True},
])
def test_invalid_or_noncurrent_requests_do_not_mutate(camp, extra):
    camper = camper_id(camp)
    assert post(camp, payload(camper, **extra)).status_code in (400, 404)
    assert read(camp, "SELECT * FROM discord_attendance") == []


def test_central_day_and_isolated_second_day(camp, monkeypatch):
    camper = camper_id(camp)
    # 01:00 UTC on Nov 24 is still Nov 23 in Central.
    monkeypatch.setattr(attendance, "utc_now",
        lambda: datetime(2026, 11, 24, 1, tzinfo=timezone.utc))
    assert post(camp, payload(camper)).status_code == 200
    monkeypatch.setattr(attendance, "utc_now",
        lambda: datetime(2026, 11, 24, 16, tzinfo=timezone.utc))
    assert post(camp, payload(camper, date="2026-11-24"), key="day-two").json["version"] == 1
    assert len(read(camp, "SELECT * FROM discord_attendance")) == 2


def test_migration_restart_and_transaction_rollback(camp, monkeypatch):
    camper = camper_id(camp)
    original = attendance.audit

    def broken_audit(*args, **kwargs):
        raise sqlite3.OperationalError("synthetic transaction failure")

    monkeypatch.setattr(attendance, "audit", broken_audit)
    assert post(camp, payload(camper)).status_code == 503
    assert read(camp, "SELECT * FROM discord_attendance") == []
    assert read(camp, "SELECT * FROM discord_attendance_idempotency") == []
    monkeypatch.setattr(attendance, "audit", original)
    assert post(camp, payload(camper)).status_code == 200
    with attendance.transaction(str(camp.database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM discord_attendance").fetchone()[0] == 1
    assert read(camp, "SELECT version FROM discord_attendance_schema") == [(1,)]


def test_removed_or_reassigned_registration_loses_access(camp):
    camper = camper_id(camp)
    with sqlite3.connect(camp.database) as connection:
        connection.execute("UPDATE registrations SET camp_session='Different' WHERE id=1")
    assert post(camp, payload(camper)).status_code == 404
    assert camp.client.get(attendance.PREFIX + "/staff-status",
        query_string=query(camper), headers=headers(staff=True)).status_code == 404


def test_unknown_schema_fails_closed(camp):
    camper = camper_id(camp)
    with sqlite3.connect(camp.database) as connection:
        connection.execute("UPDATE discord_attendance_schema SET version=2")
    assert post(camp, payload(camper)).json == {"error": {"code": "attendance_unavailable"}}
    assert read(camp, "SELECT * FROM discord_attendance") == []
    assert read(camp, "SELECT version FROM discord_attendance_schema") == [(2,)]


def test_pinned_database_and_volume_fail_closed(camp, monkeypatch, tmp_path):
    monkeypatch.setenv("DISCORD_ATTENDANCE_DATABASE_PATH", str(tmp_path / "missing.db"))
    assert link(camp).status_code == 503
    assert not (tmp_path / "missing.db").exists()
    monkeypatch.setenv("DISCORD_ATTENDANCE_DATABASE_PATH", str(camp.database))
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "synthetic")
    monkeypatch.delenv("RAILWAY_VOLUME_MOUNT_PATH", raising=False)
    assert link(camp).status_code == 503
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(tmp_path / "missing-volume"))
    assert link(camp).status_code == 503
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", str(tmp_path))
    assert link(camp).status_code == 200
    missing = tmp_path / "not-created.db"
    with pytest.raises(sqlite3.OperationalError):
        with attendance.transaction(str(missing)):
            pass
    assert not missing.exists()


def test_request_shape_and_direct_release(camp):
    camper = camper_id(camp)
    assert camp.client.post(attendance.PREFIX + "/requests", data="[]",
        content_type="application/json", headers=headers(key="array")).status_code == 400
    assert post(camp, payload(camper), key=None).status_code == 400
    assert post(camp, payload(camper, expected_version=True), staff=True).status_code == 400
    assert post(camp, payload(camper, expected_version=0), staff=True).json["state"] == "present"
    pickup = roster(camp, camper).json["pickup_id"]
    response = post(camp, payload(camper, "release", expected_version=1,
        pickup_id=pickup, roster_verified=True), staff=True, key="direct-release")
    assert response.json["state"] == "released"


def test_actual_registration_app_wiring_uses_same_database(camp, monkeypatch, tmp_path):
    # Import-time initialization is confined to a synthetic working directory.
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("SECRET_KEY", "synthetic-registration-signing-key-32")
    monkeypatch.setenv("ADMIN_PASSWORD", "synthetic-only-admin-password")
    from registration_form import app as registration_app

    monkeypatch.setattr(registration_app, "get_database_path", lambda: str(camp.database))
    monkeypatch.setitem(registration_app.app.config, "SECRET_KEY",
                        "synthetic-registration-signing-key-32")
    monkeypatch.setitem(registration_app.app.config, "TESTING", True)
    client = registration_app.app.test_client()
    # Prove the generic before-request configuration reader is not called:
    # it would open storage before the attendance authorization gate.
    def unexpected_configuration_read(*args):
        raise AssertionError("Attendance must own its authorization and session scope")

    monkeypatch.setattr(registration_app, "load_configurations", unexpected_configuration_read)
    with client.session_transaction() as browser:
        browser["admin_logged_in"] = True
        browser["admin_csrf_token"] = "synthetic-csrf"
    response = client.post(attendance.ADMIN_PREFIX + "/links", json={
        "registration_id": 1, "session_id": "thanksgiving-2026",
        "discord_user_id": "101", "active": True,
        "verification_reference": "verified-manually-001",
    }, headers={"X-CSRF-Token": "synthetic-csrf"})
    assert response.status_code == 200
    response = client.post(attendance.PREFIX + "/requests",
        json=payload(response.json["camper_id"]), headers=headers(key="wired"))
    assert response.status_code == 200
    assert response.json["state"] == "arrival_requested"
    assert len(read(camp, "SELECT * FROM discord_attendance")) == 1
    monkeypatch.delenv("DISCORD_ATTENDANCE_ENABLED")
    assert client.get(attendance.PREFIX + "/campers").json == {"error": {"code": "attendance_disabled"}}
