"""Optional real-browser checks against isolated synthetic camp-day records."""

import sqlite3
from contextlib import closing
from datetime import datetime, timezone

from registration_form import discord_attendance as attendance
from test_admin_browser import browser_page, login, snapshot, assert_no_overflow, playwright
from test_staff_camp_day import (
    camp, staff_camp, add_pickup, confirm, roster, DAY, SESSION, USER, PARENT_HEADERS,
)
from test_admin_workflows import HEADERS


def open_camp_day(page, base):
    login(page, base)
    page.goto(base + "/admin/camp-day")
    playwright.expect(page.locator("#campDayState")).to_contain_text("Camp-day records loaded.")


def row_for(page, submission_id):
    return page.locator(".camp-day-row").filter(
        has=page.locator("[data-submission-id]", has_text=submission_id),
    )


def link_parent(camp, registration_id):
    response = camp.client.post(attendance.ADMIN_PREFIX + "/links", json={
        "registration_id": registration_id, "session_id": SESSION,
        "discord_user_id": USER, "active": True, "verification_reference": "verified-014",
    }, headers=HEADERS)
    assert response.status_code == 200
    return response.json["camper_id"]


def parent_request(camp, camper_id, action, key):
    response = camp.client.post(attendance.PREFIX + "/requests", json={
        "camper_id": camper_id, "session_id": SESSION, "date": DAY, "action": action,
    }, headers={**PARENT_HEADERS, "Idempotency-Key": key})
    assert response.status_code == 200


def test_all_states_search_mobile_layout_and_discord_independent_pickup_setup(staff_camp, browser_page):
    camp = staff_camp
    ids = {name: camp.add(f"REG_{name.upper()}", child_first_name=name)
           for name in ("Avery", "Blair", "Casey", "Devon", "Emery")}
    for number in range(7):
        camp.add(f"REG_SAMPLE_{number}", child_first_name=f"Sample{number:02}")
    parent_request(camp, link_parent(camp, ids["Blair"]), "arrival", "parent-arrival-014")
    pickup = add_pickup(camp, ids["Casey"]).json["pickup_id"]
    assert confirm(camp, ids["Casey"], key="casey-arrival").status_code == 200
    assert confirm(camp, ids["Devon"], key="devon-arrival").status_code == 200
    parent_request(camp, link_parent(camp, ids["Devon"]), "pickup", "parent-pickup-014")
    emery_pickup = add_pickup(camp, ids["Emery"]).json["pickup_id"]
    assert confirm(camp, ids["Emery"], key="emery-arrival").status_code == 200
    assert confirm(camp, ids["Emery"], "release", 1, key="emery-release",
                   pickup_id=emery_pickup, roster_verified=True).status_code == 200
    page, base = browser_page
    open_camp_day(page, base)
    expect = playwright.expect
    expect(page.locator(".camp-day-row")).to_have_count(12)
    expect(page.locator("#campDayScope")).to_contain_text("Live camp day: Nov 23, 2026")
    for name, state in [
        ("AVERY", "Not arrived"), ("BLAIR", "Arrival requested via Discord"),
        ("CASEY", "Present"), ("DEVON", "Pickup requested via Discord"), ("EMERY", "Released"),
    ]:
        expect(row_for(page, f"REG_{name}").locator("[data-physical-state]")).to_have_text(state)
    expect(row_for(page, "REG_DEVON").locator("[data-no-pickups]")).to_be_visible()
    expect(row_for(page, "REG_DEVON").get_by_role("button", name="Confirm physical release")).not_to_be_visible()
    for width in (1280, 545, 360):
        page.set_viewport_size({"width": width, "height": 900})
        assert_no_overflow(page)
        row_for(page, "REG_AVERY").evaluate("el => el.scrollIntoView({block: 'start'})")
        snapshot(page, f"camp-day-roster-{width}.png")
        assert row_for(page, "REG_AVERY").get_by_role("button", name="Confirm arrival").evaluate("el => el.offsetHeight") >= 48
    page.locator("#campDaySearch").fill("casey c.")
    expect(page.locator(".camp-day-row:visible")).to_have_count(1)
    casey = row_for(page, "REG_CASEY")
    casey.locator("[data-release] > summary").click()
    casey.locator('[name="pickup_id"]').select_option(pickup)
    expect(casey.locator('[name="roster_verified"]')).not_to_be_checked()
    for width in (1280, 360):
        page.set_viewport_size({"width": width, "height": 900})
        casey.evaluate("el => el.scrollIntoView({block: 'start'})")
        assert_no_overflow(page)
        snapshot(page, f"camp-day-release-{width}.png")
    page.locator("#campDaySearch").fill("reg_avery")
    expect(page.locator(".camp-day-row:visible")).to_have_count(1)
    page.locator("#campDaySearch").fill("no-real-person")
    expect(page.locator("#campDayEmpty")).to_be_visible()
    page.get_by_role("button", name="Clear filters", exact=True).click()
    page.select_option("#campDayFilter", "pickup_requested")
    expect(page.locator(".camp-day-row:visible")).to_have_count(1)
    expect(page.locator(".camp-day-row:visible")).to_contain_text("REG_DEVON")
    page.get_by_role("button", name="Clear filters", exact=True).click()

    # Pickup setup for an unlinked camper is a deliberate authorized action.
    page.goto(base + "/admin/discord-attendance?search=REG_AVERY&session_id=thanksgiving-2026")
    expect(page.locator("#attendanceState")).to_contain_text("Setup records loaded.")
    expect(page.locator(".attendance-card:visible")).to_have_count(1)
    expect(page.locator("#attendanceSessionFilter")).to_have_value(SESSION)
    setup = page.locator(".attendance-card:visible")
    setup.locator(':scope > details > summary').click()
    setup.locator('[data-state-key="add-pickup"] > summary').click()
    setup.locator('[name="display_name"]').fill("Synthetic parent-approved adult")
    setup.locator('[name="parent_confirmation_reference"]').fill("parent-ok-015")
    setup.get_by_role("button", name="Add authorized pickup", exact=True).click()
    expect(page.locator("#attendanceState")).to_have_text("Authorized pickup added.")
    expect(setup.locator("[data-link-status]")).to_have_text("No Discord link (optional)")
    expect(setup.locator("[data-pickup-status]")).to_have_text("1 authorized pickup")


def test_never_linked_browser_family_pickup_arrival_and_release(staff_camp, browser_page):
    camp = staff_camp
    registration_id = camp.add("REG_NEVER_LINKED", child_first_name="Avery")
    page, base = browser_page
    open_camp_day(page, base)
    expect = playwright.expect
    row = row_for(page, "REG_NEVER_LINKED")
    row.get_by_role("button", name="Confirm arrival", exact=True).click()
    expect(page.locator("#campDayState")).to_have_text("Physical arrival confirmed.")
    expect(row.locator("[data-no-pickups]")).to_be_visible()
    with page.expect_navigation():
        row.locator("[data-setup-link]").click()
    expect(page.locator("#attendanceState")).to_contain_text("Setup records loaded.")
    expect(page.locator("#attendanceSearch")).to_have_value("REG_NEVER_LINKED")
    expect(page.locator("#attendanceSessionFilter")).to_have_value(SESSION)
    expect(page.locator(".attendance-card:visible")).to_have_count(1)
    setup = page.locator(".attendance-card:visible")
    setup.locator(":scope > details > summary").click()
    setup.locator('[data-state-key="add-pickup"] > summary').click()
    setup.locator('[name="display_name"]').fill("Synthetic approved collector")
    setup.locator('[name="parent_confirmation_reference"]').fill("parent-confirmed-014")
    setup.get_by_role("button", name="Add authorized pickup", exact=True).click()
    expect(page.locator("#attendanceState")).to_have_text("Authorized pickup added.")
    expect(setup.locator("[data-link-status]")).to_have_text("No Discord link (optional)")
    page.goto(base + "/admin/camp-day?session_id=thanksgiving-2026")
    expect(page.locator("#campDayState")).to_contain_text("Camp-day records loaded.")
    row.locator("[data-release] > summary").click()
    pickup = row.locator('[name="pickup_id"] option').nth(1).get_attribute("value")
    row.locator('[name="pickup_id"]').select_option(pickup)
    row.locator('[name="roster_verified"]').check()
    row.get_by_role("button", name="Confirm physical release", exact=True).click()
    expect(page.locator("#campDayState")).to_have_text("Physical release confirmed.")
    expect(row.locator("[data-physical-state]")).to_have_text("Released")
    assert roster(camp).json["registrations"][0]["registration_id"] == registration_id
    with closing(sqlite3.connect(camp.database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM discord_parent_links").fetchone()[0] == 0
        assert connection.execute("SELECT version FROM discord_attendance").fetchone()[0] == 2
        assert connection.execute("SELECT COUNT(*) FROM discord_attendance_audit WHERE actor_type='admin_web'").fetchone()[0] == 2


def test_staff_browser_arrival_release_stale_version_and_double_submit(staff_camp, browser_page):
    camp = staff_camp
    registration_id = camp.add("REG_UNLINKED", child_first_name="Avery")
    pickup = add_pickup(camp, registration_id).json["pickup_id"]
    page, base = browser_page
    open_camp_day(page, base)
    expect = playwright.expect
    row = row_for(page, "REG_UNLINKED")
    posts = []
    page.on("request", lambda request: posts.append(request) if request.method == "POST" else None)
    page.locator("#campDaySearch").fill("reg_unlinked")
    row.get_by_role("button", name="Confirm arrival", exact=True).evaluate("button => { button.click(); button.click(); }")
    expect(page.locator("#campDayState")).to_have_text("Physical arrival confirmed.")
    expect(row.locator("[data-physical-state]")).to_have_text("Present")
    assert len(posts) == 1
    assert posts[0].post_data_json["registration_id"] == registration_id
    assert posts[0].headers["idempotency-key"]
    assert "authorization" not in posts[0].headers
    expect(page.locator("#campDaySearch")).to_have_value("reg_unlinked")
    row.locator("[data-release] > summary").click()
    row.locator('[name="pickup_id"]').select_option(pickup)
    row.get_by_role("button", name="Confirm physical release", exact=True).click()
    assert len(posts) == 1
    row.locator('[name="roster_verified"]').check()
    camper = link_parent(camp, registration_id)
    parent_request(camp, camper, "pickup", "parent-while-staff-editing")
    row.get_by_role("button", name="Confirm physical release", exact=True).click()
    expect(page.locator("#campDayState")).to_contain_text("Re-check the refreshed physical state")
    expect(row.locator("[data-physical-state]")).to_have_text("Pickup requested via Discord")
    expect(row.locator('[name="roster_verified"]')).not_to_be_checked()
    expect(row.locator('[name="pickup_id"]')).to_have_value("")
    row.locator("[data-release] > summary").click()
    row.locator('[name="pickup_id"]').select_option(pickup)
    row.locator('[name="roster_verified"]').check()
    row.locator("[data-release-form]").evaluate("form => { form.requestSubmit(); form.requestSubmit(); }")
    expect(page.locator("#campDayState")).to_have_text("Physical release confirmed.")
    expect(row.locator("[data-physical-state]")).to_have_text("Released")
    assert len(posts) == 3  # arrival, rejected stale release, explicit successful release
    with closing(sqlite3.connect(camp.database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM discord_attendance_audit WHERE actor_type='admin_web'").fetchone()[0] == 2
    assert roster(camp).json["registrations"][0]["status"]["state"] == "released"


def test_staff_unknown_outcome_refreshes_without_retrying_mutation(staff_camp, browser_page):
    camp = staff_camp
    registration_id = camp.add()
    page, base = browser_page
    open_camp_day(page, base)
    expect = playwright.expect
    posts = []
    page.on("request", lambda request: posts.append(request) if request.method == "POST" else None)

    def accept_then_lose_response(route):
        assert route.fetch().status == 200
        route.abort()

    page.route("**/admin/camp-day/confirmations", accept_then_lose_response)
    page.get_by_role("button", name="Confirm arrival", exact=True).click()
    expect(page.locator("#campDayState")).to_contain_text("Save outcome unknown")
    expect(page.locator("[data-physical-state]")).to_have_text("Present")
    expect(page.locator("[data-no-pickups]")).to_be_visible()
    assert len(posts) == 1
    assert roster(camp).json["registrations"][0]["registration_id"] == registration_id
    with closing(sqlite3.connect(camp.database)) as connection:
        assert connection.execute("SELECT COUNT(*) FROM discord_attendance_audit WHERE date IS NOT NULL").fetchone()[0] == 1


def test_staff_confirmed_save_failed_refresh_and_read_only_preview(staff_camp, monkeypatch, browser_page):
    camp = staff_camp
    camp.add()
    page, base = browser_page
    open_camp_day(page, base)
    expect = playwright.expect
    page.route("**/admin/camp-day/roster*", lambda route: route.fulfill(
        status=503, content_type="application/json", body='{"error":{"code":"attendance_unavailable"}}',
    ))
    page.get_by_role("button", name="Confirm arrival", exact=True).click()
    expect(page.locator("#campDayState")).to_contain_text("Physical arrival confirmed.")
    expect(page.locator("#campDayState")).to_contain_text("may be out of date")
    expect(page.get_by_role("button", name="Confirm arrival", exact=True)).to_be_disabled()
    page.unroute("**/admin/camp-day/roster*")
    page.get_by_role("button", name="Refresh records", exact=True).click()
    expect(page.locator("[data-physical-state]")).to_have_text("Present")
    monkeypatch.setattr(attendance, "utc_now",
                        lambda: datetime(2026, 11, 2, 18, tzinfo=timezone.utc))
    page.reload()
    expect(page.locator("#campDayScope")).to_contain_text("Read-only preview")
    expect(page.locator("#campDayScope")).to_contain_text("Check-in opens Nov 23, 2026")
    expect(page.locator(".camp-day-row button:enabled")).to_have_count(0)
    for width in (1280, 360):
        page.set_viewport_size({"width": width, "height": 900})
        assert_no_overflow(page)
        page.evaluate("window.scrollTo(0, 0)")
        snapshot(page, f"camp-day-preview-{width}.png")
