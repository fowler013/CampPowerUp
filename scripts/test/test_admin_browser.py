"""Optional local-only Playwright checks; pass this file to run_registration_tests.py."""

import os
from pathlib import Path
from threading import Thread

import pytest
from werkzeug.serving import make_server

playwright = pytest.importorskip("playwright.sync_api")
from test_admin_workflows import CURRENT, OTHER, camp, scoped
from registration_form import app as registration_app
from registration_form.camp_config import DEFAULT_SESSION_ID


@pytest.fixture
def browser_page(camp):
    server = make_server("127.0.0.1", 0, registration_app.app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_port}"
    try:
        with playwright.sync_playwright() as runtime:
            browser = runtime.chromium.launch(channel=os.environ.get("CAMP_BROWSER_CHANNEL"))
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.set_default_timeout(10000)
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            page.route("**/*", lambda route: (
                route.continue_() if route.request.url.startswith(base + "/") else route.abort()
            ))
            try:
                yield page, base
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def login(page, base):
    page.goto(base + "/admin/login")
    page.locator('input[name="username"]').fill("test-admin")
    page.locator('input[name="password"]').fill("synthetic-test-password")
    with page.expect_navigation():
        page.locator('button[type="submit"]').click()
    assert page.url.endswith("/admin")
    page.on("dialog", lambda dialog: dialog.accept())


def snapshot(page, name):
    directory = os.environ.get("CAMP_UI_ARTIFACT_DIR")
    if directory:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(target / name), full_page=False)


def assert_no_overflow(page):
    sizes = page.evaluate("({content: document.documentElement.scrollWidth, viewport: innerWidth})")
    assert sizes["content"] <= sizes["viewport"], sizes


def test_dashboard_layout_search_scope_and_actions(camp, browser_page):
    page, base = browser_page
    for number in range(13):
        camp.add(f"REG_CURRENT_{number}")
    for number in range(3):
        camp.add(f"REG_OTHER_{number}", camp_session=OTHER)
    login(page, base)
    page.goto(base + scoped())
    expect = playwright.expect
    expect(page.locator("#totalRegistrations")).to_have_text("13")
    for width in (1280, 656, 360):
        page.set_viewport_size({"width": width, "height": 900})
        assert_no_overflow(page)
        if width == 656:
            assert page.locator(".admin-nav-links").evaluate("element => element.clientHeight") <= 150
        snapshot(page, f"camp-admin-{width}.png")
    page.locator("#searchInput").fill("not-a-real-camper")
    expect(page.locator(".registration-card:visible")).to_have_count(0)
    expect(page.locator("#noSearchResults")).to_be_visible()
    expect(page.locator("#totalRegistrations")).to_have_text("13")
    page.get_by_role("button", name="Clear", exact=True).click()
    expect(page.locator(".registration-card:visible")).to_have_count(13)

    page.select_option("#sessionFilter", OTHER)
    with page.expect_navigation():
        page.get_by_role("button", name="Apply session").click()
    expect(page.locator("#totalRegistrations")).to_have_text("3")
    assert page.locator('button[data-action="reminder"]:enabled').count() == 0
    page.goto(base + scoped())
    with page.expect_navigation():
        page.locator('button[data-action="paid"]').first.click()
    expect(page.locator("#paidRegistrations")).to_have_text("1")
    page.locator('button[data-action="reminder"]:enabled').first.click()
    expect(page.locator(".toast")).to_contain_text("sent")
    assert camp.email.call_count == 1
    with page.expect_navigation():
        page.locator('button[data-action="delete"]').first.click()
    expect(page.locator("#totalRegistrations")).to_have_text("12")
    assert len(camp.rows()) == 15

    page.route("**/admin/mark-paid/*", lambda route: route.fulfill(
        status=401, content_type="application/json", body='{"success": false}',
    ))
    page.locator('button[data-action="paid"]:enabled').first.click()
    expect(page.locator('.toast[role="alert"]')).to_contain_text("session expired")
    assert_no_overflow(page)


def test_settings_and_related_pages_in_browser(camp, browser_page):
    page, base = browser_page
    camp.add()
    login(page, base)
    expect = playwright.expect
    for path in ("/admin/config", "/admin/historical", "/admin/verify-returning-campers", "/admin/metrics"):
        page.goto(base + scoped(path))
        for width in (1280, 360):
            page.set_viewport_size({"width": width, "height": 900})
            assert_no_overflow(page)
    expect(page.locator("#chartStatus")).to_be_visible()
    expect(page.locator(".charts-grid")).not_to_be_visible()
    page.goto(base + scoped("/admin/config"))
    page.locator("#new_final").fill("70")
    page.get_by_role("button", name="Preview fees").click()
    expect(page.locator("#status")).to_contain_text("New campers: $120 total")
    with page.expect_navigation():
        page.get_by_role("button", name="Save configuration").click()
    expect(page.locator("#new_final")).to_have_value("70")
    page.goto(base + "/")
    expect(page.locator("body")).to_contain_text("$120 total")
    assert camp.rows()[0]["camp_session"] == CURRENT


def test_public_form_submits_and_restores_draft_safely(camp, browser_page):
    page, base = browser_page
    page.goto(base + "/")
    page.evaluate("""() => localStorage.setItem('campPowerUpDraft', JSON.stringify({
        camp_session_id: 'retired-session',
        child_first_name: 'Browser', child_last_name: 'Synthetic', child_age: '10',
        parent_email: 'browser@example.test', is_returning_camper: 'true',
        previous_year: '2025', has_sensory_issues: 'true', sensory_details: 'Synthetic note'
    }))""")
    page.reload()
    expect = playwright.expect
    expect(page.locator('input[name="camp_session_id"]')).to_have_value(DEFAULT_SESSION_ID)
    expect(page.locator("#previous_year")).to_be_visible()
    expect(page.locator("#sensory_details")).to_be_visible()
    with page.expect_navigation():
        page.get_by_role("button", name="Submit Registration").click()
    assert "/confirmation/REG_" in page.url
    assert len(camp.rows()) == 1
    row = camp.rows()[0]
    assert row["camp_session"] == CURRENT
    assert row["is_returning_camper"] == row["has_medical_conditions"] == 1
    assert row["medical_conditions_description"] == "Synthetic note"
    expect(page.locator("body")).to_contain_text("Browser Synthetic")
    assert page.evaluate("localStorage.getItem('campPowerUpDraft')") is None


def test_public_form_reports_server_errors_without_false_confirmation(camp, browser_page):
    page, base = browser_page
    page.goto(base + "/")
    for name, value in {
        "parent_email": "browser@example.test", "child_first_name": "Browser",
        "child_last_name": "Synthetic", "child_age": "10",
    }.items():
        page.locator(f"#{name}").fill(value)
    page.locator("#returning_no").check()
    page.route("**/submit", lambda route: route.fulfill(
        status=409, content_type="application/json",
        body='{"success": false, "error": "Registration is closed for this camp session."}',
    ))
    messages = []
    page.on("dialog", lambda dialog: (messages.append(dialog.message), dialog.accept()))
    page.get_by_role("button", name="Submit Registration").click()
    playwright.expect(page.locator("#submitBtn")).to_be_enabled()
    assert messages and "Registration is closed" in messages[0]
    assert "/confirmation/" not in page.url
    assert camp.rows() == []


def test_attendance_and_payment_controls_persist(camp, browser_page):
    page, base = browser_page
    camp.add()
    login(page, base)
    page.goto(base + "/admin/attendance")
    page.locator("button.status-btn.present").click()
    playwright.expect(page.locator("#present-count")).to_have_text("1")
    page.locator(".payment-btn").click()
    playwright.expect(page.locator(".payment-badge")).to_contain_text("Paid")
    assert camp.rows()[0]["payment_status"] == "paid"
    page.locator('.date-tab[data-date="2026-11-24"]').click()
    playwright.expect(page.locator("#present-count")).to_have_text("0")
    page.locator('.date-tab[data-date="2026-11-23"]').click()
    playwright.expect(page.locator("#present-count")).to_have_text("1")
    playwright.expect(page.locator("#attendanceStatus")).to_be_empty()
