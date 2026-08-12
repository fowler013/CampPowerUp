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
