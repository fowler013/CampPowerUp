"""Parent-facing contact details share one configurable address."""

import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import Mock

import pytest

from registration_form import app as registration_app
from registration_form.camp_config import CAMP_CONFIG


@pytest.mark.parametrize("configured_email", [None, "camp-contact@example.com"])
def test_contact_email_environment_default_and_override(tmp_path, configured_email):
    env = os.environ.copy()
    for key in ("CONTACT_EMAIL", "RAILWAY_ENVIRONMENT", "SENDGRID_API_KEY"):
        env.pop(key, None)
    if configured_email is not None:
        env["CONTACT_EMAIL"] = configured_email
    env["PYTHONIOENCODING"] = "utf-8"
    root = str(Path(__file__).resolve().parents[2])
    result = subprocess.run(
        [
            sys.executable, "-c",
            f"import sys; sys.path.insert(0, {root!r}); "
            "from registration_form.app import app; "
            "print('CONTACT=' + app.config['CONTACT_EMAIL'])",
        ],
        cwd=tmp_path, env=env, capture_output=True, text=True,
        encoding="utf-8", timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert f"CONTACT={configured_email or 'camppowerup2025@gmail.com'}" in result.stdout


@pytest.mark.parametrize("contact_email", [
    "camppowerup2025@gmail.com",
    "camp-contact@example.com",
])
def test_parent_templates_use_configured_contact(monkeypatch, contact_email):
    monkeypatch.setitem(registration_app.app.config, "CONTACT_EMAIL", contact_email)
    registration = {
        "submission_id": "TEST-CONTACT",
        "child_first_name": "Test",
        "child_last_name": "Camper",
        "is_returning_camper": False,
        "bringing_own_switch": False,
    }
    rendered = {}
    with registration_app.app.test_request_context():
        for template in ("confirmation.html", "faq.html", "registration_form.html"):
            rendered[template] = registration_app.render_template(
                template, registration=registration, config=CAMP_CONFIG,
                pricing=CAMP_CONFIG["pricing"],
            )
    for html in rendered.values():
        assert contact_email in html
        for obsolete in (
            "camppowerup2026@gmail.com", "info@camppowerup.com", "fowler013@gmail.com",
        ):
            assert obsolete not in html
    assert f'href="mailto:{contact_email}"' in rendered["faq.html"]
    assert f"const contactEmail = {json.dumps(contact_email)};" in rendered["registration_form.html"]
    assert "before submitting again to avoid a duplicate registration." in rendered["registration_form.html"]
    assert "Facebook group" in rendered["faq.html"]
    assert "Camp Power-Up Discord community (invite provided by camp leadership)" in rendered["faq.html"]


def test_registration_contact_is_serialized_safely_for_javascript(monkeypatch):
    contact_email = "camp'\"<&@example.com"
    monkeypatch.setitem(registration_app.app.config, "CONTACT_EMAIL", contact_email)
    with registration_app.app.test_request_context():
        html = registration_app.render_template(
            "registration_form.html", config=CAMP_CONFIG, pricing=CAMP_CONFIG["pricing"],
        )
    line = next(line for line in html.splitlines() if "const contactEmail =" in line)
    value = line.split("=", 1)[1].strip().removesuffix(";")
    assert json.loads(value) == contact_email
    assert "<" not in value
    assert "'" not in value


@pytest.mark.parametrize("contact_email", [
    "camppowerup2025@gmail.com",
    "camp-contact@example.com",
])
def test_parent_email_uses_configured_contact(monkeypatch, contact_email):
    monkeypatch.setitem(registration_app.app.config, "CONTACT_EMAIL", contact_email)
    send = Mock(return_value=True)
    monkeypatch.setattr(registration_app, "send_email_notification", send)
    assert registration_app.send_parent_confirmation_email({
        "parent_email": "parent@example.com",
        "child_first_name": "Test",
        "child_last_name": "Camper",
    })
    recipient, _, html, text = send.call_args.args
    assert recipient == "parent@example.com"
    assert f'href="mailto:{contact_email}">{contact_email}</a>' in html
    assert f"Questions? Email: {contact_email}" in text
    assert "camppowerup2026@gmail.com" not in html + text
