"""Local synthetic-only browser coverage for parent access and pickup setup."""

import sqlite3
import json
from contextlib import closing

from test_admin_browser import browser_page, login, snapshot, assert_no_overflow, playwright
from test_admin_workflows import camp, enable_discord_attendance, HEADERS, CURRENT, OTHER


USER_ID = "10101010101010101"


def open_setup(page, base):
    """Open the authenticated setup page and wait for its authorized roster."""
    login(page, base)
    page.goto(base + "/admin/discord-attendance")
    playwright.expect(page.locator("#attendanceState")).to_contain_text("Setup records loaded.")


def camper_row(page, submission_id):
    """Find a row using only its public-to-admin minimal registration ID."""
    return page.locator(".attendance-card").filter(
        has=page.locator("[data-submission-id]", has_text=submission_id),
    )


def expand(row, key):
    """Open a native disclosure only if it is closed."""
    details = row.locator(f'details[data-state-key="{key}"]')
    if details.get_attribute("open") is None:
        details.locator(":scope > summary").click()


def fill_link(row):
    """Fill a synthetic parent verification after disclosing the edit form."""
    expand(row, "editor")
    expand(row, "add-link")
    row.locator('[name="discord_user_id"]').fill(USER_ID)
    row.locator('[name="verification_reference"]').fill("parent-check-014")


def test_setup_layout_search_filters_and_drafts(camp, monkeypatch, browser_page):
    enable_discord_attendance(camp, monkeypatch)
    avery_id = camp.add("REG_AVERY", child_first_name="Avery", child_last_name="Quinn")
    camp.add("REG_BLAIR", child_first_name="Blair")
    for number in range(10):
        camp.add(f"REG_SAMPLE_{number}", child_first_name=f"Camper{number:02}")
    linked = camp.client.post("/admin/discord-attendance/links", json={
        "registration_id": avery_id, "session_id": "thanksgiving-2026",
        "discord_user_id": USER_ID, "active": True, "verification_reference": "parent-check-001",
    }, headers=HEADERS)
    assert linked.status_code == 200
    assert camp.client.post("/admin/discord-attendance/pickup-roster", json={
        "camper_id": linked.json["camper_id"], "session_id": "thanksgiving-2026",
        "display_name": "Synthetic Aunt", "active": True,
        "parent_confirmation_reference": "pickup-ok-001",
    }, headers=HEADERS).status_code == 200
    page, base = browser_page
    open_setup(page, base)
    expect = playwright.expect
    expect(page.locator(".attendance-card")).to_have_count(12)
    expect(page.locator(".attendance-card > details[open]")).to_have_count(0)
    expect(page.locator("[data-session-count]")).to_have_text(
        "12 campers · 1 with active parent links · 1 with authorized pickups",
    )
    assert "Segoe UI" in page.locator("body").evaluate("el => getComputedStyle(el).fontFamily")
    for width in (1280, 545, 360):
        page.set_viewport_size({"width": width, "height": 900})
        assert_no_overflow(page)
        assert page.locator(".attendance-session").evaluate("el => el.clientHeight") < 2400
        assert page.locator(".attendance-row").first.evaluate("el => el.clientHeight") < 200
        page.locator(".attendance-toolbar").evaluate("el => el.scrollIntoView({block: 'start'})")
        snapshot(page, f"discord-setup-roster-{width}.png")
    page.select_option("#attendanceFilter", "unlinked")
    expect(page.locator(".attendance-card:visible")).to_have_count(11)
    page.select_option("#attendanceFilter", "no-pickups")
    expect(page.locator(".attendance-card:visible")).to_have_count(11)
    page.select_option("#attendanceFilter", "all")
    page.locator("#attendanceSearch").fill("avery q.")
    expect(page.locator(".attendance-card:visible")).to_have_count(1)
    page.locator("#attendanceSearch").fill("reg_blair")
    expect(page.locator(".attendance-card:visible")).to_have_count(1)
    blair = camper_row(page, "REG_BLAIR")
    blair.locator(":scope > details > summary").focus()
    page.keyboard.press("Enter")
    expect(blair.locator(':scope > details')).to_have_attribute("open", "")
    expand(blair, "add-link")
    blair.locator('[name="discord_user_id"]').fill(USER_ID)
    blair.locator('[name="verification_reference"]').fill("draft-parent-02")
    expand(blair, "add-pickup")
    expect(blair.locator('[data-action="pickup"] button')).to_be_enabled()
    expect(blair.locator('[data-action="pickup"] input').first).to_be_enabled()
    expect(blair).to_contain_text("No Discord account or link is required")
    for width in (1280, 360):
        page.set_viewport_size({"width": width, "height": 900})
        blair.scroll_into_view_if_needed()
        assert_no_overflow(page)
        snapshot(page, f"discord-setup-editor-{width}.png")
    page.get_by_role("button", name="Refresh records", exact=True).click()
    expect(page.locator("#attendanceState")).to_contain_text("Setup records loaded.")
    expect(blair.locator('[name="verification_reference"]')).to_have_value("draft-parent-02")
    expect(blair.locator(':scope > details')).to_have_attribute("open", "")
    expect(page.locator("#attendanceSearch")).to_have_value("reg_blair")
    page.locator("#attendanceSearch").fill("no-synthetic-match")
    expect(page.locator("#attendanceEmpty")).to_be_visible()
    expect(page.locator(".attendance-card:visible")).to_have_count(0)
    page.get_by_role("button", name="Clear filters", exact=True).click()
    expect(page.locator(".attendance-card:visible")).to_have_count(12)
    expect(blair.locator('[name="verification_reference"]')).to_have_value("draft-parent-02")


def test_setup_mutations_preserve_scope_drafts_success_and_reactivation(camp, monkeypatch, browser_page):
    enable_discord_attendance(camp, monkeypatch)
    camp.add("REG_AVERY", child_first_name="Avery")
    camp.add("REG_BLAIR", child_first_name="Blair")
    page, base = browser_page
    open_setup(page, base)
    expect = playwright.expect
    avery = camper_row(page, "REG_AVERY")
    blair = camper_row(page, "REG_BLAIR")
    fill_link(blair)
    blair.locator('[name="verification_reference"]').fill("unsaved-other-parent")
    fill_link(avery)
    page.locator("#attendanceSearch").fill("reg_")
    posts = []
    page.on("request", lambda request: posts.append(request) if request.method == "POST" else None)
    avery.locator('[data-action="link"]').evaluate("form => { form.requestSubmit(); form.requestSubmit(); }")
    expect(page.locator("#attendanceState")).to_have_text("Parent link saved.")
    expect(avery.locator(".attendance-result")).to_have_text("Parent link saved.")
    expect(avery.locator("[data-link-status]")).to_have_text("1 active parent link")
    expect(avery.locator('[name="verification_reference"]')).to_have_value("")
    expect(blair.locator('[name="verification_reference"]')).to_have_value("unsaved-other-parent")
    expect(blair.locator(':scope > details')).to_have_attribute("open", "")
    expect(page.locator("#attendanceSearch")).to_have_value("reg_")
    assert len(posts) == 1
    assert posts[0].post_data_json["session_id"] == "thanksgiving-2026"
    assert posts[0].headers["x-csrf-token"]
    expand(avery, "add-pickup")
    avery.locator('[name="display_name"]').fill("Synthetic Aunt")
    avery.locator('[name="parent_confirmation_reference"]').fill("pickup-ok-014")
    avery.get_by_role("button", name="Add authorized pickup", exact=True).click()
    expect(page.locator("#attendanceState")).to_have_text("Authorized pickup added.")
    expect(avery.locator("[data-pickup-status]")).to_have_text("1 authorized pickup")
    expect(avery.get_by_role("button", name="Revoke pickup", exact=True)).not_to_be_visible()
    avery.get_by_text("Revoke this pickup authorization", exact=True).click()
    revoke_pickup = avery.locator(".attendance-revoke").filter(has_text="Revoke this pickup authorization")
    revoke_pickup.locator("input").fill("pickup-revoke-014")
    revoke_pickup.get_by_role("button", name="Revoke pickup", exact=True).click()
    expect(page.locator("#attendanceState")).to_have_text("Authorized pickup revoked.")
    expect(avery.locator("[data-pickup-status]")).to_have_text("No authorized pickups")
    avery.get_by_text("Revoke this parent link", exact=True).click()
    revoke_link = avery.locator(".attendance-revoke").filter(has_text="Revoke this parent link")
    revoke_link.locator("input").fill("parent-revoke-014")
    revoke_link.get_by_role("button", name="Revoke link", exact=True).click()
    expect(page.locator("#attendanceState")).to_have_text("Parent link revoked.")
    expect(avery.locator("[data-link-status]")).to_have_text("No Discord link (optional)")
    fill_link(avery)
    avery.get_by_role("button", name="Add or reactivate link", exact=True).click()
    expect(page.locator("#attendanceState")).to_have_text("Parent link saved.")
    expect(avery.locator("[data-link-status]")).to_have_text("1 active parent link")
    with closing(sqlite3.connect(camp.database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM discord_parent_links").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM discord_attendance_audit").fetchone()[0] == 5


def test_confirmed_save_with_failed_refresh_is_not_reported_as_failed(camp, monkeypatch, browser_page):
    enable_discord_attendance(camp, monkeypatch)
    camp.add("REG_AVERY", child_first_name="Avery")
    page, base = browser_page
    open_setup(page, base)
    expect = playwright.expect
    row = camper_row(page, "REG_AVERY")
    fill_link(row)
    page.route("**/admin/discord-attendance/roster", lambda route: route.fulfill(
        status=503, content_type="application/json", body='{"error":{"code":"attendance_unavailable"}}',
    ))
    row.get_by_role("button", name="Add or reactivate link", exact=True).click()
    expect(page.locator("#attendanceState")).to_contain_text("Parent link saved.")
    expect(page.locator("#attendanceState")).to_contain_text("may be out of date")
    expect(row.locator(".attendance-result")).to_have_text("Parent link saved.")
    expect(row.get_by_role("button", name="Add or reactivate link", exact=True)).to_be_disabled()
    with closing(sqlite3.connect(camp.database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM discord_parent_links").fetchone()[0] == 1
    page.unroute("**/admin/discord-attendance/roster")
    page.get_by_role("button", name="Refresh records", exact=True).click()
    expect(page.locator("#attendanceState")).to_contain_text("Setup records loaded.")
    expect(row.locator("[data-link-status]")).to_have_text("1 active parent link")
    expect(row.locator(".attendance-result")).to_have_text("Parent link saved.")


def test_unknown_save_retains_draft_and_requires_explicit_refresh(camp, monkeypatch, browser_page):
    enable_discord_attendance(camp, monkeypatch)
    camp.add("REG_AVERY", child_first_name="Avery")
    page, base = browser_page
    open_setup(page, base)
    expect = playwright.expect
    row = camper_row(page, "REG_AVERY")
    fill_link(row)
    posts = []
    page.on("request", lambda request: posts.append(request) if request.method == "POST" else None)
    page.route("**/admin/discord-attendance/links", lambda route: route.abort())
    row.get_by_role("button", name="Add or reactivate link", exact=True).click()
    expect(row.locator(".attendance-result")).to_contain_text("may have reached the server")
    expect(row.locator('[name="verification_reference"]')).to_have_value("parent-check-014")
    expect(row.get_by_role("button", name="Add or reactivate link", exact=True)).to_be_disabled()
    expect(page.locator("#attendanceState")).to_contain_text("Save outcome unknown")
    assert len(posts) == 1
    page.unroute("**/admin/discord-attendance/links")
    page.get_by_role("button", name="Refresh records", exact=True).click()
    expect(page.locator("#attendanceState")).to_contain_text("Setup records loaded.")
    expect(row.locator('[name="verification_reference"]')).to_have_value("parent-check-014")
    expect(row.get_by_role("button", name="Add or reactivate link", exact=True)).to_be_enabled()
    assert len(posts) == 1


def test_setup_deep_link_filters_exact_session_without_substitution(camp, monkeypatch, browser_page):
    enable_discord_attendance(camp, monkeypatch)
    camp.add("REG_FIRST_SESSION", child_first_name="Avery")
    camp.add("REG_SECOND_SESSION", child_first_name="Avery", camp_session=OTHER)
    monkeypatch.setenv("DISCORD_ATTENDANCE_SESSIONS", json.dumps({
        "thanksgiving-2026": {"label": CURRENT, "dates": ["2026-11-23"]},
        "another-session": {"label": OTHER, "dates": ["2026-11-24"]},
    }))
    page, base = browser_page
    login(page, base)
    page.goto(base + "/admin/discord-attendance?search=avery&session_id=another-session")
    expect = playwright.expect
    expect(page.locator("#attendanceState")).to_contain_text("Setup records loaded.")
    expect(page.locator("#attendanceSessionFilter")).to_have_value("another-session")
    expect(page.locator(".attendance-card:visible")).to_have_count(1)
    expect(page.locator(".attendance-card:visible")).to_contain_text("REG_SECOND_SESSION")
    page.get_by_role("button", name="Refresh records", exact=True).click()
    expect(page.locator("#attendanceState")).to_contain_text("Setup records loaded.")
    expect(page.locator("#attendanceSessionFilter")).to_have_value("another-session")
    page.select_option("#attendanceSessionFilter", "")
    expect(page.locator(".attendance-card:visible")).to_have_count(2)
    page.goto(base + "/admin/discord-attendance?search=avery&session_id=missing-session")
    expect(page.locator("#attendanceState")).to_contain_text("no other session was substituted")
    expect(page.locator(".attendance-card:visible")).to_have_count(0)
    page.route("**/admin/discord-attendance/roster", lambda route: route.fulfill(
        status=503, content_type="application/json", body='{"error":{"code":"attendance_unavailable"}}',
    ))
    page.get_by_role("button", name="Refresh records", exact=True).click()
    expect(page.locator("#attendanceState")).to_contain_text("unavailable or misconfigured")
    page.select_option("#attendanceSessionFilter", "thanksgiving-2026")
    expect(page.locator("#attendanceState")).to_contain_text("unavailable or misconfigured")
    page.unroute("**/admin/discord-attendance/roster")
    page.get_by_role("button", name="Refresh records", exact=True).click()
    expect(page.locator("#attendanceState")).to_contain_text("Setup records loaded.")
    expect(page.locator(".attendance-card:visible")).to_have_count(1)
    expect(page.locator(".attendance-card:visible")).to_contain_text("REG_FIRST_SESSION")
