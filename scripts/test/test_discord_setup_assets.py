"""Private access-setup page assets and optional-Discord copy."""

import re

from test_admin_workflows import camp


def test_setup_page_loads_base_styles_and_explains_optional_discord(camp):
    """The standalone page must load actual base styling, not just overrides."""
    page = camp.client.get("/admin/discord-attendance")
    assert page.status_code == 200
    html = page.get_data(as_text=True)
    assert "Discord is optional." in html
    assert "Parents do not need a Discord account" in html
    assert "Typing a reference does not verify identity" in html
    assert "No Discord link (optional)" in html
    assert 'id="attendanceSearch"' in html
    assert 'data-state-key="editor"' in html
    assert 'data-state-key="add-link"' in html
    assert "does not record physical attendance" in html
    for path in re.findall(r'<link rel="stylesheet" href="([^"]+)"', html):
        response = camp.client.get(path)
        assert response.status_code == 200
        assert response.mimetype == "text/css"
    css = camp.client.get("/static/css/admin_discord_attendance.css").get_data(as_text=True)
    assert 'font-family: "Segoe UI"' in css
    assert ".nav-bar {" in css
    assert ".btn {" in css
    assert "min-height: 44px" in css
