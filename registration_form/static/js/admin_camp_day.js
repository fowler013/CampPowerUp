(() => {
    "use strict";

    const root = document.getElementById("campDayRoster");
    const state = document.getElementById("campDayState");
    const scope = document.getElementById("campDayScope");
    const sessionSelect = document.getElementById("campDaySession");
    const search = document.getElementById("campDaySearch");
    const filter = document.getElementById("campDayFilter");
    const refresh = document.getElementById("campDayRefresh");
    const count = document.getElementById("campDayCount");
    const empty = document.getElementById("campDayEmpty");
    const csrf = document.querySelector('meta[name="admin-csrf-token"]').content;
    const labels = {
        not_arrived: "Not arrived",
        arrival_requested: "Arrival requested via Discord",
        present: "Present",
        pickup_requested: "Pickup requested via Discord",
        released: "Released",
    };
    const messages = new Map();
    let roster = null;
    let fresh = false;
    let loading = false;
    let saving = false;
    let selectedSession = new URLSearchParams(location.search).get("session_id") || "";

    function setControls() {
        const busy = loading || saving;
        refresh.disabled = busy;
        sessionSelect.disabled = busy || !roster;
        root.setAttribute("aria-busy", String(busy));
        for (const control of root.querySelectorAll("button, input, select")) {
            control.disabled = busy || !fresh || !roster?.write_enabled;
        }
    }

    function showState(message, error = false) {
        state.textContent = message;
        state.classList.toggle("error", error);
    }

    function rowKey(registration) {
        return JSON.stringify([roster.session_id, registration.registration_id]);
    }

    function showResult(key, message, error = false) {
        messages.set(key, { message, error });
        const row = [...root.children].find((item) => item.dataset.key === key);
        if (row) {
            const result = row.querySelector(".attendance-result");
            result.textContent = message;
            result.classList.toggle("error", error);
        }
    }

    function applyFilters() {
        let visible = 0;
        const query = search.value.trim().toLowerCase();
        for (const row of root.children) {
            row.hidden = !row.dataset.search.includes(query)
                || (filter.value !== "all" && filter.value !== row.dataset.state);
            if (!row.hidden) visible += 1;
        }
        count.textContent = roster ? `Showing ${visible} of ${root.children.length} campers in this session and date.` : "";
        empty.hidden = !roster || visible > 0;
        empty.textContent = root.children.length
            ? "No campers match these filters. Clear filters to see the full roster."
            : "No eligible registrations in this configured session. Check the exact registration session before camp-day operations.";
    }

    function formatDate(day) {
        return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" })
            .format(new Date(`${day}T12:00:00Z`));
    }

    function captureDrafts() {
        return new Map([...root.children].map((row) => [row.dataset.key, {
            signature: row.dataset.signature,
            open: row.querySelector("[data-release]").open,
            pickup: row.querySelector('[name="pickup_id"]').value,
            verified: row.querySelector('[name="roster_verified"]').checked,
        }]));
    }

    function renderRegistration(registration, drafts) {
        const row = document.getElementById("campDayRowTemplate").content.firstElementChild.cloneNode(true);
        const key = rowKey(registration);
        const physical = registration.status.state;
        if (!Object.hasOwn(labels, physical)) throw new Error("Unrecognized physical state");
        row.dataset.key = key;
        row.dataset.state = physical;
        row.dataset.signature = JSON.stringify([roster.date, registration.status.version, registration.pickups]);
        const name = `${registration.child_first_name} ${registration.child_last_initial ? registration.child_last_initial + "." : ""}`.trim();
        row.dataset.search = `${name} ${registration.submission_id}`.toLowerCase();
        row.querySelector("[data-camper-name]").textContent = name;
        row.querySelector("[data-submission-id]").textContent = registration.submission_id;
        const badge = row.querySelector("[data-physical-state]");
        badge.textContent = labels[physical];
        badge.dataset.state = physical;
        row.querySelector("[data-discord-request]").textContent = physical === "arrival_requested"
            ? "Parent request only. Staff must confirm physical arrival."
            : physical === "pickup_requested" ? "Parent request only. Check the pickup person before release." : "";
        const arrival = row.querySelector("[data-arrival]");
        arrival.hidden = !["not_arrived", "arrival_requested"].includes(physical);
        arrival.addEventListener("click", () => confirm(registration, "arrival"));
        const canRelease = ["present", "pickup_requested"].includes(physical);
        const release = row.querySelector("[data-release]");
        release.hidden = !canRelease || !registration.pickups.length;
        row.querySelector("[data-no-pickups]").hidden = !canRelease || registration.pickups.length > 0;
        row.querySelector("[data-released]").hidden = physical !== "released";
        row.querySelector("[data-setup-link]").href =
            `/admin/discord-attendance?search=${encodeURIComponent(registration.submission_id)}&session_id=${encodeURIComponent(roster.session_id)}`;
        const pickup = row.querySelector('[name="pickup_id"]');
        for (const person of registration.pickups) {
            const option = document.createElement("option");
            option.value = person.pickup_id;
            option.textContent = person.display_name;
            pickup.append(option);
        }
        const verified = row.querySelector('[name="roster_verified"]');
        const draft = drafts.get(key);
        // A changed physical version, date or pickup roster requires a new manual check.
        if (draft && draft.signature === row.dataset.signature) {
            release.open = draft.open;
            pickup.value = draft.pickup;
            verified.checked = draft.verified;
        }
        row.querySelector("[data-release-form]").addEventListener("submit", (event) => {
            event.preventDefault();
            if (!verified.checked || !registration.pickups.some((person) => person.pickup_id === pickup.value)) {
                showResult(key, "Select a current authorized pickup and confirm you checked the person before release.", true);
                return;
            }
            confirm(registration, "release", { pickup_id: pickup.value, roster_verified: true });
        });
        const message = messages.get(key);
        if (message) {
            row.querySelector(".attendance-result").textContent = message.message;
            row.querySelector(".attendance-result").classList.toggle("error", message.error);
        }
        return row;
    }

    async function loadRoster(outcome = "", outcomeError = false) {
        if (loading) return;
        loading = true;
        setControls();
        showState(outcome ? `${outcome} Refreshing records...` : "Loading camp-day records...", outcomeError);
        try {
            const query = selectedSession ? `?session_id=${encodeURIComponent(selectedSession)}` : "";
            const response = await fetch(`/admin/camp-day/roster${query}`, {
                credentials: "same-origin", headers: { "Accept": "application/json" },
            });
            const data = await response.json().catch(() => null);
            if (!response.ok) {
                const code = data?.error?.code;
                const reason = response.status === 401 || response.status === 403
                    ? "Your admin session or authorization has expired. Sign in again."
                    : code === "attendance_disabled" ? "Camp-day attendance is disabled in the server configuration."
                        : "Camp-day records are unavailable or misconfigured.";
                throw new Error(reason);
            }
            if (!data || !Array.isArray(data.sessions) || !Array.isArray(data.registrations)
                || typeof data.write_enabled !== "boolean") {
                throw new Error("The server returned an invalid camp-day roster.");
            }
            const drafts = captureDrafts();
            const previous = roster;
            roster = data;
            const fragment = document.createDocumentFragment();
            try {
                for (const registration of data.registrations) fragment.append(renderRegistration(registration, drafts));
            } catch (error) {
                roster = previous;
                throw error;
            }
            root.replaceChildren(fragment);
            selectedSession = data.session_id;
            sessionSelect.replaceChildren(...data.sessions.map((session) => {
                const option = document.createElement("option");
                option.value = session.session_id;
                option.textContent = session.label;
                option.selected = session.session_id === selectedSession;
                return option;
            }));
            scope.textContent = data.write_enabled
                ? `Live camp day: ${formatDate(data.date)} (America/Chicago). Confirm only physical arrival and release.`
                : data.date >= data.today
                    ? `Read-only preview for ${formatDate(data.date)}. Check-in opens ${formatDate(data.date)} (America/Chicago). No physical attendance can be changed today.`
                    : `Read-only: this session's configured camp dates have ended. Showing ${formatDate(data.date)} (America/Chicago).`;
            fresh = true;
            applyFilters();
            showState(outcome || "Camp-day records loaded. Refresh to see changes made by other staff.", outcomeError);
        } catch (error) {
            fresh = false;
            showState(`${outcome ? outcome + " " : ""}${error.message} ${
                roster ? "Displayed records may be out of date. " : ""
            }Refresh records before making changes. No confirmation will be retried automatically.`, true);
        } finally {
            loading = false;
            setControls();
        }
    }

    async function confirm(registration, action, extra = {}) {
        if (saving || loading || !fresh || !roster.write_enabled) return;
        saving = true;
        const key = rowKey(registration);
        const payload = {
            registration_id: registration.registration_id,
            session_id: roster.session_id,
            date: roster.date,
            action,
            expected_version: registration.status.version,
            ...extra,
        };
        setControls();
        showResult(key, "Saving staff confirmation...");
        try {
            let response;
            let result;
            try {
                response = await fetch("/admin/camp-day/confirmations", {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json", "Accept": "application/json",
                        "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID(),
                    },
                    body: JSON.stringify(payload),
                });
                result = await response.json().catch(() => null);
            } catch (_error) {
                const message = "Save outcome unknown: the confirmation may have reached the server. Review refreshed state before any further action. No automatic retry.";
                fresh = false;
                showResult(key, message, true);
                await loadRoster(message, true);
                return;
            }
            if (!response.ok) {
                const code = result?.error?.code;
                const message = code === "stale_version"
                    ? "Another action changed this camper's record. Re-check the refreshed physical state and pickup list before confirming again."
                    : code === "invalid_request"
                        ? "Confirmation rejected. Check today's configured date and the required pickup selection and staff verification."
                        : "Confirmation was not accepted. Re-check the refreshed record and authorized pickup list; sign in again if your admin session expired.";
                fresh = false;
                showResult(key, message, true);
                await loadRoster(message, true);
                return;
            }
            if (response.redirected || !result || result.state !== (action === "arrival" ? "present" : "released")
                || result.version !== payload.expected_version + 1) {
                const message = "No valid save confirmation was received. Review refreshed state before any further action. No automatic retry.";
                fresh = false;
                showResult(key, message, true);
                await loadRoster(message, true);
                return;
            }
            const message = action === "arrival" ? "Physical arrival confirmed." : "Physical release confirmed.";
            showResult(key, message);
            await loadRoster(message);
        } finally {
            saving = false;
            setControls();
        }
    }

    search.addEventListener("input", applyFilters);
    filter.addEventListener("change", applyFilters);
    sessionSelect.addEventListener("change", () => {
        selectedSession = sessionSelect.value;
        fresh = false;
        loadRoster();
    });
    document.getElementById("campDayClear").addEventListener("click", () => {
        search.value = "";
        filter.value = "all";
        applyFilters();
        search.focus();
    });
    refresh.addEventListener("click", () => loadRoster());
    loadRoster();
})();
