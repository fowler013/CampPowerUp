"""Private Discord attendance contract backed by the registration database."""

import hashlib
import json
import os
import re
import secrets
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import jsonify, request


PREFIX = "/api/discord/attendance/v1"
ADMIN_PREFIX = "/admin/discord-attendance"
IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{1,128}\Z")
SNOWFLAKE = re.compile(r"[0-9]{1,20}\Z")
DISCORD_USER_ID = re.compile(r"[0-9]{17,20}\Z")
SCHEMA_VERSION = 1
SCHEMA = (
    """CREATE TABLE IF NOT EXISTS discord_attendance_schema (
        version INTEGER PRIMARY KEY CHECK(version > 0))""",
    """CREATE TABLE IF NOT EXISTS discord_campers (
        camper_id TEXT PRIMARY KEY, registration_id INTEGER NOT NULL,
        session_id TEXT NOT NULL, session_label TEXT NOT NULL,
        UNIQUE(registration_id, session_id))""",
    """CREATE TABLE IF NOT EXISTS discord_parent_links (
        camper_id TEXT NOT NULL REFERENCES discord_campers(camper_id),
        discord_user_id TEXT NOT NULL, active INTEGER NOT NULL CHECK(active IN (0,1)),
        PRIMARY KEY(camper_id, discord_user_id))""",
    """CREATE TABLE IF NOT EXISTS discord_pickup_roster (
        pickup_id TEXT PRIMARY KEY, camper_id TEXT NOT NULL REFERENCES discord_campers(camper_id),
        display_name TEXT NOT NULL, active INTEGER NOT NULL CHECK(active IN (0,1)))""",
    """CREATE TABLE IF NOT EXISTS discord_attendance (
        camper_id TEXT NOT NULL REFERENCES discord_campers(camper_id),
        date TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN
        ('not_arrived','arrival_requested','present','pickup_requested','released')),
        version INTEGER NOT NULL, updated_at TEXT NOT NULL,
        PRIMARY KEY(camper_id,date))""",
    """CREATE TABLE IF NOT EXISTS discord_attendance_audit (
        event_id TEXT PRIMARY KEY, occurred_at TEXT NOT NULL,
        actor_id TEXT NOT NULL, actor_type TEXT NOT NULL,
        camper_id TEXT NOT NULL, date TEXT, action TEXT NOT NULL,
        before_state TEXT, after_state TEXT, details TEXT NOT NULL)""",
    """CREATE TABLE IF NOT EXISTS discord_attendance_idempotency (
        actor_id TEXT NOT NULL, idempotency_key TEXT NOT NULL,
        fingerprint TEXT NOT NULL, response TEXT NOT NULL,
        PRIMARY KEY(actor_id,idempotency_key))""",
)


class AttendanceError(Exception):
    """An expected, privacy-safe API failure."""

    def __init__(self, code: str, status: int):
        super().__init__(code)
        self.code = code
        self.status = status


def fail(code: str, status: int) -> None:
    """Raise a stable API error without including caller data."""
    raise AttendanceError(code, status)


def utc_now() -> datetime:
    """Return an aware time; attendance dates are evaluated in Central time."""
    return datetime.now(timezone.utc)


def settings() -> dict:
    """Read deployment-only credentials without exposing them in Flask config."""
    if os.environ.get("DISCORD_ATTENDANCE_ENABLED") != "true":
        fail("attendance_disabled", 503)
    try:
        result = {
            "parent": os.environ["DISCORD_ATTENDANCE_PARENT_TOKEN"],
            "staff": os.environ["DISCORD_ATTENDANCE_STAFF_TOKEN"],
            "guild": os.environ["DISCORD_ATTENDANCE_GUILD_ID"],
            "staff_ids": json.loads(os.environ["DISCORD_ATTENDANCE_STAFF_IDS"]),
            "sessions": json.loads(os.environ["DISCORD_ATTENDANCE_SESSIONS"]),
            "database_path": os.environ["DISCORD_ATTENDANCE_DATABASE_PATH"],
        }
        if (len(result["parent"]) < 32 or len(result["staff"]) < 32
                or result["parent"] == result["staff"]
                or not SNOWFLAKE.fullmatch(result["guild"])
                or not isinstance(result["staff_ids"], list)
                or not result["staff_ids"]
                or any(not isinstance(value, str) or not SNOWFLAKE.fullmatch(value)
                       for value in result["staff_ids"])
                or not isinstance(result["sessions"], dict) or not result["sessions"]):
            raise ValueError("Invalid attendance configuration")
        if not Path(result["database_path"]).is_absolute():
            raise ValueError("Attendance requires an explicitly pinned database")
        for key, value in result["sessions"].items():
            if (not IDENTIFIER.fullmatch(key) or not isinstance(value, dict)
                    or not isinstance(value.get("label"), str) or not value["label"]
                    or not isinstance(value.get("dates"), list) or not value["dates"]):
                raise ValueError("Invalid attendance session")
            for day in value["dates"]:
                if datetime.strptime(day, "%Y-%m-%d").strftime("%Y-%m-%d") != day:
                    raise ValueError("Invalid attendance date")
        return result
    except (KeyError, ValueError, TypeError):
        fail("attendance_unavailable", 503)


@contextmanager
def transaction(path: str):
    """Serialize writes, schema upgrades, audit and deduplication in one commit."""
    connection = sqlite3.connect(Path(path).resolve().as_uri() + "?mode=rw", uri=True, timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("SELECT id,submission_id,camp_session FROM registrations LIMIT 0")
        # Do not touch legacy attendance or infer physical state from it.
        for statement in SCHEMA:
            connection.execute(statement)
        versions = connection.execute("SELECT version FROM discord_attendance_schema").fetchall()
        if versions and [row["version"] for row in versions] != [SCHEMA_VERSION]:
            fail("attendance_unavailable", 503)
        connection.execute("INSERT OR IGNORE INTO discord_attendance_schema VALUES (?)",
                           (SCHEMA_VERSION,))
        yield connection
        connection.commit()
    except BaseException:
        connection.rollback()
        raise
    finally:
        connection.close()


def body(required: set, optional: set = frozenset()) -> dict:
    """Require a bounded, explicit JSON object rather than permissive coercion."""
    if request.content_length is None or request.content_length > 4096:
        fail("invalid_request", 400)
    value = request.get_json(silent=True)
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - required - optional:
        fail("invalid_request", 400)
    return value


def text(value, pattern=IDENTIFIER) -> str:
    """Validate an opaque identifier."""
    if not isinstance(value, str) or not pattern.fullmatch(value):
        fail("invalid_request", 400)
    return value


def scope(config: dict, data: dict, write: bool = False) -> tuple:
    """Resolve an exact configured session and date, never a caller-supplied label."""
    session_id = text(data.get("session_id"))
    offered = config["sessions"].get(session_id)
    if offered is None:
        fail("not_found", 404)
    day = data.get("date")
    if not isinstance(day, str) or day not in offered["dates"]:
        fail("invalid_request", 400)
    if write and day != utc_now().astimezone(ZoneInfo("America/Chicago")).date().isoformat():
        fail("invalid_request", 400)
    return session_id, day


def camper(connection, config: dict, camper_id, session_id: str, actor: str = None):
    """Check current registration/session and, for parents, the approved link."""
    camper_id = text(camper_id)
    row = connection.execute("""
        SELECT c.* FROM discord_campers c JOIN registrations r ON r.id=c.registration_id
        WHERE c.camper_id=? AND c.session_id=? AND c.session_label=?
        AND r.camp_session=c.session_label AND r.submission_id NOT GLOB 'HIST_*'
        """, (camper_id, session_id, config["sessions"][session_id]["label"])).fetchone()
    if row is None:
        fail("not_found", 404)
    if actor is not None and not connection.execute("""
        SELECT 1 FROM discord_parent_links WHERE camper_id=? AND discord_user_id=? AND active=1
        """, (camper_id, actor)).fetchone():
        fail("not_found", 404)
    return row


def status(connection, camper_id: str, session_id: str, day: str) -> dict:
    """Return only the opaque camper handle and attendance state."""
    row = connection.execute("SELECT * FROM discord_attendance WHERE camper_id=? AND date=?",
                             (camper_id, day)).fetchone()
    return {
        "camper_id": camper_id, "session_id": session_id, "date": day,
        "state": row["state"] if row else "not_arrived",
        "version": row["version"] if row else 0,
        "updated_at": row["updated_at"] if row else None,
    }


def audit(connection, actor: str, actor_type: str, camper_id: str, action: str,
          details: dict, day: str = None, before: str = None, after: str = None) -> None:
    """Record successful mutations atomically; do not log family details."""
    connection.execute("""INSERT INTO discord_attendance_audit VALUES (?,?,?,?,?,?,?,?,?,?)""",
                       (str(uuid.uuid4()), utc_now().isoformat(), actor, actor_type, camper_id,
                        day, action, before, after, json.dumps(details, sort_keys=True)))


def register_discord_attendance(app, database_path, admin_auth, admin_csrf, admin_actor) -> None:
    """Install routes without opening a database or enabling the integration."""

    def guarded(staff=False, admin=False):
        def decorate(function):
            @wraps(function)
            def wrapped(*args, **kwargs):
                try:
                    config = settings()
                    if admin and (not app.secret_key or len(app.secret_key) < 32):
                        fail("attendance_unavailable", 503)
                    actor = "admin:" + admin_actor() if admin else request.headers.get("X-Discord-User-ID", "")
                    if not admin:
                        if request.headers.get("X-Discord-Guild-ID") != config["guild"]:
                            fail("forbidden", 403)
                        if not SNOWFLAKE.fullmatch(actor):
                            fail("unauthenticated", 401)
                        supplied = request.headers.get("Authorization", "")
                        expected = "Bearer " + config["staff" if staff else "parent"]
                        if not secrets.compare_digest(supplied.encode(), expected.encode()):
                            fail("unauthenticated", 401)
                        if staff and actor not in config["staff_ids"]:
                            fail("forbidden", 403)
                    pinned = Path(config["database_path"]).resolve()
                    if os.environ.get("RAILWAY_ENVIRONMENT"):
                        mount = os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
                        if not mount or not Path(mount).is_dir() or not pinned.is_relative_to(Path(mount).resolve()):
                            fail("attendance_unavailable", 503)
                    resolved = Path(database_path()).resolve()
                    if resolved != pinned:
                        fail("attendance_unavailable", 503)
                    with transaction(str(resolved)) as connection:
                        return function(connection, config, actor, *args, **kwargs)
                except AttendanceError as error:
                    if error.status >= 500:
                        app.logger.error("Discord attendance unavailable: %s", error.code)
                    return jsonify(error={"code": error.code}), error.status
                except (sqlite3.Error, OSError):
                    app.logger.error("Discord attendance database operation failed")
                    return jsonify(error={"code": "attendance_unavailable"}), 503
            return wrapped
        return decorate

    @app.after_request
    def private_attendance_response(response):
        if request.path.startswith((PREFIX, ADMIN_PREFIX)):
            response.headers["Cache-Control"] = "no-store"
            response.headers["Pragma"] = "no-cache"
        return response

    @app.get(PREFIX + "/campers")
    @guarded()
    def linked_campers(connection, config, actor):
        session_id = text(request.args.get("session_id"))
        if session_id not in config["sessions"]:
            fail("not_found", 404)
        rows = connection.execute("""
            SELECT c.camper_id FROM discord_campers c
            JOIN discord_parent_links l ON l.camper_id=c.camper_id
            JOIN registrations r ON r.id=c.registration_id
            WHERE l.discord_user_id=? AND l.active=1 AND c.session_id=?
            AND c.session_label=? AND r.camp_session=c.session_label
            AND r.submission_id NOT GLOB 'HIST_*' ORDER BY c.camper_id
            """, (actor, session_id, config["sessions"][session_id]["label"])).fetchall()
        return jsonify(campers=[{"camper_id": row["camper_id"]} for row in rows])

    @app.get(PREFIX + "/status")
    @guarded()
    def own_status(connection, config, actor):
        session_id, day = scope(config, request.args)
        row = camper(connection, config, request.args.get("camper_id"), session_id, actor)
        return jsonify(status(connection, row["camper_id"], session_id, day))

    @app.get(PREFIX + "/staff-status")
    @guarded(staff=True)
    def staff_status(connection, config, actor):
        session_id, day = scope(config, request.args)
        row = camper(connection, config, request.args.get("camper_id"), session_id)
        return jsonify(status(connection, row["camper_id"], session_id, day))

    def mutate(connection, config, actor, staff):
        required = {"camper_id", "session_id", "date", "action"}
        if staff:
            required.add("expected_version")
        data = body(required, {"pickup_id", "roster_verified"} if staff else set())
        session_id, day = scope(config, data, write=True)
        row = camper(connection, config, data["camper_id"], session_id, None if staff else actor)
        camper_id = row["camper_id"]
        key = text(request.headers.get("Idempotency-Key"))
        fingerprint = hashlib.sha256(json.dumps(
            {"operation": "confirmation" if staff else "request", "body": data},
            sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        prior = connection.execute("""SELECT * FROM discord_attendance_idempotency
            WHERE actor_id=? AND idempotency_key=?""", (actor, key)).fetchone()
        if prior:
            if prior["fingerprint"] != fingerprint:
                fail("idempotency_conflict", 409)
            return jsonify(json.loads(prior["response"]))
        current = status(connection, camper_id, session_id, day)
        action = data["action"]
        if not isinstance(action, str):
            fail("invalid_request", 400)
        if staff:
            if type(data["expected_version"]) is not int or data["expected_version"] < 0:
                fail("invalid_request", 400)
            if data["expected_version"] != current["version"]:
                fail("stale_version", 409)
            transitions = {"arrival": ({"not_arrived", "arrival_requested"}, "present"),
                           "release": ({"present", "pickup_requested"}, "released")}
        else:
            transitions = {"arrival": ({"not_arrived"}, "arrival_requested"),
                           "pickup": ({"present"}, "pickup_requested")}
        if action not in transitions:
            fail("invalid_request", 400)
        allowed, target = transitions[action]
        # A second parent interaction is a no-op, not a second attendance event.
        duplicate = not staff and current["state"] == target
        if not duplicate and current["state"] not in allowed:
            fail("invalid_transition", 409)
        details = {}
        if staff and action == "release":
            pickup_id = text(data.get("pickup_id"))
            if data.get("roster_verified") is not True:
                fail("invalid_request", 400)
            if not connection.execute("""SELECT 1 FROM discord_pickup_roster
                WHERE pickup_id=? AND camper_id=? AND active=1""", (pickup_id, camper_id)).fetchone():
                fail("not_found", 404)
            details["pickup_id"] = pickup_id
            details["roster_verified"] = True
        elif "pickup_id" in data or "roster_verified" in data:
            fail("invalid_request", 400)
        if not duplicate:
            connection.execute("""INSERT INTO discord_attendance VALUES (?,?,?,?,?)
                ON CONFLICT(camper_id,date) DO UPDATE SET state=excluded.state,
                version=excluded.version,updated_at=excluded.updated_at""",
                               (camper_id, day, target, current["version"] + 1, utc_now().isoformat()))
            audit(connection, actor, "staff" if staff else "parent", camper_id, action, details,
                  day, current["state"], target)
        result = status(connection, camper_id, session_id, day)
        connection.execute("INSERT INTO discord_attendance_idempotency VALUES (?,?,?,?)",
                           (actor, key, fingerprint, json.dumps(result, sort_keys=True)))
        return jsonify(result)

    @app.post(PREFIX + "/requests")
    @guarded()
    def parent_request(connection, config, actor):
        return mutate(connection, config, actor, False)

    @app.post(PREFIX + "/confirmations")
    @guarded(staff=True)
    def staff_confirmation(connection, config, actor):
        return mutate(connection, config, actor, True)

    @app.get(PREFIX + "/pending")
    @guarded(staff=True)
    def pending(connection, config, actor):
        session_id, day = scope(config, request.args)
        rows = connection.execute("""
            SELECT a.camper_id FROM discord_attendance a
            JOIN discord_campers c ON c.camper_id=a.camper_id
            JOIN registrations r ON r.id=c.registration_id
            WHERE a.date=? AND a.state IN ('arrival_requested','pickup_requested')
            AND c.session_id=? AND c.session_label=? AND r.camp_session=c.session_label
            AND r.submission_id NOT GLOB 'HIST_*' ORDER BY a.updated_at,a.camper_id
            """, (day, session_id, config["sessions"][session_id]["label"])).fetchall()
        return jsonify(items=[status(connection, row["camper_id"], session_id, day) for row in rows])

    @app.get(PREFIX + "/pickup-roster")
    @guarded(staff=True)
    def pickup_roster(connection, config, actor):
        session_id = text(request.args.get("session_id"))
        if session_id not in config["sessions"]:
            fail("not_found", 404)
        row = camper(connection, config, request.args.get("camper_id"), session_id)
        rows = connection.execute("""SELECT pickup_id,display_name FROM discord_pickup_roster
            WHERE camper_id=? AND active=1 ORDER BY pickup_id""", (row["camper_id"],)).fetchall()
        return jsonify(entries=[dict(entry) for entry in rows])

    @app.get(ADMIN_PREFIX + "/roster")
    @admin_auth
    @guarded(admin=True)
    def admin_roster(connection, config, actor):
        sessions = []
        for session_id, session_config in config["sessions"].items():
            registrations = connection.execute("""
                SELECT r.id, r.submission_id, r.child_first_name, r.child_last_name,
                       c.camper_id
                FROM registrations r
                LEFT JOIN discord_campers c
                    ON c.registration_id=r.id AND c.session_id=? AND c.session_label=?
                WHERE r.camp_session=? AND r.submission_id NOT GLOB 'HIST_*'
                ORDER BY r.child_first_name, r.child_last_name, r.id
                """, (session_id, session_config["label"], session_config["label"])).fetchall()
            items = []
            for registration in registrations:
                links = []
                pickups = []
                if registration["camper_id"]:
                    links = [dict(row) for row in connection.execute("""
                        SELECT discord_user_id, active FROM discord_parent_links
                        WHERE camper_id=? ORDER BY discord_user_id
                        """, (registration["camper_id"],)).fetchall()]
                    pickups = [dict(row) for row in connection.execute("""
                        SELECT pickup_id, display_name FROM discord_pickup_roster
                        WHERE camper_id=? AND active=1 ORDER BY display_name, pickup_id
                        """, (registration["camper_id"],)).fetchall()]
                last_name = registration["child_last_name"] or ""
                items.append({
                    "registration_id": registration["id"],
                    "camper_id": registration["camper_id"],
                    "submission_id": registration["submission_id"],
                    "child_first_name": registration["child_first_name"] or "",
                    "child_last_initial": last_name[:1],
                    "links": links,
                    "pickups": pickups,
                })
            sessions.append({
                "session_id": session_id,
                "label": session_config["label"],
                "registrations": items,
            })
        return jsonify(sessions=sessions)

    @app.post(ADMIN_PREFIX + "/links")
    @admin_auth
    @admin_csrf
    @guarded(admin=True)
    def approve_link(connection, config, actor):
        data = body({"registration_id", "session_id", "discord_user_id", "active", "verification_reference"})
        session_id = text(data["session_id"])
        user_id = text(data["discord_user_id"], DISCORD_USER_ID)
        reference = text(data["verification_reference"])
        if (session_id not in config["sessions"] or type(data["registration_id"]) is not int
                or type(data["active"]) is not bool):
            fail("invalid_request", 400)
        label = config["sessions"][session_id]["label"]
        if not connection.execute("""SELECT 1 FROM registrations WHERE id=? AND camp_session=?
            AND submission_id NOT GLOB 'HIST_*'""", (data["registration_id"], label)).fetchone():
            fail("not_found", 404)
        connection.execute("""INSERT INTO discord_campers VALUES (?,?,?,?)
            ON CONFLICT(registration_id,session_id) DO NOTHING""",
                           (str(uuid.uuid4()), data["registration_id"], session_id, label))
        row = connection.execute("""SELECT * FROM discord_campers
            WHERE registration_id=? AND session_id=?""", (data["registration_id"], session_id)).fetchone()
        if row["session_label"] != label:
            fail("not_found", 404)
        connection.execute("""INSERT INTO discord_parent_links VALUES (?,?,?)
            ON CONFLICT(camper_id,discord_user_id) DO UPDATE SET active=excluded.active""",
                           (row["camper_id"], user_id, int(data["active"])))
        audit(connection, actor, "admin", row["camper_id"], "link_approved" if data["active"] else "link_revoked",
              {"discord_user_id": user_id, "verification_reference": reference})
        return jsonify(camper_id=row["camper_id"], active=data["active"])

    @app.post(ADMIN_PREFIX + "/pickup-roster")
    @admin_auth
    @admin_csrf
    @guarded(admin=True)
    def maintain_roster(connection, config, actor):
        data = body({"camper_id", "session_id", "parent_confirmation_reference", "active"},
                    {"pickup_id", "display_name"})
        session_id = text(data["session_id"])
        if session_id not in config["sessions"] or type(data["active"]) is not bool:
            fail("invalid_request", 400)
        row = camper(connection, config, data["camper_id"], session_id)
        reference = text(data["parent_confirmation_reference"])
        if data["active"]:
            name = data.get("display_name")
            if (not isinstance(name, str) or not 1 <= len(name.strip()) <= 100
                    or any(ord(char) < 32 for char in name) or "pickup_id" in data):
                fail("invalid_request", 400)
            pickup_id = str(uuid.uuid4())
            connection.execute("INSERT INTO discord_pickup_roster VALUES (?,?,?,1)",
                               (pickup_id, row["camper_id"], name.strip()))
        else:
            pickup_id = text(data.get("pickup_id"))
            if "display_name" in data:
                fail("invalid_request", 400)
            changed = connection.execute("""UPDATE discord_pickup_roster SET active=0
                WHERE pickup_id=? AND camper_id=? AND active=1""", (pickup_id, row["camper_id"]))
            if changed.rowcount != 1:
                fail("not_found", 404)
        audit(connection, actor, "admin", row["camper_id"], "pickup_added" if data["active"] else "pickup_revoked",
              {"pickup_id": pickup_id, "parent_confirmation_reference": reference})
        return jsonify(pickup_id=pickup_id, active=data["active"])
