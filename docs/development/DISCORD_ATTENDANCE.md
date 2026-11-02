# Private Discord attendance API

CampPowerUp is the authoritative persistent store; Kit is only the private
Discord interface. A request never confirms physical arrival or release.
No photo-ID collection, WhatsApp integration, public attendance messages,
automatic family matching, or production activation is included.

## Deployment gate and trust boundary

Disabled by default. Do not enable until an operator has verified the deployment's
persistent registration SQLite volume, strong admin signing secret (at least 32
characters), admin credentials, HTTPS, private Discord behavior, and synthetic
end-to-end testing. This runs in `registration_form/app.py` (the registration
service), not the analytics dashboard. Despite older PostgreSQL documentation,
this app's actual registration and attendance routes use `get_database_path()`
and SQLite. There is no PostgreSQL fallback or separate attendance database.

Configure these environment variables on both sides through a secret manager,
never through Discord commands or committed files:

| Variable | Requirement |
|---|---|
| `DISCORD_ATTENDANCE_ENABLED` | Exact `true` to enable; unset otherwise |
| `DISCORD_ATTENDANCE_PARENT_TOKEN` | Distinct random bearer credential, at least 32 characters |
| `DISCORD_ATTENDANCE_STAFF_TOKEN` | Separate random bearer credential, at least 32 characters |
| `DISCORD_ATTENDANCE_GUILD_ID` | Exact approved Discord guild ID string |
| `DISCORD_ATTENDANCE_STAFF_IDS` | JSON array of operator-approved staff Discord ID strings |
| `DISCORD_ATTENDANCE_SESSIONS` | JSON object mapping session slug to exact stored label and ISO dates |
| `DISCORD_ATTENDANCE_DATABASE_PATH` | Absolute existing registration database path, matching `get_database_path()` exactly; pins the authoritative store |

Nonsecret session example:

```json
{
  "thanksgiving-2026": {
    "label": "Camp Power-Up Thanksgiving 2026 - November 23-24, 2026",
    "dates": ["2026-11-23", "2026-11-24"]
  }
}
```

Camp is November 23-24, 2026, 10am-3pm Central, grades K-8. Writes are allowed
only for today's configured date in `America/Chicago`; there is deliberately
no 10am cutoff so staff can record early arrival or delayed pickup. Reads can
inspect either configured day. An updated session label must be reconciled by
an operator; never rematch registrations by name or email.

On Railway, `RAILWAY_VOLUME_MOUNT_PATH` must be explicitly configured and
exist, and the pinned database must be inside it. Unlike legacy registration
startup, attendance refuses ephemeral fallback, a changed resolved path, or a
missing database. It opens SQLite in existing-file-only mode; it cannot silently
create a replacement registration store.

All bot calls require `Authorization: Bearer <scope credential>`,
`X-Discord-Guild-ID`, and `X-Discord-User-ID`. Kit must derive the latter two
from the authenticated Discord interaction, never message text, an LLM tool
argument, command options, or an end-user HTTP request. These are service
credentials: a bearer holder can assert users in its scope. Keep them out of
client browsers, model context, request logs, and errors; restrict network
access to the service where possible. Staff calls additionally require the
asserted user to be in the backend allowlist. Discord roles may narrow access
further but cannot grant backend access or establish family identity.

Use private DMs or ephemeral interaction responses only, including errors,
pending lists, opaque handles and pickup names. No channel announcements,
public followups, or public fallback on DM failure. Kit must enforce this;
the HTTP backend cannot determine the visibility of a Discord message.

## Operator-approved linkage and pickup roster

There is **no parent self-link endpoint**. An administrator first verifies the
parent using the existing trusted registration/contact process and independently
verifies ownership of the exact Discord account. A Verified Parent role,
matching name/email, knowledge of a registration ID, or a requester's assertion
is insufficient. Record an opaque reference to that private verification;
do not place contact details, verification conversations, or secrets in references.
Manual verification and parent-first restrictions remain in force.

The following administration endpoints require the existing signed-in admin
browser session and `X-CSRF-Token` from that session; bot bearer credentials do
not authorize them. Use the registration service's private authenticated admin
workflow/tooling; no new public administration UI is provided.

`POST /admin/discord-attendance/links`:

```json
{
  "registration_id": 123,
  "session_id": "thanksgiving-2026",
  "discord_user_id": "123456789012345678",
  "active": true,
  "verification_reference": "manual-verification-opaque-reference"
}
```

`registration_id` is the internal integer primary key, obtained by staff in
the private admin workflow, not a parent-supplied claim. The exact active
registration/session must exist. Historical registrations are rejected.
Response: `{"camper_id":"<opaque UUID>","active":true}`. Use the same body
with `active:false` and a revocation reference to revoke a link. A camper may
have multiple individually approved parents; each receives only their links.

`POST /admin/discord-attendance/pickup-roster`:

```json
{
  "camper_id": "<opaque UUID>",
  "session_id": "thanksgiving-2026",
  "active": true,
  "display_name": "Authorized pickup person's name",
  "parent_confirmation_reference": "private-parent-confirmation-reference"
}
```

Response: `{"pickup_id":"<opaque UUID>","active":true}`. An administrator must
obtain authorization directly from the verified parent through the trusted
private process before creating or changing this roster. Emergency contacts
are **not** automatically authorized pickup people. Revocation uses the same
endpoint with `active:false`, `pickup_id`, and no `display_name`. Changes use
revoke + add so old IDs cannot silently refer to a different person. Both
operations are audited. No photo ID is required or collected.

Staff must privately match the person physically collecting the camper to
the current authorized roster and resolve any uncertainty with the verified
parent before release. A Discord request, roster name, role, or button alone
is not permission to release. Never release based only on what the requester
says. `roster_verified:true` is the acting staff member's explicit attestation
of this manual check, not an automated verification result.

## Kit API contract

Prefix: `/api/discord/attendance/v1`. Query strings and JSON use exact session
slug `session_id`, ISO `date`, and opaque `camper_id` returned by approved links.
All JSON responses have `Cache-Control: no-store`; errors never include family
data. Request bodies are explicit bounded JSON objects (4096 bytes maximum).

| Method and suffix | Scope | Input / response |
|---|---|---|
| `GET /campers` | Parent | Query `session_id`; `{"campers":[{"camper_id":"..."}]}` for caller's active links only |
| `GET /status` | Parent | Query `camper_id,session_id,date`; status object below |
| `POST /requests` | Parent | JSON `camper_id,session_id,date,action`; action `arrival` or `pickup`; status object |
| `GET /staff-status` | Staff | Same query and response as `/status`, any camper in configured session |
| `GET /pending` | Staff | Query `session_id,date`; `{"items":[<status objects>]}` for requested arrivals/pickups only |
| `GET /pickup-roster` | Staff | Query `camper_id,session_id`; `{"entries":[{"pickup_id":"...","display_name":"..."}]}` active roster, private staff only |
| `POST /confirmations` | Staff | JSON `camper_id,session_id,date,action,expected_version`; action `arrival` or `release`; release also requires `pickup_id,roster_verified:true`; status object |

Successful attendance status object (HTTP 200):

```json
{
  "camper_id": "<opaque UUID>",
  "session_id": "thanksgiving-2026",
  "date": "2026-11-23",
  "state": "arrival_requested",
  "version": 1,
  "updated_at": "2026-11-23T16:00:00+00:00"
}
```

An unrecorded day has `state:not_arrived`, `version:0`, `updated_at:null`.
No camper names, registration IDs, contact, medical, or other full registration
data are returned. Kit must obtain opaque handles from approved links or
private staff workflows, not guess IDs. If more than one camper is linked,
require an explicit private selection; do not silently choose the first.

Both attendance POST endpoints require `Idempotency-Key` (use Discord
interaction ID, ASCII letters/digits/underscore/hyphen, maximum 128). Preserve
the same body/key for a transport retry. Keys are bound to actor, endpoint and
canonical body. Successful retries return the original result, which may be
older than current state: fetch fresh status before the next confirmation.
Changed body under the same key is rejected. Revoked links/removed staff
cannot retrieve cached results. Different interactions requesting the same
already-requested state are no-ops, not additional attendance events.

Errors: `{"error":{"code":"<code>"}}`:

| HTTP | Code | Meaning |
|---|---|---|
| 400 | `invalid_request` | Invalid/missing/extra fields, unsupported action/date, noncurrent write date, missing idempotency key or roster attestation |
| 401 | `unauthenticated` | Missing/incorrect scoped credential or malformed actor ID |
| 403 | `forbidden` | Wrong guild or staff actor not allowlisted |
| 404 | `not_found` | Unknown session/camper, family mismatch, removed/reassigned registration, or inactive/wrong-camper pickup |
| 409 | `invalid_transition` | Current physical/request state does not allow operation |
| 409 | `stale_version` | Staff must refresh status and re-evaluate, not blindly retry |
| 409 | `idempotency_conflict` | Actor/key reused for different content/operation |
| 503 | `attendance_disabled` | Feature not enabled |
| 503 | `attendance_unavailable` | Missing/invalid configuration, insecure admin signing secret, database unavailable or unsupported schema |

Admin session/CSRF failures retain the existing admin API's error format.
Transport errors have unknown outcome: retry only the same interaction/key/body,
then refresh status; never tell a user arrival/release succeeded without a
confirmed API result. Parent-facing wording must say **requested**, not
checked in/out. Only staff confirmation can report actual arrival or release.

## State and persistence

Normal flow: `not_arrived -> arrival_requested -> present -> pickup_requested
-> released`. Only staff can set `present` or `released`. Staff may confirm
arrival directly from `not_arrived` or release directly from `present`; requests
are a convenience, not a prerequisite for physically present staff. Release
always requires current roster verification. Staff use compare-and-swap
`expected_version` to avoid stale/conflicting confirmations.

Each configured session/registration has an opaque camper handle and each
day has its own versioned state. This initial contract permits one arrival
and release per day. Re-entry, corrections, or reopening a released day are
intentionally not exposed: escalate to camp leadership instead of inventing
an unaudited reversal.

New `discord_*` tables are created lazily after authorization, within one
`BEGIN IMMEDIATE` transaction in the registration database. Schema version 1
is recorded separately; an unknown version fails closed. Setup is repeatable
on existing installations, does not alter registration or legacy attendance
tables, and never backfills old `present` rows as verified arrivals. Schema,
transition, UTC timestamp, acting Discord staff/user ID, audit and deduplication
result commit together or all roll back. SQLite serialization plus expected
versions prevents duplicate concurrent transitions across workers. Database
failures return a generic error and log no payload, token, or family details.

The old `/admin/attendance` page remains a separate present/absent/late roll
call; it is **not** a pickup/release authorization system and does not override
this new physical-state ledger. Operators must use the private new workflow
for Discord arrivals/releases and not present the old page as confirmation.
Back up the complete persistent database (including all `discord_*` tables)
and restrict backups/audit access; roster names and linkage are private data.
Retention/deletion and future schema upgrades require an explicit operator
policy; do not delete audits as a side effect of deleting a registration.

## Synthetic validation

```powershell
python -m pytest scripts\test\test_discord_attendance.py -q
```

Tests create an isolated Flask app and temporary synthetic SQLite database,
without importing the production app's startup database initializer. They cover
disabled/configuration gates, scopes, approved linkage/revocation, cross-family
denials, admin CSRF, explicit staff transitions, current roster checks, per-day
state, Central-time boundaries, replay/content binding, concurrent operations,
atomic rollback, repeatable migration and unchanged legacy attendance.
