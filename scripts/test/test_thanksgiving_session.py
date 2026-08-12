import sqlite3

from registration_form import app as registration_app
from registration_form.camp_config import (
    CAMP_CONFIG,
    DEFAULT_SESSION_ID,
    SESSIONS,
    validate_config,
)


def test_thanksgiving_session_configuration():
    assert validate_config()
    assert DEFAULT_SESSION_ID == "thanksgiving-2026"
    assert SESSIONS[DEFAULT_SESSION_ID] is CAMP_CONFIG
    assert CAMP_CONFIG["camp_dates"] == "November 23-25, 2026"
    assert CAMP_CONFIG["camp_days"] == 3
    assert CAMP_CONFIG["daily_hours"] == "10:00 AM - 3:00 PM"
    assert CAMP_CONFIG["pricing"]["new_camper"]["total"] == 100
    assert CAMP_CONFIG["pricing"]["returning_camper"]["total"] == 80


def test_registration_page_uses_thanksgiving_session():
    client = registration_app.app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert b"Camp Power-Up Thanksgiving 2026" in response.data
    assert b"November 23-25, 2026" in response.data
    assert b'name="camp_session_id" value="thanksgiving-2026"' in response.data


def test_confirmation_page_uses_current_dates_and_pricing():
    registration = {
        "submission_id": "TEST-THANKSGIVING",
        "child_first_name": "Test",
        "child_last_name": "Camper",
        "child_age": 10,
        "child_grade": "5",
        "parent_email": "parent@example.com",
        "is_returning_camper": False,
        "bringing_own_switch": False,
        "timestamp": "2026-08-11 12:00:00",
    }

    with registration_app.app.test_request_context():
        rendered = registration_app.render_template(
            "confirmation.html",
            registration=registration,
            config=CAMP_CONFIG,
        )

    assert "November 23-25, 2026" in rendered
    assert "November 22, 2026" in rendered
    assert "$50 remaining ($100 total)" in rendered
    assert "June" not in rendered


def test_expired_july_registration_redirects_to_current_session():
    client = registration_app.app.test_client()

    response = client.get("/session/july-2026")

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


def test_confirmation_uses_stored_session_configuration(monkeypatch):
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.execute(
        """
        CREATE TABLE registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_id TEXT,
            timestamp TEXT,
            child_first_name TEXT,
            child_last_name TEXT,
            child_age TEXT,
            child_grade TEXT,
            parent_email TEXT,
            is_returning_camper INTEGER,
            bringing_own_switch INTEGER,
            camp_session TEXT
        )
        """
    )
    db.execute(
        """
        INSERT INTO registrations (
            submission_id, timestamp, child_first_name, child_last_name, child_age, child_grade,
            parent_email, is_returning_camper, bringing_own_switch, camp_session
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "CONFIRM-OLD-SESSION",
            "2026-05-01 12:00:00",
            "Jamie",
            "Legacy",
            "10",
            "5",
            "legacy@example.com",
            1,
            0,
            "Camp Power-Up Summer 2026 - June 15-19, 2026",
        ),
    )
    db.commit()

    monkeypatch.setattr(registration_app, "get_database_path", lambda: ":memory:")
    monkeypatch.setattr(registration_app.sqlite3, "connect", lambda *args, **kwargs: db)
    monkeypatch.setitem(
        registration_app.SESSIONS,
        "legacy-june-2026",
        {
            "camp_name": "Camp Power-Up Summer 2026",
            "camp_dates": "June 15-19, 2026",
            "camp_days": 5,
            "daily_hours": "10:00 AM - 3:00 PM",
            "final_payment_due": "June 1st",
            "pricing": {
                "new_camper": {"deposit": 50, "final_payment": 150, "total": 200},
                "returning_camper": {"deposit": 50, "final_payment": 130, "total": 180},
            },
        },
    )

    client = registration_app.app.test_client()
    response = client.get("/confirmation/CONFIRM-OLD-SESSION")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "June 15-19, 2026" in html
    assert "June 1st" in html
    assert "$130 remaining ($180 total)" in html
