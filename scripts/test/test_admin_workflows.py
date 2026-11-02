import csv
from contextlib import closing
from datetime import datetime, timezone
from html import unescape
from io import BytesIO, StringIO
import json
import re
import sqlite3
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.parse import parse_qs, urlencode, urlparse

import pytest

from registration_form import app as registration_app
from registration_form import discord_attendance
from registration_form.admin_support import (
    configuration_revision, load_configurations, normalize_registration, registration_summary,
)
from registration_form.camp_config import CAMP_CONFIG, DEFAULT_SESSION_ID, get_session_label


CURRENT = get_session_label(CAMP_CONFIG)
OTHER = "Camp Power-Up Thanksgiving 2026 - November 23-25, 2026"
TOKEN = "synthetic-admin-csrf"
HEADERS = {"Accept": "application/json", "X-CSRF-Token": TOKEN}


@pytest.fixture
def camp(tmp_path, monkeypatch):
    package = tmp_path / "registration_form"
    package.mkdir()
    database = tmp_path / "registration_submissions.db"
    monkeypatch.setattr(registration_app, "__file__", str(package / "app.py"))
    monkeypatch.setattr(registration_app, "get_database_path", lambda: str(database))
    monkeypatch.setattr(registration_app, "ADMIN_USERNAME", "test-admin")
    monkeypatch.setattr(registration_app, "ADMIN_PASSWORD", "synthetic-test-password")
    monkeypatch.setitem(registration_app.app.config, "TESTING", True)
    monkeypatch.setitem(registration_app.app.config, "SECRET_KEY", "synthetic-test-session-key")
    email = Mock(return_value=True)
    monkeypatch.setattr(registration_app, "send_email_notification", email)
    monkeypatch.setattr(registration_app, "send_parent_confirmation_email", Mock(return_value=True))
    monkeypatch.setattr(registration_app, "send_admin_notification_email", Mock(return_value=True))
    assert registration_app.init_db_with_logging()
    client = registration_app.app.test_client()
    with client.session_transaction() as session:
        session["admin_logged_in"] = True
        session["admin_csrf_token"] = TOKEN

    def add(submission_id="REG_TEST", **overrides):
        values = {
            "submission_id": submission_id,
            "child_first_name": "Synthetic",
            "child_last_name": "Camper",
            "child_age": 10,
            "child_grade": "5",
            "parent_email": "parent@example.test",
            "timestamp": "2026-10-30 12:00:00",
            "camp_session": CURRENT,
            "payment_status": "pending",
            **overrides,
        }
        with closing(sqlite3.connect(database)) as connection, connection:
            cursor = connection.execute(
                f"INSERT INTO registrations ({', '.join(values)}) VALUES ({', '.join('?' for _ in values)})",
                tuple(values.values()),
            )
            return cursor.lastrowid

    def rows():
        with closing(sqlite3.connect(database)) as connection:
            connection.row_factory = sqlite3.Row
            return [dict(row) for row in connection.execute("SELECT * FROM registrations ORDER BY id")]

    return SimpleNamespace(client=client, add=add, rows=rows, database=database, root=tmp_path, email=email)


def scoped(path="/admin", label=CURRENT):
    return path + "?" + urlencode({"session": label})


def assert_scoped_link(html, path, label=CURRENT):
    links = [urlparse(unescape(href)) for href in re.findall(r'href="([^"]+)"', html)]
    matching = [link for link in links if link.path == path]
    assert matching, f"No link to {path}"
    assert all(parse_qs(link.query) == {"session": [label]} for link in matching)


def enable_discord_attendance(camp, monkeypatch):
    monkeypatch.setenv("DISCORD_ATTENDANCE_ENABLED", "true")
    monkeypatch.setenv("DISCORD_ATTENDANCE_PARENT_TOKEN", "synthetic-parent-token-000000000000")
    monkeypatch.setenv("DISCORD_ATTENDANCE_STAFF_TOKEN", "synthetic-staff-token-0000000000000")
    monkeypatch.setenv("DISCORD_ATTENDANCE_GUILD_ID", "100")
    monkeypatch.setenv("DISCORD_ATTENDANCE_STAFF_IDS", '["900"]')
    monkeypatch.setenv("DISCORD_ATTENDANCE_SESSIONS", json.dumps({
        "thanksgiving-2026": {"label": CURRENT, "dates": ["2026-11-23"]},
    }))
    monkeypatch.setenv("DISCORD_ATTENDANCE_DATABASE_PATH", str(camp.database))
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    monkeypatch.setattr(registration_app.app, "secret_key", "synthetic-session-signing-key-with-32-bytes")
    with camp.client.session_transaction() as browser:
        browser["admin_logged_in"] = True
        browser["admin_csrf_token"] = TOKEN


def test_session_timestamp_index_supports_dashboard_query(camp):
    with closing(sqlite3.connect(camp.database)) as connection:
        plan = connection.execute("""
            EXPLAIN QUERY PLAN
            SELECT * FROM registrations
            WHERE submission_id NOT GLOB 'HIST_*' AND camp_session = ?
            ORDER BY timestamp DESC
        """, (CURRENT,)).fetchall()

    assert any("idx_registrations_camp_session_timestamp" in row[3] for row in plan)


def update_values(**overrides):
    return {
        "config_revision": configuration_revision(CAMP_CONFIG),
        "camp_name": CAMP_CONFIG["camp_name"],
        "camp_subtitle": CAMP_CONFIG["camp_subtitle"],
        "camp_dates": CAMP_CONFIG["camp_dates"],
        "camp_days": CAMP_CONFIG["camp_days"],
        "daily_hours": CAMP_CONFIG["daily_hours"],
        "final_payment_due": CAMP_CONFIG["final_payment_due"],
        "returning_deposit": 50,
        "returning_final": 30,
        "new_deposit": 50,
        "new_final": 50,
        **overrides,
    }


def submission(**overrides):
    return {
        "child_first_name": "Synthetic",
        "child_last_name": "Signup",
        "child_age": 10,
        "parent_email": "parent@example.test",
        "camp_session_id": DEFAULT_SESSION_ID,
        "is_returning_camper": "false",
        **overrides,
    }


@pytest.mark.parametrize("path", [
    "/admin", "/admin/config", "/admin/historical", "/admin/metrics",
    "/admin/analytics", "/admin/verify-returning-campers", "/admin/attendance",
])
def test_linked_admin_pages_render_with_empty_database(camp, path):
    response = camp.client.get(scoped(path))
    assert response.status_code == 200
    assert b"Traceback" not in response.data


def test_discord_attendance_admin_page_requires_admin_and_is_private(camp, monkeypatch):
    enable_discord_attendance(camp, monkeypatch)
    camp.add("REG_ATTENDANCE_PAGE", parent_email="private@example.test", parent_phone="555-0100")
    page = camp.client.get("/admin/discord-attendance")
    html = page.get_data(as_text=True)
    assert page.status_code == 200
    assert page.headers["Cache-Control"] == "no-store"
    assert "Discord attendance" in html
    assert "private@example.test" not in html
    assert "555-0100" not in html

    anonymous = registration_app.app.test_client().get("/admin/discord-attendance")
    assert anonymous.status_code == 302
    assert "/admin/login" in anonymous.headers["Location"]


def test_discord_attendance_disabled_page_reports_safe_state(camp, monkeypatch):
    enable_discord_attendance(camp, monkeypatch)
    monkeypatch.delenv("DISCORD_ATTENDANCE_ENABLED")
    page = camp.client.get("/admin/discord-attendance")
    assert page.status_code == 200
    assert "Loading Discord attendance records" in page.get_data(as_text=True)
    roster = camp.client.get("/admin/discord-attendance/roster")
    assert roster.status_code == 503
    assert roster.json == {"error": {"code": "attendance_disabled"}}
    script = camp.client.get("/static/js/admin_discord_attendance.js")
    assert b"Discord attendance is off." in script.data
    assert b"Discord attendance is unavailable or misconfigured." in script.data


def test_discord_attendance_roster_lists_only_matching_eligible_fields(camp, monkeypatch):
    enable_discord_attendance(camp, monkeypatch)
    current_id = camp.add("REG_ATTENDANCE_CURRENT", child_first_name="Avery",
                          child_last_name="Quinn", parent_email="private@example.test",
                          parent_phone="555-0100")
    camp.add("HIST_ATTENDANCE_OLD", child_first_name="Historical",
             child_last_name="Camper", camp_session=CURRENT)
    camp.add("REG_ATTENDANCE_OTHER", child_first_name="Other",
             child_last_name="Session", camp_session=OTHER)
    linked = camp.client.post("/admin/discord-attendance/links", json={
        "registration_id": current_id, "session_id": "thanksgiving-2026",
        "discord_user_id": "10101010101010101", "active": True,
        "verification_reference": "verified-parent-01",
    }, headers=HEADERS)
    assert linked.status_code == 200

    response = camp.client.get("/admin/discord-attendance/roster")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    sessions = response.json["sessions"]
    assert [item["session_id"] for item in sessions] == ["thanksgiving-2026"]
    registrations = sessions[0]["registrations"]
    assert [item["submission_id"] for item in registrations] == ["REG_ATTENDANCE_CURRENT"]
    camper = registrations[0]
    assert camper["child_first_name"] == "Avery"
    assert camper["child_last_initial"] == "Q"
    assert camper["links"] == [{"discord_user_id": "10101010101010101", "active": 1}]
    assert "parent_email" not in response.get_data(as_text=True)
    assert "parent_phone" not in response.get_data(as_text=True)
    assert "private@example.test" not in response.get_data(as_text=True)
    assert "555-0100" not in response.get_data(as_text=True)


def test_discord_attendance_unlinked_registration_cannot_add_pickup(camp, monkeypatch):
    enable_discord_attendance(camp, monkeypatch)
    registration_id = camp.add("REG_ATTENDANCE_UNLINKED")
    response = camp.client.get("/admin/discord-attendance/roster")
    assert response.status_code == 200
    camper = response.json["sessions"][0]["registrations"][0]
    assert camper["registration_id"] == registration_id
    assert camper["camper_id"] is None
    assert camper["links"] == []
    rejected = camp.client.post("/admin/discord-attendance/pickup-roster", json={
        "camper_id": camper["camper_id"], "session_id": "thanksgiving-2026",
        "parent_confirmation_reference": "parent-confirmed-unlinked",
        "active": True, "display_name": "Aunt Sam",
    }, headers=HEADERS)
    assert rejected.status_code == 400
    assert rejected.json == {"error": {"code": "invalid_request"}}


def test_discord_attendance_link_and_pickup_mutations_use_audited_endpoints(camp, monkeypatch):
    enable_discord_attendance(camp, monkeypatch)
    registration_id = camp.add("REG_ATTENDANCE_ROUNDTRIP")
    link_url = "/admin/discord-attendance/links"
    link_body = {
        "registration_id": registration_id, "session_id": "thanksgiving-2026",
        "discord_user_id": "10101010101010101", "active": True,
        "verification_reference": "verified-parent-02",
    }
    assert camp.client.post(link_url, json=link_body, headers=HEADERS).status_code == 200
    camper = camp.client.get("/admin/discord-attendance/roster").json["sessions"][0]["registrations"][0]
    assert camper["links"] == [{"discord_user_id": "10101010101010101", "active": 1}]

    link_body["active"] = False
    assert camp.client.post(link_url, json=link_body, headers=HEADERS).status_code == 200
    roster_url = "/admin/discord-attendance/pickup-roster"
    pickup_body = {
        "camper_id": camper["camper_id"], "session_id": "thanksgiving-2026",
        "parent_confirmation_reference": "parent-confirmed-02",
        "active": True, "display_name": "Aunt Sam",
    }
    added = camp.client.post(roster_url, json=pickup_body, headers=HEADERS)
    assert added.status_code == 200
    pickup_id = added.json["pickup_id"]
    current = camp.client.get("/admin/discord-attendance/roster").json["sessions"][0]["registrations"][0]
    assert current["pickups"] == [{"pickup_id": pickup_id, "display_name": "Aunt Sam"}]

    revoked = camp.client.post(roster_url, json={
        "camper_id": camper["camper_id"], "session_id": "thanksgiving-2026",
        "parent_confirmation_reference": "parent-revoked-02",
        "active": False, "pickup_id": pickup_id,
    }, headers=HEADERS)
    assert revoked.status_code == 200
    assert camp.client.get("/admin/discord-attendance/roster").json["sessions"][0]["registrations"][0]["pickups"] == []
    with closing(sqlite3.connect(camp.database)) as connection:
        actions = [row[0] for row in connection.execute(
            "SELECT action FROM discord_attendance_audit ORDER BY rowid"
        )]
    assert actions == ["link_approved", "link_revoked", "pickup_added", "pickup_revoked"]


def test_discord_attendance_admin_rejects_bad_ids_missing_references_and_csrf(camp, monkeypatch):
    enable_discord_attendance(camp, monkeypatch)
    registration_id = camp.add("REG_ATTENDANCE_INVALID")
    url = "/admin/discord-attendance/links"
    body = {
        "registration_id": registration_id, "session_id": "thanksgiving-2026",
        "discord_user_id": "123456", "active": True,
        "verification_reference": "verified-parent-03",
    }
    assert camp.client.post(url, json=body, headers=HEADERS).status_code == 400
    body["discord_user_id"] = "10101010101010101"
    del body["verification_reference"]
    assert camp.client.post(url, json=body, headers=HEADERS).status_code == 400
    body["verification_reference"] = "verified-parent-03"
    assert camp.client.post(url, json=body).status_code == 400

    camper = camp.client.post(url, json=body, headers=HEADERS).json["camper_id"]
    assert camp.client.post("/admin/discord-attendance/pickup-roster", json={
        "camper_id": camper, "session_id": "thanksgiving-2026",
        "active": True, "display_name": "Aunt Sam",
    }, headers=HEADERS).status_code == 400


def test_exact_session_counts_and_exports(camp):
    for number in range(13):
        camp.add(f"REG_CURRENT_{number}", is_returning_camper="false", has_allergies="No")
    for number in range(3):
        camp.add(f"REG_OTHER_{number}", camp_session=OTHER)
    camp.add("HIST_OLD", camp_session=CURRENT)
    html = camp.client.get(scoped()).get_data(as_text=True)
    assert 'id="totalRegistrations">13<' in html
    assert html.count('class="registration-card"') == 13
    assert "REG_OTHER_0" not in html
    assert 'id="returningCampers">0<' in html
    assert 'id="newCampers">13<' in html
    for path in ("/admin/export-json",):
        response = camp.client.get(scoped(path)).get_json()
        assert response["count"] == 13
        assert {row["camp_session"] for row in response["registrations"]} == {CURRENT}
    csv_rows = list(csv.DictReader(StringIO(camp.client.get(scoped("/admin/export")).get_data(as_text=True))))
    assert len(csv_rows) == 13
    assert {row["camp_session"] for row in csv_rows} == {CURRENT}
    assert camp.client.get("/admin/export-json").get_json()["count"] == 16
    assert camp.client.get(scoped("/admin/export-json", OTHER)).get_json()["count"] == 3


@pytest.mark.parametrize("path", ["/admin", "/admin?session="])
def test_dashboard_defaults_to_current_camp_with_scoped_links(camp, path):
    camp.add("REG_CURRENT", payment_status="paid", is_returning_camper="true")
    camp.add("REG_OTHER", camp_session=OTHER)
    camp.add("REG_UNASSIGNED", camp_session=None)
    camp.add("HIST_IMPORTED", camp_session=CURRENT)
    before = camp.rows()

    response = camp.client.get(path)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert f'<option value="{CURRENT}" selected>' in html
    assert 'id="totalRegistrations">1<' in html
    assert 'id="paidRegistrations">1<' in html
    assert 'id="returningCampers">1<' in html
    assert html.count('class="registration-card"') == 1
    assert "REG_CURRENT" in html
    assert all(value not in html for value in ("REG_OTHER", "REG_UNASSIGNED", "HIST_IMPORTED"))
    for endpoint in ("/admin/export", "/admin/metrics", "/admin/config"):
        assert_scoped_link(html, endpoint)
    assert camp.rows() == before


@pytest.mark.parametrize("selection,expected", [
    ("all", {"REG_CURRENT", "REG_OTHER", "REG_UNASSIGNED"}),
    (OTHER, {"REG_OTHER"}),
    (CURRENT, {"REG_CURRENT"}),
])
def test_dashboard_preserves_explicit_selection_and_export_scope(camp, selection, expected):
    camp.add("REG_CURRENT")
    camp.add("REG_OTHER", camp_session=OTHER)
    camp.add("REG_UNASSIGNED", camp_session=None)
    camp.add("HIST_IMPORTED", camp_session=CURRENT)
    before = camp.rows()

    html = camp.client.get(scoped(label=selection)).get_data(as_text=True)
    assert f'<option value="{selection}" selected>' in html
    assert f'id="totalRegistrations">{len(expected)}<' in html
    assert html.count('class="registration-card"') == len(expected)
    assert "HIST_IMPORTED" not in html
    for submission_id in ("REG_CURRENT", "REG_OTHER", "REG_UNASSIGNED"):
        assert (submission_id in html) == (submission_id in expected)
    assert_scoped_link(html, "/admin/export", selection)
    assert_scoped_link(html, "/admin/metrics", selection)
    exported = camp.client.get(scoped("/admin/export-json", selection)).get_json()
    assert {row["submission_id"] for row in exported["registrations"]} == expected
    csv_rows = csv.DictReader(StringIO(
        camp.client.get(scoped("/admin/export", selection)).get_data(as_text=True)
    ))
    assert {row["submission_id"] for row in csv_rows} == expected
    assert camp.rows() == before


def test_dashboard_default_follows_saved_current_config_even_when_empty(camp):
    camp.add("REG_PREVIOUS")
    camp.add("REG_OTHER", camp_session=OTHER)
    before = camp.rows()
    values = update_values(camp_name="Camp Power-Up Winter 2026", camp_dates="December 1-2, 2026")
    assert camp.client.post("/admin/update-config", json=values, headers=HEADERS).status_code == 200
    current = get_session_label(values)

    html = camp.client.get("/admin").get_data(as_text=True)
    assert f'<option value="{current}" selected>' in html
    assert 'id="totalRegistrations">0<' in html
    assert "No registrations were found for this exact session" in html
    assert "REG_PREVIOUS" not in html and "REG_OTHER" not in html
    assert camp.rows() == before
    assert "REG_PREVIOUS" in camp.client.get(scoped(label=CURRENT)).get_data(as_text=True)
    camp.add("REG_NEW_CURRENT", camp_session=current)
    assert "REG_NEW_CURRENT" in camp.client.get("/admin").get_data(as_text=True)


def test_empty_selection_stays_empty_and_export_keeps_scope(camp):
    camp.add()
    missing = "A different camp"
    response = camp.client.get(scoped(label=missing))
    assert b'No registrations were found for this exact session' in response.data
    assert b'id="totalRegistrations">0<' in response.data
    exported = camp.client.get(scoped("/admin/export", missing))
    assert exported.status_code == 302
    assert exported.headers["Location"] == scoped(label=missing)


def test_summary_uses_stored_flags_payments_and_utc_dates():
    rows = [
        normalize_registration({"timestamp": "2026-11-01T00:30:00Z", "child_age": 10, "payment_status": "paid", "bringing_own_switch": "true", "is_returning_camper": "yes", "has_allergies": "No"}),
        normalize_registration({"timestamp": "2026-10-31 12:00:00", "child_age": None, "payment_status": "pending", "has_medical_conditions": "1"}),
        normalize_registration({"timestamp": "not-a-date", "has_allergies": "false", "payment_status": "pending"}),
    ]
    stats = registration_summary(rows, now=datetime(2026, 11, 1, 12, tzinfo=timezone.utc))
    assert stats["paid_count"] == 1
    assert stats["pending_payment"] == 2
    assert stats["bringing_switch"] == stats["returning_campers"] == stats["has_medical_conditions"] == 1
    assert stats["has_allergies"] == 0
    assert stats["todays_count"] == 1
    assert stats["weeks_count"] == 2
    assert stats["invalid_dates"] == 1
    assert stats["last_registration"] == "2026-11-01"


def test_payment_actions_and_missing_ids(camp):
    registration_id = camp.add()
    response = camp.client.post("/admin/mark-paid/REG_TEST", headers=HEADERS)
    assert response.status_code == 200
    assert camp.rows()[0]["payment_status"] == "paid"
    assert b'id="paidRegistrations">1<' in camp.client.get(scoped()).data
    assert camp.client.post("/admin/mark-paid/UNKNOWN", headers=HEADERS).status_code == 404
    assert camp.client.post("/admin/delete/9999", headers=HEADERS).status_code == 404
    deleted = camp.client.post(f"/admin/delete/{registration_id}", headers=HEADERS)
    assert deleted.status_code == 200 and deleted.get_json()["success"]
    assert camp.rows() == []


def test_mutations_require_auth_and_csrf(camp):
    camp.add()
    assert camp.client.post("/admin/mark-paid/REG_TEST").status_code == 400
    assert camp.client.post("/admin/update-config", json=update_values()).status_code == 400
    anonymous = registration_app.app.test_client()
    assert anonymous.get("/admin").status_code == 302
    assert anonymous.post("/admin/mark-paid/REG_TEST", headers=HEADERS).status_code == 401
    assert camp.rows()[0]["payment_status"] == "pending"


def test_non_ascii_csrf_token_is_rejected_without_server_error(camp):
    camp.add()
    response = camp.client.post("/admin/mark-paid/REG_TEST", data={"csrf_token": "\u1234"})
    assert response.status_code == 400
    assert camp.rows()[0]["payment_status"] == "pending"


def test_login_and_logout(camp):
    client = registration_app.app.test_client()
    assert client.post("/admin/login", data={"username": "test-admin", "password": "incorrect"}).status_code == 200
    assert client.get("/admin").status_code == 302
    assert client.post("/admin/login", data={"username": "test-admin", "password": "synthetic-test-password"}).status_code == 302
    assert client.get("/admin").status_code == 200
    client.get("/admin/logout")
    assert client.get("/admin").status_code == 302


def test_payment_reminders_use_provider_result(camp):
    camp.add(child_first_name="<script>synthetic</script>")
    response = camp.client.post("/admin/send-reminder/REG_TEST", headers=HEADERS)
    assert response.status_code == 200
    assert camp.email.call_count == 1
    assert "&lt;script&gt;" in camp.email.call_args.args[2]
    assert "<script>" not in camp.email.call_args.args[2]
    camp.email.return_value = False
    failed = camp.client.post("/admin/send-reminder/REG_TEST", headers=HEADERS)
    assert failed.status_code == 502 and not failed.get_json()["success"]


@pytest.mark.parametrize("values,status", [
    ({"payment_status": "paid"}, 409),
    ({"camp_session": OTHER}, 409),
    ({"parent_email": ""}, 400),
])
def test_reminder_refuses_inappropriate_records(camp, values, status):
    camp.add(**values)
    assert camp.client.post("/admin/send-reminder/REG_TEST", headers=HEADERS).status_code == status
    camp.email.assert_not_called()


def test_settings_persist_without_mutating_code_defaults(camp):
    response = camp.client.post("/admin/update-config", json=update_values(new_final=70), headers=HEADERS)
    assert response.status_code == 200
    active, stored = load_configurations(str(camp.database))
    assert active[DEFAULT_SESSION_ID]["pricing"]["new_camper"]["total"] == 120
    assert stored[CURRENT]["pricing"]["new_camper"]["total"] == 120
    assert CAMP_CONFIG["pricing"]["new_camper"]["total"] == 100
    fresh_client = registration_app.app.test_client()
    assert b"$120 total" in fresh_client.get("/").data
    stale = camp.client.post("/admin/update-config", json=update_values(new_final=80), headers=HEADERS)
    assert stale.status_code == 409


@pytest.mark.parametrize("values", [
    {"camp_name": ""}, {"camp_days": 0}, {"camp_days": 1.5},
    {"new_final": -1}, {"returning_deposit": "not-a-number"}, {"new_final": True},
])
def test_invalid_settings_do_not_change_saved_configuration(camp, values):
    response = camp.client.post("/admin/update-config", json=update_values(**values), headers=HEADERS)
    assert response.status_code == 400
    assert load_configurations(str(camp.database)) == ({}, {})


def test_settings_preserve_existing_session_records(camp):
    camp.add()
    response = camp.client.post("/admin/update-config", json=update_values(camp_dates="December 1-2, 2026", new_final=70), headers=HEADERS)
    assert response.status_code == 200
    assert camp.rows()[0]["camp_session"] == CURRENT
    result = camp.client.post("/submit", json=submission()).get_json()
    assert result["success"]
    assert camp.rows()[1]["camp_session"].endswith("December 1-2, 2026")
    old_confirmation = camp.client.get("/confirmation/REG_TEST").get_data(as_text=True)
    assert "November 23-24, 2026" in old_confirmation
    assert "$50 remaining ($100 total)" in old_confirmation


def test_settings_cannot_merge_existing_labels(camp):
    camp.add(camp_session=OTHER)
    response = camp.client.post("/admin/update-config", json=update_values(camp_dates="November 23-25, 2026"), headers=HEADERS)
    assert response.status_code == 400
    assert camp.rows()[0]["camp_session"] == OTHER


def test_public_submission_persists_actual_form_fields(camp):
    response = camp.client.post("/submit", json=submission(
        has_allergies="false", allergy_details="",
        has_sensory_issues="true", sensory_details="Synthetic accommodation",
        bringing_own_switch="true", additional_notes="Synthetic note",
        favorite_games="Example game", photo_permission=False,
    ))
    assert response.status_code == 200 and response.get_json()["success"]
    row = camp.rows()[0]
    assert row["camp_session"] == CURRENT
    assert row["has_allergies"] == 0
    assert row["has_medical_conditions"] == row["bringing_own_switch"] == 1
    assert row["medical_conditions_description"] == "Synthetic accommodation"
    assert "Synthetic note" in row["additional_comments"]
    assert "Favorite games: Example game" in row["additional_comments"]
    assert "Photo permission: No" in row["additional_comments"]
    assert camp.client.get(f"/confirmation/{row['submission_id']}").status_code == 200
    dashboard = camp.client.get(scoped()).get_data(as_text=True)
    assert "Synthetic accommodation" in dashboard
    assert 'id="totalRegistrations">1<' in dashboard
    assert camp.client.get(scoped("/admin/export-json")).get_json()["count"] == 1


@pytest.mark.parametrize("values", [
    {"child_first_name": ""}, {"child_age": 4}, {"child_age": "10.5"},
    {"parent_email": "invalid"}, {"camp_session_id": "unknown-session"},
])
def test_invalid_submissions_are_not_saved(camp, values):
    assert camp.client.post("/submit", json=submission(**values)).status_code == 400
    assert camp.rows() == []


def test_missing_confirmation_never_claims_success(camp):
    response = camp.client.get("/confirmation/NOT_SAVED")
    assert response.status_code == 404
    assert b"Registration Confirmed" not in response.data


def test_unknown_session_does_not_display_current_fees(camp):
    camp.add(camp_session=OTHER)
    html = camp.client.get("/confirmation/REG_TEST").get_data(as_text=True)
    assert OTHER in html
    assert "Pricing and dates are not configured" in html
    assert "$100" not in html
    assert b"Not configured for this session" in camp.client.get(scoped(label=OTHER)).data


def test_json_round_trip_preserves_session_and_payment(camp):
    camp.add(payment_status="paid", camp_session=OTHER)
    exported = camp.client.get("/admin/export-json").get_json()
    exported["registrations"][0]["submission_id"] = "REG_COPY"
    response = camp.client.post("/admin/import-json", json=exported, headers=HEADERS)
    assert response.status_code == 200 and response.get_json()["imported"] == 1
    assert camp.rows()[1]["camp_session"] == OTHER
    assert camp.rows()[1]["payment_status"] == "paid"
    repeated = camp.client.post("/admin/import-json", json=exported, headers=HEADERS)
    assert repeated.get_json()["skipped"] == 1
    assert len(camp.rows()) == 2


def test_bad_import_rolls_back_all_new_rows(camp):
    response = camp.client.post("/admin/import-json", json={"registrations": [
        {"submission_id": "REG_VALID"},
        {"submission_id": "REG_INVALID", "child_first_name": ["invalid"]},
    ]}, headers=HEADERS)
    assert response.status_code == 400 and not response.get_json()["success"]
    assert camp.rows() == []


def historical_csv():
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["Childs First Name?", "Childs Last Name?", "Email Address", "Timestamp", "Age?"])
    writer.writeheader()
    writer.writerow({"Childs First Name?": "Synthetic", "Childs Last Name?": "Camper", "Email Address": "parent@example.test", "Timestamp": "7/1/2025 10:00:00", "Age?": "10"})
    return output.getvalue()


def test_history_upload_preserves_current_registration_and_is_idempotent(camp):
    camp.add()
    for _ in range(2):
        response = camp.client.post("/admin/upload-historical", data={
            "csrf_token": TOKEN,
            "csv_file": (BytesIO(historical_csv().encode()), "synthetic.csv"),
        }, content_type="multipart/form-data")
        assert response.status_code == 302
    rows = camp.rows()
    assert len(rows) == 2
    assert rows[0]["submission_id"] == "REG_TEST" and rows[0]["camp_session"] == CURRENT
    assert rows[1]["submission_id"].startswith("HIST_")


def test_legacy_repair_does_not_reclassify_current_campers(camp):
    data_dir = camp.root / "data"
    data_dir.mkdir()
    (data_dir / "Camp_Power_Up_past_forms - Sheet1.csv").write_text(historical_csv(), encoding="utf-8")
    camp.add(timestamp="7/1/2025 10:00:00")
    camp.add("REG_OTHER", camp_session=OTHER, timestamp="7/1/2025 10:00:00")
    camp.add("LEGACY_UNASSIGNED", camp_session=None, timestamp="7/1/2025 10:00:00")
    for _ in range(2):
        response = camp.client.post("/admin/fix-historical-records", headers=HEADERS)
        assert response.status_code == 302
    rows = camp.rows()
    assert rows[0]["submission_id"] == "REG_TEST"
    assert rows[1]["submission_id"] == "REG_OTHER"
    assert rows[2]["submission_id"].startswith("HIST_")
    assert [row["camp_session"] for row in rows] == [CURRENT, OTHER, None]


def test_verification_is_scoped_and_handles_incomplete_history(camp):
    camp.add(is_returning_camper="true")
    camp.add("REG_OTHER", camp_session=OTHER, is_returning_camper=1)
    camp.add("HIST_MATCH", camp_session=None)
    camp.add("HIST_NULL", child_first_name=None, parent_email=None, camp_session=None)
    html = camp.client.get(scoped("/admin/verify-returning-campers")).get_data(as_text=True)
    assert "REG_TEST" in html and "REG_OTHER" not in html
    assert "VERIFIED" in html
    assert "is not proof of fraud" in html


def test_metrics_do_not_apply_current_prices_to_other_sessions(camp):
    camp.add()
    camp.add("REG_OTHER", camp_session=OTHER)
    html = camp.client.get("/admin/metrics").get_data(as_text=True)
    assert OTHER in html and "Pricing unavailable" in html
    assert "1 registrations have no saved session pricing" in html
    scoped_html = camp.client.get(scoped("/admin/metrics")).get_data(as_text=True)
    assert OTHER not in scoped_html
    assert "Pricing unavailable" not in scoped_html


def test_edit_keeps_session_context(camp):
    registration_id = camp.add(camp_session=OTHER)
    response = camp.client.post(scoped(f"/admin/edit/{registration_id}", OTHER), data={
        "csrf_token": TOKEN, "child_first_name": "Edited", "child_last_name": "Camper",
        "child_age": "10", "parent_email": "parent@example.test",
    })
    assert response.status_code == 302
    assert urlparse(response.headers["Location"]).path == "/admin"
    assert parse_qs(urlparse(response.headers["Location"]).query) == {"session": [OTHER]}
    assert camp.rows()[0]["camp_session"] == OTHER
    assert camp.rows()[0]["child_first_name"] == "Edited"


@pytest.mark.parametrize("values", [
    {"child_first_name": " "}, {"parent_email": "invalid"}, {"child_age": "ten"},
])
def test_invalid_edit_preserves_saved_registration(camp, values):
    registration_id = camp.add()
    before = camp.rows()
    response = camp.client.post(scoped(f"/admin/edit/{registration_id}"), data={
        **submission(), **values, "csrf_token": TOKEN,
    })
    assert response.status_code == 400
    assert camp.rows() == before


def test_metrics_escape_session_labels_in_scripts(camp):
    label = "</script><script>window.unexpected=true</script>"
    camp.add(camp_session=label)
    html = camp.client.get("/admin/metrics").get_data(as_text=True)
    assert label not in html
    assert "\\u003c/script\\u003e" in html


def test_changed_deposits_are_explicit_on_public_form(camp):
    response = camp.client.post("/admin/update-config", json=update_values(
        new_deposit=60, returning_deposit=40,
    ), headers=HEADERS)
    assert response.status_code == 200
    html = camp.client.get("/").get_data(as_text=True)
    assert "$60 for a new camper or $40 for a returning camper" in html


def test_attendance_starts_empty_and_saves_valid_checkins(camp):
    camp.add()
    assert camp.client.get("/admin/attendance/status/2026-11-23").get_json() == {}
    payload = {"submission_id": "REG_TEST", "date": "2026-11-23", "status": "present"}
    assert camp.client.post("/admin/attendance/check-in", json=payload).status_code == 400
    assert camp.client.post("/admin/attendance/check-in", json=payload, headers=HEADERS).status_code == 200
    assert camp.client.get("/admin/attendance/status/2026-11-23").get_json()["REG_TEST"]["status"] == "present"
    payload["status"] = "late"
    assert camp.client.post("/admin/attendance/check-in", json=payload, headers=HEADERS).status_code == 200
    assert camp.client.get("/admin/attendance/status/2026-11-23").get_json()["REG_TEST"]["status"] == "late"
    assert camp.client.get("/admin/attendance/status/2026-11-24").get_json() == {}


@pytest.mark.parametrize("selection", ["all", OTHER, CURRENT])
def test_manual_attendance_roster_ignores_dashboard_selection(camp, selection):
    camp.add("REG_CURRENT")
    camp.add("REG_OTHER", camp_session=OTHER)
    camp.add("REG_UNASSIGNED", camp_session=None)
    camp.add("HIST_IMPORTED", camp_session=CURRENT)
    before = camp.rows()

    response = camp.client.get(scoped("/admin/attendance", selection))
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert f"{CURRENT} (current camp only)" in html
    assert 'id="total-count">1<' in html
    assert html.count('class="camper-card"') == 1
    assert 'data-id="REG_CURRENT"' in html
    assert all(value not in html for value in ("REG_OTHER", "REG_UNASSIGNED", "HIST_IMPORTED"))
    assert camp.rows() == before


@pytest.mark.parametrize("prefix,label", [
    ("REG_OTHER", OTHER), ("REG_UNASSIGNED", None), ("HIST_IMPORTED", CURRENT),
])
def test_manual_attendance_rejects_out_of_scope_writes_and_filters_status(camp, prefix, label):
    camp.add("REG_CURRENT")
    camp.add(f"{prefix}_EXISTING", camp_session=label)
    camp.add(f"{prefix}_NEW", camp_session=label)
    registrations_before = camp.rows()
    payload = {"submission_id": "REG_CURRENT", "date": "2026-11-23", "status": "present"}
    assert camp.client.post("/admin/attendance/check-in", json=payload, headers=HEADERS).status_code == 200
    with closing(sqlite3.connect(camp.database)) as connection, connection:
        connection.executemany(
            "INSERT INTO attendance (submission_id, date, status) VALUES (?, ?, ?)",
            [(f"{prefix}_EXISTING", "2026-11-23", "absent"),
             ("REG_NO_LONGER_EXISTS", "2026-11-23", "late")],
        )
        attendance_before = connection.execute("SELECT * FROM attendance ORDER BY id").fetchall()

    for suffix in ("EXISTING", "NEW"):
        for selection in ("all", label or "all"):
            rejected = camp.client.post(scoped("/admin/attendance/check-in", selection), json={
                **payload, "submission_id": f"{prefix}_{suffix}", "camp_session": CURRENT,
            }, headers=HEADERS)
            assert rejected.status_code == 404
            assert rejected.get_json()["success"] is False
    for selection in ("all", label or "all"):
        visible = camp.client.get(scoped("/admin/attendance/status/2026-11-23", selection)).get_json()
        assert set(visible) == {"REG_CURRENT"}
        assert visible["REG_CURRENT"]["status"] == "present"
    with closing(sqlite3.connect(camp.database)) as connection:
        assert connection.execute("SELECT * FROM attendance ORDER BY id").fetchall() == attendance_before
    assert camp.rows() == registrations_before


def test_manual_attendance_follows_saved_current_config_without_rewriting_history(camp):
    camp.add("REG_PREVIOUS")
    payload = {"submission_id": "REG_PREVIOUS", "date": "2026-11-23", "status": "present"}
    assert camp.client.post("/admin/attendance/check-in", json=payload, headers=HEADERS).status_code == 200
    values = update_values(camp_name="Camp Power-Up Winter 2026", camp_dates="December 1-2, 2026")
    assert camp.client.post("/admin/update-config", json=values, headers=HEADERS).status_code == 200
    current = get_session_label(values)
    html = camp.client.get("/admin/attendance").get_data(as_text=True)
    assert f"{current} (current camp only)" in html
    assert "No registrations were found for the current camp." in html
    assert 'data-id="REG_PREVIOUS"' not in html
    assert camp.client.get("/admin/attendance/status/2026-11-23").get_json() == {}
    assert camp.client.post("/admin/attendance/check-in", json={
        **payload, "status": "absent",
    }, headers=HEADERS).status_code == 404

    camp.add("REG_CURRENT", camp_session=current)
    assert 'data-id="REG_CURRENT"' in camp.client.get("/admin/attendance").get_data(as_text=True)
    assert camp.client.post("/admin/attendance/check-in", json={
        "submission_id": "REG_CURRENT", "date": "2026-12-01", "status": "present",
    }, headers=HEADERS).status_code == 200
    assert set(camp.client.get("/admin/attendance/status/2026-12-01").get_json()) == {"REG_CURRENT"}
    with closing(sqlite3.connect(camp.database)) as connection:
        assert connection.execute(
            "SELECT status FROM attendance WHERE submission_id = 'REG_PREVIOUS'"
        ).fetchone() == ("present",)
    assert camp.rows()[0]["camp_session"] == CURRENT


def test_dashboard_scope_and_manual_checkin_do_not_enable_discord_attendance(camp, monkeypatch):
    enable_discord_attendance(camp, monkeypatch)
    monkeypatch.setenv("DISCORD_ATTENDANCE_ENABLED", "false")
    camp.add()
    for path in ("/admin", scoped(label="all"), scoped(label=OTHER), "/admin/attendance"):
        assert camp.client.get(path).status_code == 200
        response = camp.client.get("/admin/discord-attendance/roster")
        assert response.status_code == 503
        assert response.get_json() == {"error": {"code": "attendance_disabled"}}
    payload = {"submission_id": "REG_TEST", "date": "2026-11-23", "status": "present"}
    assert camp.client.post("/admin/attendance/check-in", json=payload, headers=HEADERS).status_code == 200
    assert camp.client.get("/admin/discord-attendance/roster").get_json() == {
        "error": {"code": "attendance_disabled"},
    }


@pytest.mark.parametrize("values,status", [
    ({"submission_id": "UNKNOWN"}, 404), ({"date": "not-a-date"}, 400),
    ({"status": "invalid"}, 400),
])
def test_invalid_attendance_is_not_saved(camp, values, status):
    camp.add()
    payload = {"submission_id": "REG_TEST", "date": "2026-11-23", "status": "present", **values}
    assert camp.client.post("/admin/attendance/check-in", json=payload, headers=HEADERS).status_code == status
    assert camp.client.get("/admin/attendance/status/2026-11-23").get_json() == {}


def test_backup_restore_preserves_session_and_payment(camp):
    camp.add(camp_session=OTHER, payment_status="paid")
    exported = camp.client.get("/admin/export-json").get_json()
    (camp.root / "registration_form" / "registrations_backup.json").write_text(json.dumps(exported), encoding="utf-8")
    camp.database.unlink()
    assert registration_app.init_db_with_logging()
    assert len(camp.rows()) == 1
    assert camp.rows()[0]["camp_session"] == OTHER
    assert camp.rows()[0]["payment_status"] == "paid"


def test_historical_feedback_appears_once(camp):
    with camp.client.session_transaction() as session:
        session["_flashes"] = [("warning", "Synthetic import warning")]
    html = camp.client.get("/admin/historical").get_data(as_text=True)
    assert html.count("Synthetic import warning") == 1


def test_paid_confirmation_does_not_request_another_payment(camp):
    camp.add(payment_status="paid")
    html = camp.client.get("/confirmation/REG_TEST").get_data(as_text=True)
    assert "No further payment is requested" in html
    assert "Send Your $" not in html
    assert "Send your $" not in html
