"""Registration summaries and persistent camp configuration."""

from collections import Counter
from contextlib import closing
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import re
import sqlite3


BOOLEAN_FIELDS = (
    "is_returning_camper",
    "bringing_own_switch",
    "has_allergies",
    "has_medical_conditions",
)


def is_checked(value):
    """Interpret the boolean representations used by forms and older imports."""
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def normalize_registration(registration):
    """Return a display copy without changing the stored registration."""
    result = dict(registration)
    for field in BOOLEAN_FIELDS:
        result[field] = is_checked(result.get(field))
    result["payment_status"] = str(result.get("payment_status") or "pending").strip().lower()
    return result


def registration_identity_error(values):
    """Validate the required identity fields shared by registration and editing."""
    for field in ("child_first_name", "child_last_name"):
        if not isinstance(values.get(field), str) or not values[field].strip():
            return "The camper's first and last names are required."
    email = values.get("parent_email")
    if not isinstance(email, str) or not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email.strip()):
        return "Enter a valid parent or guardian email address."
    age = str(values.get("child_age"))
    if not age.isascii() or not age.isdigit() or not 5 <= int(age) <= 18:
        return "Camper age must be a whole number between 5 and 18."
    return None


def registration_summary(registrations, now=None):
    """Summarize a selected set of registrations; SQLite timestamps are UTC."""
    now = now or datetime.now(timezone.utc)
    dates = []
    invalid_dates = 0
    ages = Counter()
    for registration in registrations:
        timestamp = registration.get("timestamp")
        try:
            date = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            dates.append(date.replace(tzinfo=timezone.utc) if date.tzinfo is None else date.astimezone(timezone.utc))
        except (ValueError, TypeError):
            invalid_dates += 1
        try:
            age = int(registration.get("child_age"))
            if age < 5:
                group = "Under 5"
            elif age <= 6:
                group = "5-6 years"
            elif age <= 8:
                group = "7-8 years"
            elif age <= 10:
                group = "9-10 years"
            elif age <= 12:
                group = "11-12 years"
            else:
                group = "13+ years"
        except (TypeError, ValueError):
            group = "Unknown"
        ages[group] += 1
    paid = sum(r["payment_status"] == "paid" for r in registrations)
    returning = sum(r["is_returning_camper"] for r in registrations)
    return {
        "total_registrations": len(registrations),
        "todays_count": sum(date.date() == now.date() for date in dates),
        "weeks_count": sum(now - timedelta(days=7) <= date <= now for date in dates),
        "returning_campers": returning,
        "new_campers": len(registrations) - returning,
        "bringing_switch": sum(r["bringing_own_switch"] for r in registrations),
        "has_allergies": sum(r["has_allergies"] for r in registrations),
        "has_medical_conditions": sum(r["has_medical_conditions"] for r in registrations),
        "paid_count": paid,
        "pending_payment": len(registrations) - paid,
        "last_registration": max(dates).date().isoformat() if dates else None,
        "invalid_dates": invalid_dates,
        "age_groups": dict(ages),
    }


def configuration_revision(config):
    """Identify the configuration a form was opened with."""
    content = json.dumps(config, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def validate_configuration_update(current, values):
    """Validate the editor's supported fields before changing stored settings."""
    if not isinstance(values, dict):
        raise ValueError("Configuration must be a JSON object.")
    result = deepcopy(current)
    for field in ("camp_name", "camp_subtitle", "camp_dates", "daily_hours", "final_payment_due"):
        value = values.get(field)
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 200:
            raise ValueError(f"{field.replace('_', ' ').title()} is required and must be at most 200 characters.")
        result[field] = value.strip()

    def integer(field, minimum, maximum):
        value = values.get(field)
        if isinstance(value, bool) or not str(value).isdigit():
            raise ValueError(f"{field.replace('_', ' ').title()} must be a whole number.")
        number = int(value)
        if not minimum <= number <= maximum:
            raise ValueError(f"{field.replace('_', ' ').title()} must be between {minimum} and {maximum}.")
        return number

    result["camp_days"] = integer("camp_days", 1, 10)
    for prefix, camper_type in (("returning", "returning_camper"), ("new", "new_camper")):
        deposit = integer(f"{prefix}_deposit", 0, 10000)
        final = integer(f"{prefix}_final", 0, 10000)
        result["pricing"][camper_type] = {
            "deposit": deposit,
            "final_payment": final,
            "total": deposit + final,
        }
    return result


def load_configurations(db_file):
    """Read saved settings; an older database without this table uses code defaults."""
    if not os.path.exists(db_file):
        return {}, {}
    with closing(sqlite3.connect(db_file)) as connection:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'camp_configurations'"
        ).fetchone()
        if not exists:
            return {}, {}
        rows = connection.execute(
            "SELECT session_id, camp_session, configuration, active FROM camp_configurations"
        ).fetchall()
    active = {}
    by_label = {}
    for session_id, label, configuration, is_active in rows:
        config = json.loads(configuration)
        if not isinstance(config, dict) or not isinstance(config.get("pricing"), dict):
            raise ValueError("Saved camp configuration is invalid.")
        by_label[label] = config
        if is_active:
            active[session_id] = config
    return active, by_label


class ConfigurationConflict(ValueError):
    """Another administrator saved settings after this editor was opened."""


def save_configuration(db_file, session_id, current, updated, expected_revision):
    """Atomically save settings and retain configurations for previous session labels."""
    def label(config):
        return f"{config['camp_name']} - {config['camp_dates']}"

    with closing(sqlite3.connect(db_file)) as connection:
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS camp_configurations (
                    session_id TEXT NOT NULL,
                    camp_session TEXT NOT NULL,
                    configuration TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (session_id, camp_session)
                )
            """)
            connection.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS active_camp_configuration
                ON camp_configurations(session_id) WHERE active = 1
            """)
            saved = connection.execute(
                "SELECT configuration FROM camp_configurations WHERE session_id = ? AND active = 1",
                (session_id,),
            ).fetchone()
            latest = json.loads(saved[0]) if saved else current
            if configuration_revision(latest) != expected_revision:
                raise ConfigurationConflict("Settings changed in another session. Reload before saving again.")
            if label(updated) != label(latest):
                existing = connection.execute(
                    "SELECT 1 FROM registrations WHERE camp_session = ? LIMIT 1", (label(updated),)
                ).fetchone()
                if existing:
                    raise ValueError("That session label already has registrations. Choose a distinct label; existing sessions cannot be merged here.")
            connection.execute("""
                INSERT OR IGNORE INTO camp_configurations
                    (session_id, camp_session, configuration, active) VALUES (?, ?, ?, 0)
            """, (session_id, label(latest), json.dumps(latest)))
            connection.execute(
                "UPDATE camp_configurations SET active = 0 WHERE session_id = ?", (session_id,)
            )
            connection.execute("""
                INSERT INTO camp_configurations (session_id, camp_session, configuration, active)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(session_id, camp_session)
                DO UPDATE SET configuration = excluded.configuration, active = 1
            """, (session_id, label(updated), json.dumps(updated)))
