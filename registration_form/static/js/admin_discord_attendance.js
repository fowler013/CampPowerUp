(() => {
    "use strict";

    const state = document.getElementById("attendanceState");
    const sessionsRoot = document.getElementById("attendanceSessions");
    const csrfToken = document.querySelector('meta[name="admin-csrf-token"]').content;
    const idPattern = /^[0-9]{17,20}$/;

    function showUnavailable(code) {
        state.classList.add("error");
        state.textContent = code === "attendance_disabled"
            ? "Discord attendance is off. Enable it in the server configuration to use this page."
            : "Discord attendance is unavailable or misconfigured. No changes were made.";
        sessionsRoot.replaceChildren();
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
            callback(reference);
        });
        return form;
    }

    function showResult(card, message, isError = false) {
        const result = card.querySelector(".attendance-result");
        result.textContent = message;
        result.classList.toggle("error", isError);
    }

    async function mutate(card, route, payload, successMessage) {
        let response;
        let data;
        try {
            response = await fetch(`/admin/discord-attendance/${route}`, {
                method: "POST",
                headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken },
                body: JSON.stringify(payload),
                credentials: "same-origin",
            });
            data = await response.json().catch(() => ({}));
        } catch (_error) {
            showResult(card, "The change could not reach the server. No confirmation was received.", true);
            return;
        }
        if (!response.ok) {
            const code = data.error && data.error.code;
            if (code === "attendance_disabled" || code === "attendance_unavailable") {
                showUnavailable(code);
            }
            showResult(card, code === "invalid_request"
                ? "Check the Discord ID and required reference, then try again."
                : "The change was not saved. Reload the page and try again.", true);
            return;
        }
        showResult(card, successMessage);
        await loadRoster();
    }

    function renderRegistration(session, registration) {
        const card = document.getElementById("attendanceRegistrationTemplate").content.firstElementChild.cloneNode(true);
        card.querySelector("[data-camper-name]").textContent =
            `${registration.child_first_name} ${registration.child_last_initial ? registration.child_last_initial + "." : ""}`.trim();
        card.querySelector("[data-submission-id]").textContent = registration.submission_id;

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
                item.append(referenceForm("Revocation verification reference", "Revoke link", (reference) => {
                    mutate(card, "links", {
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
            item.append(referenceForm("Revocation parent confirmation reference", "Revoke pickup", (reference) => {
                mutate(card, "pickup-roster", {
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
            mutate(card, "links", {
                registration_id: registration.registration_id,
                session_id: session.session_id,
                discord_user_id: userId,
                active: true,
                verification_reference: reference,
            }, "Parent link saved.");
        });
        card.querySelector('[data-action="pickup"]').addEventListener("submit", (event) => {
            event.preventDefault();
            const form = event.currentTarget;
            const displayName = form.elements.display_name.value.trim();
            const reference = form.elements.parent_confirmation_reference.value.trim();
            if (!displayName || !reference) {
                showResult(card, "Enter a pickup name and parent confirmation reference.", true);
                return;
            }
            mutate(card, "pickup-roster", {
                camper_id: registration.camper_id,
                session_id: session.session_id,
                parent_confirmation_reference: reference,
                active: true,
                display_name: displayName,
            }, "Authorized pickup added.");
        });
        return card;
    }

    async function loadRoster() {
        state.classList.remove("error");
        state.textContent = "Loading Discord attendance records…";
        try {
            const response = await fetch("/admin/discord-attendance/roster", {
                credentials: "same-origin",
                headers: { "Accept": "application/json" },
            });
            const data = await response.json().catch(() => ({}));
            if (!response.ok) {
                showUnavailable(data.error && data.error.code);
                return;
            }
            sessionsRoot.replaceChildren();
            for (const session of data.sessions) {
                const section = document.getElementById("attendanceSessionTemplate").content.firstElementChild.cloneNode(true);
                section.querySelector("[data-session-label]").textContent = session.label;
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
                sessionsRoot.append(section);
            }
            state.textContent = "Discord attendance records loaded.";
        } catch (_error) {
            showUnavailable("attendance_unavailable");
        }
    }

    loadRoster();
})();
