"""Public health probes must stay independent of private data and admin access."""

from unittest.mock import Mock

import pytest

from registration_form import app as registration_app


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setitem(registration_app.app.config, "TESTING", True)
    return registration_app.app.test_client()


def test_healthz_is_public_and_returns_only_status(client, monkeypatch):
    for name in ("SECRET_KEY", "ADMIN_PASSWORD", "DATABASE_URL", "RAILWAY_GIT_COMMIT_SHA"):
        monkeypatch.setenv(name, "synthetic-private-value")
    monkeypatch.setitem(registration_app.app.config, "SECRET_KEY", "synthetic-session-key")
    monkeypatch.setattr(registration_app, "ADMIN_PASSWORD", None)
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert response.get_json() == {"status": "ok"}
    assert response.data == b'{"status":"ok"}\n'
    assert "Set-Cookie" not in response.headers
    assert "Location" not in response.headers


def test_healthz_does_not_read_configuration_or_database(client, monkeypatch):
    unavailable = Mock(side_effect=AssertionError("Health probes must not read storage"))
    monkeypatch.setattr(registration_app, "load_configurations", unavailable)
    monkeypatch.setattr(registration_app, "get_database_path", unavailable)
    monkeypatch.setattr(registration_app.sqlite3, "connect", unavailable)

    assert client.get("/healthz").get_json() == {"status": "ok"}
    unavailable.assert_not_called()


@pytest.mark.parametrize("path", ["/admin", "/admin/export-json", "/debug-all-registrations"])
def test_healthz_does_not_bypass_other_routes_auth(client, monkeypatch, path):
    monkeypatch.setattr(registration_app, "load_configurations", Mock(return_value=({}, {})))
    assert client.get("/healthz").status_code == 200

    response = client.get(path, headers={"Accept": "application/json"})

    assert response.status_code == 401
    assert response.get_json()["success"] is False


def test_healthz_exemption_does_not_skip_other_routes_configuration(client, monkeypatch):
    configurations = Mock(return_value=({}, {}))
    monkeypatch.setattr(registration_app, "load_configurations", configurations)
    client.get("/admin", headers={"Accept": "application/json"})
    configurations.assert_called_once()


def test_healthz_rejects_writes(client, monkeypatch):
    monkeypatch.setattr(registration_app, "load_configurations", Mock(return_value=({}, {})))
    assert client.post("/healthz", json={}).status_code == 405
