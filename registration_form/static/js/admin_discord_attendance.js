(() => {
    "use strict";

    const state = document.getElementById("attendanceState");
    const sessionsRoot = document.getElementById("attendanceSessions");
    const search = document.getElementById("attendanceSearch");
    const filter = document.getElementById("attendanceFilter");
    const sessionFilter = document.getElementById("attendanceSessionFilter");
    const refresh = document.getElementById("attendanceRefresh");
    const count = document.getElementById("attendanceCount");
    const empty = document.getElementById("attendanceEmpty");
    const csrfToken = document.querySelector('meta[name="admin-csrf-token"]').content;
    const idPattern = /^[0-9]{17,20}$/;
    const initialQuery = new URLSearchParams(location.search);
    search.value = initialQuery.get("search") || "";
    let selectedSession = initialQuery.get("session_id") || "";
    let saving = false;
    let loading = false;
    let hasRoster = false;
    let fresh = false;

    function showUnavailable(code, savedMessage = "") {
        fresh = false;
        state.classList.add("error");
        const reason = code === "attendance_disabled"
            ? "Discord attendance is off. Enable it in the server configuration to use this page."
            : "Discord attendance is unavailable or misconfigured.";
        state.textContent = `${savedMessage ? savedMessage + " " : ""}${reason} ${
            hasRoster ? "The displayed records may be out of date. Your drafts are retained. " : ""
        }Refresh records before making changes. No change will be retried automatically.`;
        setControls();
    }

    function setControls() {
        refresh.disabled = loading || saving;
        sessionsRoot.setAttribute("aria-busy", String(loading));
        for (const button of sessionsRoot.querySelectorAll('button[type="submit"]')) {
            button.disabled = saving || loading || !fresh;
        }
    }

    function referenceForm(labelText, submitText, callback) {
        const form = document.createElement("form");
        form.className = "attendance-form";
        const label = document.createElement("label");
        label.textContent = labelText;
        const input = document.createElement("input");
        input.name = "reference";
        input.maxLength = 128;
        input.pattern = "[A-Za-z0-9_-]{1,128}";
        input.required = true;
        input.placeholder = "private-record-014";
        label.append(input);
        const button = document.createElement("button");
        button.type = "submit";
        button.className = "btn btn-warning";
        button.textContent = submitText;
        form.append(label, button);
        form.addEventListener("submit", (event) => {
            event.preventDefault();
            const reference = input.value.trim();
            if (!reference) {
                showResult(form.closest(".attendance-card"), "A reference is required.", true);
                return;
            }
            callback(reference, form);
        });
        return form;
    }

    function revokeDisclosure(key, label, referenceLabel, buttonLabel, callback) {
        const details = document.createElement("details");
        details.className = "attendance-revoke";
        details.dataset.stateKey = key;
        const summary = document.createElement("summary");
        summary.textContent = label;
        const hint = document.createElement("p");
        hint.className = "attendance-hint";
        hint.textContent = "Complete the manual verification first. Enter only a nonsecret private record reference (letters, numbers, hyphens or underscores).";
        details.append(summary, hint, referenceForm(referenceLabel, buttonLabel, callback));
        return details;
    }

    function showResult(card, message, isError = false) {
        const result = card.querySelector(".attendance-result");
        result.textContent = message;
        result.classList.toggle("error", isError);
    }

    async function mutate(card, form, route, payload, successMessage) {
        if (saving || loading || !fresh) {
            return;
        }
        saving = true;
        const inputs = [...form.querySelectorAll("input")];
        inputs.forEach((input) => { input.disabled = true; });
        setControls();
        showResult(card, "Saving...");
        try {
            let response;
            try {
                response = await fetch(`/admin/discord-attendance/${route}`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken, "Accept": "application/json" },
                    body: JSON.stringify(payload),
                    credentials: "same-origin",
                });
            } catch (_error) {
                fresh = false;
                showResult(card, "No save confirmation was received. The change may have reached the server. Refresh records and check before trying again; it will not be retried automatically.", true);
                state.classList.add("error");
                state.textContent = "Save outcome unknown. Refresh records before making further changes. Your draft is retained.";
                return;
            }
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                const code = data.error && data.error.code;
                if (code === "attendance_disabled" || code === "attendance_unavailable") {
                    showUnavailable(code);
                }
                if (response.status === 401 || response.status === 403) {
                    fresh = false;
                    state.classList.add("error");
                    state.textContent = "Your admin session or authorization has expired. Sign in again, then refresh records.";
                } else if (response.status >= 500) {
                    fresh = false;
                    showUnavailable(code);
                }
                showResult(card, code === "invalid_request"
                    ? "The server rejected this change. Check the Discord ID, name and required reference, then try again."
                    : "The server did not confirm this change. Refresh records and check before trying again.", true);
                return;
            }
            const confirmation = await response.json().catch(() => null);
            if (response.redirected || !confirmation || confirmation.active !== payload.active) {
                fresh = false;
                state.classList.add("error");
                state.textContent = "The server returned no valid save confirmation. Refresh records and check before trying again.";
                showResult(card, "Save outcome unknown. Your draft is retained. No change will be retried automatically.", true);
                return;
            }
            form.reset();
            showResult(card, successMessage);
            await loadRoster(successMessage);
        } finally {
            saving = false;
            inputs.forEach((input) => { input.disabled = false; });
            setControls();
        }
    }

    function renderRegistration(session, registration) {
        const card = document.getElementById("attendanceRegistrationTemplate").content.firstElementChild.cloneNode(true);
        card.dataset.key = JSON.stringify([session.session_id, registration.registration_id]);
        card.dataset.sessionId = session.session_id;
        card.querySelector("[data-camper-name]").textContent =
            `${registration.child_first_name} ${registration.child_last_initial ? registration.child_last_initial + "." : ""}`.trim();
        card.querySelector("[data-submission-id]").textContent = registration.submission_id;
        card.dataset.search = `${card.querySelector("[data-camper-name]").textContent} ${registration.submission_id}`.toLowerCase();
        const activeLinks = registration.links.filter((link) => link.active).length;
        card.dataset.linked = String(activeLinks > 0);
        card.dataset.pickups = String(registration.pickups.length > 0);
        const linkStatus = card.querySelector("[data-link-status]");
        linkStatus.textContent = activeLinks ? `${activeLinks} active parent ${activeLinks === 1 ? "link" : "links"}` : "No Discord link (optional)";
        linkStatus.classList.toggle("active", activeLinks > 0);
        const pickupStatus = card.querySelector("[data-pickup-status]");
        pickupStatus.textContent = registration.pickups.length
            ? `${registration.pickups.length} authorized ${registration.pickups.length === 1 ? "pickup" : "pickups"}`
            : "No authorized pickups";
        pickupStatus.classList.toggle("active", registration.pickups.length > 0);

        const links = card.querySelector("[data-links]");
        if (!registration.links.length) {
            const empty = document.createElement("li");
            empty.textContent = "No parent links.";
            links.append(empty);
        }
        for (const link of registration.links) {
            const item = document.createElement("li");
            item.append(document.createTextNode(`${link.discord_user_id} — ${link.active ? "active" : "revoked"}`));
            if (link.active) {
                item.append(revokeDisclosure(`revoke-link-${link.discord_user_id}`, "Revoke this parent link",
                    "Revocation verification reference", "Revoke link", (reference, form) => {
                    mutate(card, form, "links", {
                        registration_id: registration.registration_id,
                        session_id: session.session_id,
                        discord_user_id: link.discord_user_id,
                        active: false,
                        verification_reference: reference,
                    }, "Parent link revoked.");
                }));
            }
            links.append(item);
        }

        const pickups = card.querySelector("[data-pickups]");
        if (!registration.pickups.length) {
            const empty = document.createElement("li");
            empty.textContent = "No active authorized pickups.";
            pickups.append(empty);
        }
        for (const pickup of registration.pickups) {
            const item = document.createElement("li");
            item.append(document.createTextNode(pickup.display_name));
            item.append(revokeDisclosure(`revoke-pickup-${pickup.pickup_id}`, "Revoke this pickup authorization",
                "Revocation parent confirmation reference", "Revoke pickup", (reference, form) => {
                mutate(card, form, "pickup-roster", {
                    camper_id: registration.camper_id,
                    session_id: session.session_id,
                    parent_confirmation_reference: reference,
                    active: false,
                    pickup_id: pickup.pickup_id,
                }, "Authorized pickup revoked.");
            }));
            pickups.append(item);
        }

        card.querySelector('[data-action="link"]').addEventListener("submit", (event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const userId = form.elements.discord_user_id.value.trim();
            const reference = form.elements.verification_reference.value.trim();
            if (!idPattern.test(userId) || !reference) {
                showResult(card, "Enter a 17–20 digit Discord user ID and a verification reference.", true);
                return;
            }
            mutate(card, form, "links", {
                registration_id: registration.registration_id,
                session_id: session.session_id,
                discord_user_id: userId,
                active: true,
                verification_reference: reference,
            }, "Parent link saved.");
        });
        const pickupForm = card.querySelector('[data-action="pickup"]');
        pickupForm.addEventListener("submit", (event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const displayName = form.elements.display_name.value.trim();
            const reference = form.elements.parent_confirmation_reference.value.trim();
            if (!displayName || !reference) {
                showResult(card, "Enter a pickup name and parent confirmation reference.", true);
                return;
            }
            mutate(card, form, "pickup-roster", {
                ...(registration.camper_id == null
                    ? { registration_id: registration.registration_id }
                    : { camper_id: registration.camper_id }),
                session_id: session.session_id,
                parent_confirmation_reference: reference,
                active: true,
                display_name: displayName,
            }, "Authorized pickup added.");
        });
        return card;
    }

    function applyFilters() {
        if (fresh && state.dataset.scopeError === "true" && sessionFilter.selectedOptions[0]?.dataset.unavailable !== "true") {
            state.dataset.scopeError = "false";
            state.classList.remove("error");
            state.textContent = "Setup records loaded. Expand a camper row to manage parent access and pickups.";
        }
        let visible = 0;
        const cards = sessionsRoot.querySelectorAll(".attendance-card");
        const query = search.value.trim().toLowerCase();
        for (const card of cards) {
            card.hidden = !card.dataset.search.includes(query)
                || Boolean(selectedSession && card.dataset.sessionId !== selectedSession)
                || (filter.value === "unlinked" && card.dataset.linked === "true")
                || (filter.value === "no-pickups" && card.dataset.pickups === "true");
            if (!card.hidden) visible += 1;
        }
        for (const section of sessionsRoot.querySelectorAll(".attendance-session")) {
            const rows = [...section.querySelectorAll(".attendance-card")];
            section.hidden = rows.length ? rows.every((row) => row.hidden)
                : Boolean(query || filter.value !== "all" || (selectedSession && section.dataset.sessionId !== selectedSession));
        }
        count.textContent = hasRoster ? `Showing ${visible} of ${cards.length} campers. Counts describe access and pickup setup only.` : "";
        empty.hidden = !hasRoster || visible > 0;
        empty.textContent = cards.length
            ? "No campers match these filters. Clear filters to see the full setup roster."
            : "No eligible registrations in the configured sessions. Check the registration session and server configuration.";
    }

    function captureDrafts() {
        const drafts = new Map();
        for (const card of sessionsRoot.querySelectorAll(".attendance-card")) {
            const details = [...card.querySelectorAll("details")].map((element) => [element.dataset.stateKey, element.open]);
            const forms = [...card.querySelectorAll("form")].map((form) => ({
                key: form.dataset.action || form.closest("details").dataset.stateKey,
                values: [...form.querySelectorAll("input")].map((input) => [input.name, input.value]),
            }));
            const result = card.querySelector(".attendance-result");
            drafts.set(card.dataset.key, { details, forms, message: result.textContent, error: result.classList.contains("error") });
        }
        return drafts;
    }

    function restoreDrafts(drafts) {
        for (const card of sessionsRoot.querySelectorAll(".attendance-card")) {
            const draft = drafts.get(card.dataset.key);
            if (!draft) continue;
            for (const details of card.querySelectorAll("details")) {
                details.open = draft.details.some(([key, open]) => key === details.dataset.stateKey && open);
            }
            for (const form of card.querySelectorAll("form")) {
                const key = form.dataset.action || form.closest("details").dataset.stateKey;
                const saved = draft.forms.find((item) => item.key === key);
                if (!saved) continue;
                for (const input of form.querySelectorAll("input")) {
                    input.value = saved.values.find(([name]) => name === input.name)?.[1] || "";
                }
            }
            showResult(card, draft.message, draft.error);
        }
    }

    async function loadRoster(savedMessage = "") {
        if (loading) return;
        loading = true;
        setControls();
        state.classList.remove("error");
        state.textContent = savedMessage ? `${savedMessage} Refreshing records...` : "Loading Discord attendance records for access setup...";
        try {
            const response = await fetch("/admin/discord-attendance/roster", {
                credentials: "same-origin",
                headers: { "Accept": "application/json" },
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                showUnavailable(data.error && data.error.code, savedMessage);
                return;
            }
            if (!Array.isArray(data.sessions)) throw new Error("Invalid roster response");
            const drafts = captureDrafts();
            const focused = document.activeElement;
            const focusedCard = focused.closest(".attendance-card")?.dataset.key;
            const focusedForm = focused.closest("form");
            const focusedFormKey = focusedForm?.dataset.action || focusedForm?.closest("details").dataset.stateKey;
            const focusedDetailsKey = focused.closest("details")?.dataset.stateKey;
            const scrollPosition = window.scrollY;
            const fragment = document.createDocumentFragment();
            for (const session of data.sessions) {
                const section = document.getElementById("attendanceSessionTemplate").content.firstElementChild.cloneNode(true);
                section.dataset.sessionId = session.session_id;
                section.querySelector("[data-session-label]").textContent = session.label;
                const linked = session.registrations.filter((registration) => registration.links.some((link) => link.active)).length;
                const pickups = session.registrations.filter((registration) => registration.pickups.length > 0).length;
                section.querySelector("[data-session-count]").textContent =
                    `${session.registrations.length} campers · ${linked} with active parent links · ${pickups} with authorized pickups`;
                const registrations = section.querySelector("[data-registrations]");
                for (const registration of session.registrations) {
                    registrations.append(renderRegistration(session, registration));
                }
                if (!session.registrations.length) {
                    const empty = document.createElement("p");
                    empty.className = "empty-state";
                    empty.textContent = "No eligible registrations for this session.";
                    registrations.append(empty);
                }
                fragment.append(section);
            }
            sessionsRoot.replaceChildren(fragment);
            restoreDrafts(drafts);
            const allSessions = document.createElement("option");
            allSessions.value = "";
            allSessions.textContent = "All configured sessions";
            sessionFilter.replaceChildren(allSessions, ...data.sessions.map((session) => {
                const option = document.createElement("option");
                option.value = session.session_id;
                option.textContent = session.label;
                return option;
            }));
            const missingSession = selectedSession && !data.sessions.some((session) => session.session_id === selectedSession);
            if (missingSession) {
                const missing = document.createElement("option");
                missing.value = selectedSession;
                missing.dataset.unavailable = "true";
                missing.textContent = "Selected session unavailable";
                sessionFilter.append(missing);
            }
            sessionFilter.value = selectedSession;
            hasRoster = true;
            fresh = true;
            applyFilters();
            if (focusedCard) {
                const card = [...sessionsRoot.querySelectorAll(".attendance-card")].find((item) => item.dataset.key === focusedCard);
                const form = card && [...card.querySelectorAll("form")].find((item) =>
                    (item.dataset.action || item.closest("details").dataset.stateKey) === focusedFormKey);
                const control = form && [...form.elements].find((item) => focused.name ? item.name === focused.name : item.tagName === focused.tagName);
                const details = card && [...card.querySelectorAll("details")].find((item) => item.dataset.stateKey === focusedDetailsKey);
                (control || details?.querySelector("summary") || card?.querySelector("summary"))?.focus({ preventScroll: true });
                window.scrollTo({ top: scrollPosition });
            }
            state.textContent = missingSession
                ? "The selected session is unavailable. Choose a configured camp session; no other session was substituted."
                : savedMessage || "Setup records loaded. Expand a camper row to manage parent access and pickups.";
            state.classList.toggle("error", Boolean(missingSession));
            state.dataset.scopeError = String(Boolean(missingSession));
        } catch (_error) {
            showUnavailable("attendance_unavailable", savedMessage);
        } finally {
            loading = false;
            setControls();
        }
    }

    search.addEventListener("input", applyFilters);
    filter.addEventListener("change", applyFilters);
    sessionFilter.addEventListener("change", () => {
        selectedSession = sessionFilter.value;
        applyFilters();
    });
    document.getElementById("attendanceClear").addEventListener("click", () => {
        search.value = "";
        filter.value = "all";
        selectedSession = "";
        sessionFilter.value = "";
        applyFilters();
        search.focus();
    });
    refresh.addEventListener("click", () => loadRoster());
    loadRoster();
})();
