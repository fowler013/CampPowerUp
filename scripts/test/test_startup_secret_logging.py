"""Startup and diagnostics output must not reveal secret values.

The WSGI tests run a copy of ``wsgi_railway.py`` in a subprocess against a
synthetic ``registration_form/app.py``, so the real registration app and its
database are never imported by those tests.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import textwrap

import pytest

from registration_form import app as registration_app

ROOT = Path(__file__).resolve().parents[2]
SYNTHETIC_SECRET = "synthetic-startup-secret-value-0123456789abcdef"
SYNTHETIC_PASSWORD = "synthetic-admin-password-value"
SYNTHETIC_DATABASE_URL = "postgresql://synthetic-user:synthetic-db-password@db.example.test/camp"
SECRETS = (SYNTHETIC_SECRET, SYNTHETIC_PASSWORD, "synthetic-db-password")

SUCCESSFUL_APP = textwrap.dedent(
    """
    import os
    from flask import Flask

    app = Flask("synthetic_registration")
    app.secret_key = os.environ.get("SECRET_KEY", "dev-key-change-in-production")
    app.config["ADMIN_PASSWORD"] = os.environ["ADMIN_PASSWORD"]
    app.config["DATABASE_URL"] = os.environ["DATABASE_URL"]

    @app.route("/health")
    def health():
        return "ok"
    """
)

FAILING_APP = textwrap.dedent(
    """
    import os

    raise RuntimeError("cannot connect using " + os.environ["DATABASE_URL"] + " " + os.environ["SECRET_KEY"])
    """
)

DRIVER = textwrap.dedent(
    """
    import json
    import wsgi_railway

    client = wsgi_railway.application.test_client()
    responses = {}
    for path in ("/", "/health"):
        response = client.get(path)
        responses[path] = [response.status_code, response.get_data(as_text=True)]
    print("RESPONSES=" + json.dumps(responses))
    """
)


def run_entry_point(tmp_path, app_source, secret_key=SYNTHETIC_SECRET):
    shutil.copy(ROOT / "wsgi_railway.py", tmp_path / "wsgi_railway.py")
    package = tmp_path / "registration_form"
    package.mkdir()
    (package / "app.py").write_text(app_source, encoding="utf-8")
    env = {
        key: value for key, value in os.environ.items()
        if key not in {"SECRET_KEY", "ADMIN_PASSWORD", "DATABASE_URL", "PYTHONPATH"}
    }
    env.update(
        ADMIN_PASSWORD=SYNTHETIC_PASSWORD,
        DATABASE_URL=SYNTHETIC_DATABASE_URL,
        PYTHONIOENCODING="utf-8",
    )
    if secret_key is not None:
        env["SECRET_KEY"] = secret_key
    result = subprocess.run(
        [sys.executable, "-c", DRIVER], cwd=tmp_path, env=env,
        capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert result.returncode == 0, result.stderr
    marker = [line for line in result.stdout.splitlines() if line.startswith("RESPONSES=")]
    return result.stdout + result.stderr, json.loads(marker[-1].removeprefix("RESPONSES="))


def assert_no_secrets(text):
    for secret in SECRETS:
        assert secret not in text


def test_successful_startup_reports_key_status_without_values(tmp_path):
    output, responses = run_entry_point(tmp_path, SUCCESSFUL_APP)

    assert_no_secrets(output)
    assert "SECRET_KEY status: set (32+ characters)" in output
    assert "Available routes:" in output
    assert "WSGI application ready" in output
    assert responses["/health"] == [200, "ok"]


@pytest.mark.parametrize(
    ("secret_key", "expected"),
    [
        (None, "not set - registration app is using its insecure development fallback key"),
        ("", "set but empty"),
        ("short-synthetic", "set, shorter than the recommended 32 characters"),
    ],
)
def test_startup_reports_weak_key_configuration(tmp_path, secret_key, expected):
    output, _ = run_entry_point(tmp_path, SUCCESSFUL_APP, secret_key=secret_key)

    assert_no_secrets(output)
    assert "short-synthetic" not in output
    assert "dev-key-change-in-production" not in output
    assert f"SECRET_KEY status: {expected}" in output


def test_import_failure_hides_exception_message_from_logs_and_clients(tmp_path):
    output, responses = run_entry_point(tmp_path, FAILING_APP)

    assert_no_secrets(output)
    assert "Error importing Flask app: RuntimeError" in output
    assert "minimal error app" in output
    for status, body in responses.values():
        assert status == 503
        assert_no_secrets(body)
        assert "RuntimeError" not in body


@pytest.fixture
def admin_client(tmp_path, monkeypatch):
    database = tmp_path / "registration_submissions.db"
    monkeypatch.setattr(registration_app, "get_database_path", lambda: str(database))
    monkeypatch.setitem(registration_app.app.config, "TESTING", True)
    monkeypatch.setitem(registration_app.app.config, "SECRET_KEY", "synthetic-test-session-key")
    monkeypatch.setenv("SECRET_KEY", SYNTHETIC_SECRET)
    monkeypatch.setenv("ADMIN_PASSWORD", SYNTHETIC_PASSWORD)
    monkeypatch.setenv("DATABASE_URL", SYNTHETIC_DATABASE_URL)
    monkeypatch.setenv("RAILWAY_VOLUME_MOUNT_PATH", "/synthetic-volume")
    assert registration_app.init_db_with_logging()
    real_exists = os.path.exists
    temporary_root = str(tmp_path)

    def isolated_exists(path):
        # Keep diagnostics from probing or writing to host filesystem locations.
        path = os.fspath(path)
        if path.startswith("/") and not path.startswith(temporary_root):
            return False
        return real_exists(path)

    monkeypatch.setattr(os.path, "exists", isolated_exists)
    client = registration_app.app.test_client()
    with client.session_transaction() as session:
        session["admin_logged_in"] = True
    return client


def test_railway_status_omits_secret_environment_values(admin_client):
    response = admin_client.get("/railway-status")

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert_no_secrets(body)
    volume_vars = response.get_json()["volume_related_env_vars"]
    assert volume_vars["RAILWAY_VOLUME_MOUNT_PATH"] == "/synthetic-volume"
    assert all(name.startswith("RAILWAY_VOLUME_") for name in volume_vars)


def test_find_volumes_lists_environment_names_only(admin_client, monkeypatch):
    def unavailable(*args, **kwargs):
        raise OSError("command unavailable in tests")

    monkeypatch.setattr(subprocess, "check_output", unavailable)
    response = admin_client.get("/find-volumes")

    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert_no_secrets(body)
    payload = response.get_json()
    assert "all_env_vars" not in payload
    assert {"SECRET_KEY", "ADMIN_PASSWORD", "DATABASE_URL"} <= set(payload["env_var_names"])
