"""Synthetic-only coverage of Discord-independent pickups and the shared ledger."""

import json
import sqlite3
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest

from registration_form import app as registration_app
from registration_form import discord_attendance as attendance
from test_admin_workflows import camp, enable_discord_attendance, CURRENT, OTHER, HEADERS, TOKEN


DAY = "2026-11-23"
SESSION = "thanksgiving-2026"
USER = "10101010101010101"
PARENT_HEADERS = {
    "Authorization": "Bearer synthetic-parent-token-000000000000",
    "X-Discord-User-ID": USER,
    "X-Discord-Guild-ID": "100",
}
BOT_STAFF_HEADERS = {
    "Authorization": "Bearer synthetic-staff-token-0000000000000",
    "X-Discord-User-ID": "900",
    "X-Discord-Guild-ID": "100",
}


@pytest.fixture
def staff_camp(camp, monkeypatch):
    enable_discord_attendance(camp, monkeypatch)
    monkeypatch.setattr(attendance, "utc_now",
                        lambda: datetime(2026, 11, 23, 18, tzinfo=timezone.utc))
    assert camp.client.get(attendance.CAMP_DAY_PREFIX + "/roster").status_code == 200
    return camp


def rows(camp, sql):
    with closing(sqlite3.connect(camp.database)) as connection:
        return connection.execute(sql).fetchall()


def add_pickup(camp, target_id, **overrides):
    body = {
        "registration_id": target_id, "session_id": SESSION,
        "active": True, "display_name": "Synthetic approved adult",
        "parent_confirmation_reference": "parent-ok-014",
        **overrides,
    }
    return camp.client.post(attendance.ADMIN_PREFIX + "/pickup-roster", json=body, headers=HEADERS)


def confirm(camp, registration_id, action="arrival", version=0, key="web-confirm-001", **extra):
    return camp.client.post(attendance.CAMP_DAY_PREFIX + "/confirmations", json={
        "registration_id": registration_id, "session_id": SESSION, "date": DAY,
        "action": action, "expected_version": version, **extra,
    }, headers={**HEADERS, "Idempotency-Key": key})


def roster(camp, session=SESSION):
    return camp.client.get(attendance.CAMP_DAY_PREFIX + "/roster", query_string={"session_id": session})


def test_all_eligible_campers_are_visible_without_creating_handles_or_events(staff_camp):
    camp = staff_camp
    camp.add("REG_UNLINKED", parent_phone="555-0100", parent_email="private@example.test")
    camp.add("REG_OTHER", camp_session=OTHER)
    camp.add("HIST_OLD")
    response = roster(camp)
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json["date"] == DAY and response.json["write_enabled"] is True
    registration = response.json["registrations"][0]
    assert registration["submission_id"] == "REG_UNLINKED"
    assert registration["camper_id"] is None
    assert registration["status"]["state"] == "not_arrived"
    assert registration["status"]["version"] == 0
    assert len(response.json["registrations"]) == 1
    assert not any(word in response.get_data(as_text=True) for word in [
        "parent_email", "parent_phone", "medical", "private@example.test", "discord_user_id",
    ])
    assert rows(camp, "SELECT * FROM discord_campers") == []
    assert rows(camp, "SELECT * FROM discord_parent_links") == []
    assert rows(camp, "SELECT * FROM discord_attendance") == []
    assert rows(camp, "SELECT * FROM discord_attendance_audit") == []
    page = camp.client.get(attendance.CAMP_DAY_PREFIX)
    assert page.status_code == 200 and page.headers["Cache-Control"] == "no-store"
    assert b"shared admin account" in page.data
    assert b"No Discord account needed" in page.data
    assert registration_app.app.test_client().get(attendance.CAMP_DAY_PREFIX).status_code == 302
    assert registration_app.app.test_client().get(
        attendance.CAMP_DAY_PREFIX + "/roster", headers={"Accept": "application/json"},
    ).status_code == 401


def test_unlinked_pickup_web_arrival_later_discord_link_and_shared_release(staff_camp):
    camp = staff_camp
    registration_id = camp.add("REG_NO_DISCORD", child_first_name="Avery")
    other_id = camp.add("REG_STILL_UNLINKED", child_first_name="Blair")
    pickup = add_pickup(camp, registration_id)
    assert pickup.status_code == 200
    assert add_pickup(camp, other_id).status_code == 200
    initial = roster(camp).json["registrations"][0]
    camper = initial["camper_id"]
    assert camper and initial["status"]["state"] == "not_arrived"
    assert rows(camp, "SELECT * FROM discord_parent_links") == []
    assert rows(camp, "SELECT * FROM discord_attendance") == []
    arrival = confirm(camp, registration_id)
    assert arrival.status_code == 200
    assert arrival.json["state"] == "present" and arrival.json["version"] == 1
    link = camp.client.post(attendance.ADMIN_PREFIX + "/links", json={
        "registration_id": registration_id, "session_id": SESSION, "discord_user_id": USER,
        "active": True, "verification_reference": "parent-check-014",
    }, headers=HEADERS)
    assert link.status_code == 200 and link.json["camper_id"] == camper
    query = {"camper_id": camper, "session_id": SESSION, "date": DAY}
    assert camp.client.get(attendance.PREFIX + "/status", query_string=query,
                           headers=PARENT_HEADERS).json == arrival.json
    assert camp.client.get(attendance.PREFIX + "/campers", query_string={"session_id": SESSION},
                           headers=PARENT_HEADERS).json == {"campers": [{"camper_id": camper}]}
    request = camp.client.post(attendance.PREFIX + "/requests", json={**query, "action": "pickup"},
                               headers={**PARENT_HEADERS, "Idempotency-Key": "parent-request-001"})
    assert request.json["state"] == "pickup_requested" and request.json["version"] == 2
    assert roster(camp).json["registrations"][0]["status"] == request.json
    released = confirm(camp, registration_id, "release", 2, key="web-release-001",
                       pickup_id=pickup.json["pickup_id"], roster_verified=True)
    assert released.status_code == 200 and released.json["state"] == "released"
    assert released.json["version"] == 3
    for path, headers in [("/status", PARENT_HEADERS), ("/staff-status", BOT_STAFF_HEADERS)]:
        assert camp.client.get(attendance.PREFIX + path, query_string=query, headers=headers).json == released.json
    assert rows(camp, "SELECT COUNT(*) FROM discord_campers") == [(2,)]
    assert rows(camp, "SELECT actor_id,actor_type,action FROM discord_attendance_audit WHERE date IS NOT NULL") == [
        ("admin:test-admin", "admin_web", "arrival"),
        (USER, "parent", "pickup"),
        ("admin:test-admin", "admin_web", "release"),
    ]


def test_staff_direct_arrival_creates_no_parent_link_and_release_needs_verified_pickup(staff_camp):
    camp = staff_camp
    first = camp.add("REG_ONE")
    second = camp.add("REG_TWO")
    arrived = confirm(camp, first)
    assert arrived.status_code == 200
    assert rows(camp, "SELECT * FROM discord_parent_links") == []
    assert confirm(camp, first, "release", 1, key="missing-pickup").status_code == 400
    wrong_pickup = add_pickup(camp, second).json["pickup_id"]
    assert confirm(camp, first, "release", 1, key="wrong-pickup",
                   pickup_id=wrong_pickup, roster_verified=True).status_code == 404
    pickup = add_pickup(camp, first).json["pickup_id"]
    for verified in [False, "true", 1]:
        assert confirm(camp, first, "release", 1, key="not-verified",
                       pickup_id=pickup, roster_verified=verified).status_code == 400
    assert camp.client.post(attendance.ADMIN_PREFIX + "/pickup-roster", json={
        "camper_id": arrived.json["camper_id"], "session_id": SESSION,
        "pickup_id": pickup, "active": False, "parent_confirmation_reference": "revoke-014",
    }, headers=HEADERS).status_code == 200
    assert confirm(camp, first, "release", 1, key="revoked-pickup",
                   pickup_id=pickup, roster_verified=True).status_code == 404
    assert roster(camp).json["registrations"][0]["status"]["state"] == "present"
    assert rows(camp, "SELECT COUNT(*) FROM discord_attendance_audit WHERE date IS NOT NULL") == [(1,)]


def test_never_linked_family_completes_arrival_and_release_without_parent_links(staff_camp):
    camp = staff_camp
    registration_id = camp.add("REG_NEVER_LINKED")
    pickup = add_pickup(camp, registration_id)
    assert pickup.status_code == 200
    handle = roster(camp).json["registrations"][0]["camper_id"]
    arrival = confirm(camp, registration_id)
    assert arrival.status_code == 200 and arrival.json["camper_id"] == handle
    release = confirm(camp, registration_id, "release", 1, key="never-linked-release",
                      pickup_id=pickup.json["pickup_id"], roster_verified=True)
    assert release.status_code == 200 and release.json["state"] == "released"
    assert release.json["version"] == 2 and release.json["camper_id"] == handle
    assert rows(camp, "SELECT * FROM discord_parent_links") == []
    assert rows(camp, "SELECT actor_type,action FROM discord_attendance_audit WHERE date IS NOT NULL") == [
        ("admin_web", "arrival"), ("admin_web", "release"),
    ]
    assert camp.client.get(attendance.PREFIX + "/campers", query_string={"session_id": SESSION},
                           headers=PARENT_HEADERS).json == {"campers": []}


def test_camp_day_gate_precedes_unrelated_configuration_reads(staff_camp, monkeypatch):
    camp = staff_camp

    def forbidden_read(*args, **kwargs):
        raise AssertionError("Camp-day routes must authenticate and pin their database before any read")

    monkeypatch.setattr(registration_app, "load_configurations", forbidden_read)
    assert camp.client.get(attendance.CAMP_DAY_PREFIX).status_code == 200
    assert roster(camp).status_code == 200
    assert registration_app.app.test_client().get(attendance.CAMP_DAY_PREFIX).status_code == 302
    monkeypatch.delenv("DISCORD_ATTENDANCE_ENABLED")
    assert roster(camp).status_code == 503


def test_web_stale_version_idempotency_and_discord_confirmation_share_engine(staff_camp):
    camp = staff_camp
    registration_id = camp.add()
    initial = confirm(camp, registration_id)
    assert confirm(camp, registration_id).json == initial.json
    assert confirm(camp, registration_id, "release", 1, key="web-confirm-001").status_code == 409
    stale = confirm(camp, registration_id, key="second-arrival")
    assert stale.status_code == 409 and stale.json["error"]["code"] == "stale_version"
    assert confirm(camp, registration_id, version=1, key="invalid-state").json["error"]["code"] == "invalid_transition"
    pickup = add_pickup(camp, registration_id).json["pickup_id"]
    released = camp.client.post(attendance.PREFIX + "/confirmations", json={
        "camper_id": initial.json["camper_id"], "session_id": SESSION, "date": DAY,
        "action": "release", "expected_version": 1, "pickup_id": pickup, "roster_verified": True,
    }, headers={**BOT_STAFF_HEADERS, "Idempotency-Key": "bot-release"})
    assert released.status_code == 200
    assert roster(camp).json["registrations"][0]["status"] == released.json
    assert confirm(camp, registration_id).json == initial.json
    assert rows(camp, "SELECT COUNT(*) FROM discord_attendance") == [(1,)]
    assert rows(camp, "SELECT COUNT(*) FROM discord_attendance_audit WHERE date IS NOT NULL") == [(2,)]


@pytest.mark.parametrize("overrides", [
    {"registration_id": None}, {"registration_id": True}, {"camper_id": "extra"},
    {"active": "true"}, {"parent_confirmation_reference": ""},
    {"display_name": ""}, {"display_name": "Bad\nname"}, {"pickup_id": "extra"},
    {"unexpected": True},
])
def test_registration_pickup_validation_rolls_back_without_creating_handles(staff_camp, overrides):
    camp = staff_camp
    registration_id = camp.add()
    assert add_pickup(camp, registration_id, **overrides).status_code == 400
    assert rows(camp, "SELECT * FROM discord_campers") == []
    assert rows(camp, "SELECT * FROM discord_pickup_roster") == []
    assert rows(camp, "SELECT * FROM discord_attendance_audit") == []


def test_exact_session_history_and_stale_handle_checks_apply_to_all_entry_points(staff_camp):
    camp = staff_camp
    historical = camp.add("HIST_TEST")
    other = camp.add("REG_OTHER", camp_session=OTHER)
    for registration_id in [historical, other, 99999]:
        assert add_pickup(camp, registration_id).status_code == 404
        assert confirm(camp, registration_id).status_code == 404
    current = camp.add("REG_CURRENT")
    assert add_pickup(camp, current).status_code == 200
    with closing(sqlite3.connect(camp.database)) as connection, connection:
        connection.execute("UPDATE discord_campers SET session_label='Old label' WHERE registration_id=?", (current,))
    assert add_pickup(camp, current).status_code == 404
    assert confirm(camp, current).status_code == 404
    assert rows(camp, "SELECT COUNT(*) FROM discord_campers") == [(1,)]
    assert rows(camp, "SELECT COUNT(*) FROM discord_attendance_audit") == [(1,)]


@pytest.mark.parametrize("extra", [
    {"expected_version": True}, {"expected_version": -1}, {"expected_version": "0"},
    {"camper_id": "extra"}, {"unexpected": True}, {"pickup_id": "extra"},
    {"roster_verified": True}, {"date": "2026-11-24"}, {"session_id": "unknown"},
])
def test_web_confirmation_rejects_bad_body_without_partial_state(staff_camp, extra):
    camp = staff_camp
    registration_id = camp.add()
    assert confirm(camp, registration_id, **extra).status_code in (400, 404)
    assert rows(camp, "SELECT * FROM discord_campers") == []
    assert rows(camp, "SELECT * FROM discord_attendance") == []
    assert rows(camp, "SELECT * FROM discord_attendance_idempotency") == []
    assert rows(camp, "SELECT * FROM discord_attendance_audit") == []


def test_central_day_guard_and_read_only_preview(staff_camp, monkeypatch):
    camp = staff_camp
    registration_id = camp.add()
    monkeypatch.setattr(attendance, "utc_now",
                        lambda: datetime(2026, 11, 2, 18, tzinfo=timezone.utc))
    preview = roster(camp).json
    assert preview["today"] == "2026-11-02" and preview["date"] == DAY
    assert preview["write_enabled"] is False
    assert confirm(camp, registration_id).status_code == 400
    monkeypatch.setattr(attendance, "utc_now",
                        lambda: datetime(2026, 11, 24, 5, 59, tzinfo=timezone.utc))
    assert roster(camp).json["today"] == DAY
    assert confirm(camp, registration_id).status_code == 200
    monkeypatch.setattr(attendance, "utc_now",
                        lambda: datetime(2026, 11, 24, 6, 0, tzinfo=timezone.utc))
    assert roster(camp).json["write_enabled"] is False
    assert confirm(camp, registration_id, "release", 1, key="after-midnight").status_code == 400
    assert rows(camp, "SELECT COUNT(*) FROM discord_attendance_audit WHERE date IS NOT NULL") == [(1,)]


def test_staff_session_selection_never_crosses_exact_labels(staff_camp, monkeypatch):
    camp = staff_camp
    camp.add("REG_CURRENT")
    camp.add("REG_OTHER", camp_session=OTHER)
    monkeypatch.setenv("DISCORD_ATTENDANCE_SESSIONS", json.dumps({
        SESSION: {"label": CURRENT, "dates": [DAY]},
        "other-session": {"label": OTHER, "dates": ["2026-11-24"]},
    }))
    selected = roster(camp, "other-session").json
    assert selected["write_enabled"] is False
    assert selected["date"] == "2026-11-24"
    assert [item["submission_id"] for item in selected["registrations"]] == ["REG_OTHER"]
    default = camp.client.get(attendance.CAMP_DAY_PREFIX + "/roster").json
    assert default["session_id"] == SESSION
    assert [item["submission_id"] for item in default["registrations"]] == ["REG_CURRENT"]
    assert roster(camp, "unknown").status_code == 404


@pytest.mark.parametrize("operation", ["pickup", "arrival"])
def test_new_handle_and_mutation_roll_back_if_audit_fails(staff_camp, operation):
    camp = staff_camp
    registration_id = camp.add()
    with closing(sqlite3.connect(camp.database)) as connection, connection:
        connection.execute("""CREATE TRIGGER reject_synthetic_audit
            BEFORE INSERT ON discord_attendance_audit
            BEGIN SELECT RAISE(FAIL, 'synthetic audit failure'); END""")
    response = add_pickup(camp, registration_id) if operation == "pickup" else confirm(camp, registration_id)
    assert response.status_code == 503
    assert response.json == {"error": {"code": "attendance_unavailable"}}
    for table in ["discord_campers", "discord_pickup_roster", "discord_attendance",
                  "discord_attendance_audit", "discord_attendance_idempotency"]:
        assert rows(camp, f"SELECT * FROM {table}") == []


def test_concurrent_discord_and_website_arrival_only_confirm_once(staff_camp):
    camp = staff_camp
    registration_id = camp.add()
    assert add_pickup(camp, registration_id).status_code == 200
    camper = roster(camp).json["registrations"][0]["camper_id"]

    def website():
        client = registration_app.app.test_client()
        with client.session_transaction() as browser:
            browser["admin_logged_in"] = True
            browser["admin_csrf_token"] = TOKEN
        return client.post(attendance.CAMP_DAY_PREFIX + "/confirmations", json={
            "registration_id": registration_id, "session_id": SESSION, "date": DAY,
            "action": "arrival", "expected_version": 0,
        }, headers={**HEADERS, "Idempotency-Key": "concurrent-web"}).status_code

    def discord():
        return registration_app.app.test_client().post(attendance.PREFIX + "/confirmations", json={
            "camper_id": camper, "session_id": SESSION, "date": DAY,
            "action": "arrival", "expected_version": 0,
        }, headers={**BOT_STAFF_HEADERS, "Idempotency-Key": "concurrent-discord"}).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda operation: operation(), [website, discord]))
    assert sorted(responses) == [200, 409]
    assert rows(camp, "SELECT state,version FROM discord_attendance") == [("present", 1)]
    assert rows(camp, "SELECT COUNT(*) FROM discord_attendance_audit WHERE date IS NOT NULL") == [(1,)]


def test_new_admin_endpoints_enforce_csrf_login_pin_and_enablement(staff_camp, monkeypatch):
    camp = staff_camp
    registration_id = camp.add()
    for path in [attendance.CAMP_DAY_PREFIX + "/confirmations", attendance.ADMIN_PREFIX + "/pickup-roster"]:
        assert camp.client.post(path, json={}).status_code == 400
    assert camp.client.post(attendance.CAMP_DAY_PREFIX + "/confirmations", json={
        "registration_id": registration_id, "session_id": SESSION, "date": DAY,
        "action": "arrival", "expected_version": 0,
    }, headers=HEADERS).status_code == 400
    assert rows(camp, "SELECT * FROM discord_campers") == []
    monkeypatch.setenv("DISCORD_ATTENDANCE_DATABASE_PATH", str(camp.root / "wrong.db"))
    assert roster(camp).status_code == 503
    assert confirm(camp, registration_id).status_code == 503
    assert not (camp.root / "wrong.db").exists()
    monkeypatch.setenv("DISCORD_ATTENDANCE_DATABASE_PATH", str(camp.database))
    monkeypatch.delenv("DISCORD_ATTENDANCE_ENABLED")
    assert roster(camp).json["error"]["code"] == "attendance_disabled"
    page = camp.client.get(attendance.CAMP_DAY_PREFIX)
    assert page.status_code == 503 and page.headers["Cache-Control"] == "no-store"
    assert b"Camp-day check-in" in page.data
    with camp.client.session_transaction() as browser:
        browser.clear()
    assert confirm(camp, registration_id).status_code == 401
