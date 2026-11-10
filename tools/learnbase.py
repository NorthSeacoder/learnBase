#!/usr/bin/env python3
"""Small offline CLI for a learnBase workspace."""

from __future__ import annotations

import argparse
import hashlib
import html
import http.client
import json
import os
import re
import sqlite3
import sys
import tempfile
import unicodedata
from datetime import date, datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


DATABASE_SCHEMA_VERSION = 4
DEFAULT_WORKSPACE_NAME = "My Learning Base"
PROPOSAL_VERSION = 1
CARD_PROPOSAL_VERSION = 1
TOPIC_ID_PATTERN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
CARD_ID_PATTERN = re.compile(r"CARD-\d{4,}")
CARD_SECTION_PATTERN = re.compile(r"(?ms)^## Front\n(.*?)\n## Back\n(.*)\Z")
ANKI_CONNECT_HOST = "127.0.0.1"
ANKI_CONNECT_PORT = 8765
ANKI_CONNECT_TIMEOUT_SECONDS = 2
ANKI_CONNECT_MAX_RESPONSE_BYTES = 2 * 1024 * 1024
ANKI_READ_ACTIONS = frozenset({"deckNames", "modelNames", "modelFieldNames", "findNotes", "notesInfo"})
ACTIVITY_TYPES = ("question_attempt", "recall_practice", "reading_observation", "practice_reflection")
EVIDENCE_TYPES = ("learner_statement", "observed_artifact", "verified_outcome")
EVIDENCE_STATUSES = ("unknown", "pending", "confirmed", "conflicting", "superseded")
EVIDENCE_DIRECTIONS = ("supports", "contradicts", "observes")
LEARNER_INPUT_FIELDS = {
    "question_attempt": ("prompt", "learner_response", "confidence", "approach", "duration_seconds"),
    "recall_practice": ("prompt", "recall", "confidence", "approach", "duration_seconds"),
    "reading_observation": ("observation", "reflection"),
    "practice_reflection": ("task", "action", "reflection", "learner_observed_outcome"),
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS topics (
    topic_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    parent_id TEXT REFERENCES topics(topic_id),
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS topic_config (
    topic_id TEXT PRIMARY KEY REFERENCES topics(topic_id),
    config_version INTEGER NOT NULL CHECK (config_version = 1),
    learning_goal TEXT,
    prior_background TEXT,
    constraints_json TEXT,
    source_hints_json TEXT,
    progress_signals_json TEXT,
    approved_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL CHECK (kind IN ('pdf', 'web')),
    title TEXT NOT NULL,
    locator TEXT NOT NULL,
    source_mode TEXT NOT NULL CHECK (source_mode IN ('workspace', 'external-readonly')),
    sha256 TEXT,
    byte_size INTEGER,
    created_at TEXT NOT NULL,
    UNIQUE (kind, locator)
);
CREATE TABLE IF NOT EXISTS source_topics (
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    topic_id TEXT NOT NULL REFERENCES topics(topic_id),
    PRIMARY KEY (source_id, topic_id)
);
CREATE TABLE IF NOT EXISTS notes (
    note_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS note_topics (
    note_id TEXT NOT NULL REFERENCES notes(note_id),
    topic_id TEXT NOT NULL REFERENCES topics(topic_id),
    PRIMARY KEY (note_id, topic_id)
);
CREATE TABLE IF NOT EXISTS note_sources (
    note_id TEXT NOT NULL REFERENCES notes(note_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    locator TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (note_id, source_id)
);
CREATE TABLE IF NOT EXISTS learning_activities (
    activity_id TEXT PRIMARY KEY,
    idempotency_key TEXT NOT NULL UNIQUE,
    payload_sha256 TEXT NOT NULL CHECK (length(payload_sha256) = 64),
    topic_id TEXT NOT NULL REFERENCES topics(topic_id),
    activity_type TEXT NOT NULL CHECK (activity_type IN ('question_attempt', 'recall_practice', 'reading_observation', 'practice_reflection')),
    occurred_at TEXT,
    learner_input_json TEXT NOT NULL,
    assistant_analysis TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (activity_id, topic_id)
);
CREATE TABLE IF NOT EXISTS learning_evidence (
    evidence_id TEXT PRIMARY KEY,
    activity_id TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    evidence_type TEXT NOT NULL CHECK (evidence_type IN ('learner_statement', 'observed_artifact', 'verified_outcome')),
    statement TEXT NOT NULL CHECK (length(statement) > 0),
    status TEXT NOT NULL CHECK (status IN ('unknown', 'pending', 'confirmed', 'conflicting', 'superseded')),
    created_at TEXT NOT NULL,
    FOREIGN KEY (activity_id, topic_id) REFERENCES learning_activities(activity_id, topic_id),
    UNIQUE (evidence_id, topic_id)
);
CREATE TABLE IF NOT EXISTS topic_profile_dimensions (
    topic_id TEXT NOT NULL REFERENCES topics(topic_id),
    dimension_id TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    eligible_activity_types_json TEXT NOT NULL,
    eligible_evidence_types_json TEXT NOT NULL,
    minimum_evidence_count INTEGER NOT NULL CHECK (minimum_evidence_count > 0),
    recency_days INTEGER NOT NULL CHECK (recency_days > 0),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (topic_id, dimension_id)
);
CREATE TABLE IF NOT EXISTS evidence_dimensions (
    evidence_id TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    dimension_id TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('supports', 'contradicts', 'observes')),
    PRIMARY KEY (evidence_id, dimension_id),
    FOREIGN KEY (evidence_id, topic_id) REFERENCES learning_evidence(evidence_id, topic_id),
    FOREIGN KEY (topic_id, dimension_id) REFERENCES topic_profile_dimensions(topic_id, dimension_id)
);
CREATE TABLE IF NOT EXISTS evidence_sources (
    evidence_id TEXT NOT NULL REFERENCES learning_evidence(evidence_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    locator TEXT,
    PRIMARY KEY (evidence_id, source_id)
);
CREATE TABLE IF NOT EXISTS evidence_notes (
    evidence_id TEXT NOT NULL REFERENCES learning_evidence(evidence_id),
    note_id TEXT NOT NULL REFERENCES notes(note_id),
    PRIMARY KEY (evidence_id, note_id)
);
CREATE TABLE IF NOT EXISTS evidence_status_history (
    history_id TEXT PRIMARY KEY,
    evidence_id TEXT NOT NULL REFERENCES learning_evidence(evidence_id),
    from_status TEXT CHECK (from_status IS NULL OR from_status IN ('unknown', 'pending', 'confirmed', 'conflicting')),
    to_status TEXT NOT NULL CHECK (to_status IN ('unknown', 'pending', 'confirmed', 'conflicting', 'superseded')),
    changed_at TEXT NOT NULL,
    approved_at TEXT NOT NULL,
    reason TEXT NOT NULL CHECK (length(reason) > 0)
);
CREATE TABLE IF NOT EXISTS cards (
    card_id TEXT PRIMARY KEY,
    topic_id TEXT NOT NULL REFERENCES topics(topic_id),
    objective_key TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (card_id, topic_id),
    UNIQUE (topic_id, objective_key)
);
CREATE TABLE IF NOT EXISTS card_notes (
    card_id TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    note_id TEXT NOT NULL,
    PRIMARY KEY (card_id, note_id),
    FOREIGN KEY (card_id, topic_id) REFERENCES cards(card_id, topic_id),
    FOREIGN KEY (note_id, topic_id) REFERENCES note_topics(note_id, topic_id)
);
CREATE TABLE IF NOT EXISTS card_evidence (
    card_id TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    evidence_id TEXT NOT NULL,
    PRIMARY KEY (card_id, evidence_id),
    FOREIGN KEY (card_id, topic_id) REFERENCES cards(card_id, topic_id),
    FOREIGN KEY (evidence_id, topic_id) REFERENCES learning_evidence(evidence_id, topic_id)
);
CREATE TABLE IF NOT EXISTS card_sources (
    card_id TEXT NOT NULL REFERENCES cards(card_id),
    source_id TEXT NOT NULL REFERENCES sources(source_id),
    locator TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (card_id, source_id, locator)
);
CREATE TABLE IF NOT EXISTS topic_anki_decks (
    topic_id TEXT NOT NULL REFERENCES topics(topic_id),
    deck_name TEXT NOT NULL CHECK (length(deck_name) > 0),
    created_at TEXT NOT NULL,
    PRIMARY KEY (topic_id, deck_name)
);
CREATE INDEX IF NOT EXISTS learning_activities_topic_date ON learning_activities(topic_id, occurred_at);
CREATE INDEX IF NOT EXISTS learning_evidence_topic_status ON learning_evidence(topic_id, status);
CREATE INDEX IF NOT EXISTS evidence_dimensions_topic_dimension ON evidence_dimensions(topic_id, dimension_id);
CREATE INDEX IF NOT EXISTS cards_topic_updated ON cards(topic_id, updated_at);
CREATE TRIGGER IF NOT EXISTS evidence_status_history_no_update
BEFORE UPDATE ON evidence_status_history
BEGIN
    SELECT RAISE(ABORT, 'evidence status history is append-only');
END;
CREATE TRIGGER IF NOT EXISTS evidence_status_history_no_delete
BEFORE DELETE ON evidence_status_history
BEGIN
    SELECT RAISE(ABORT, 'evidence status history is append-only');
END;
"""


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def connect(root: Path) -> sqlite3.Connection:
    db_path = root / "data" / "learnbase.sqlite3"
    if not db_path.exists():
        raise ValueError("workspace is not initialized; run `python3 tools/learnbase.py setup` first")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def setup_workspace(root: Path, name: str | None = None) -> None:
    if name is not None:
        name = name.strip()
        if not name or len(name) > 160:
            raise ValueError("workspace name must contain 1 to 160 characters")
    for directory in ("01-sources", "02-notes", "03-reviews", "04-cards/drafts", "reports", "data"):
        (root / directory).mkdir(parents=True, exist_ok=True)
    db_path = root / "data" / "learnbase.sqlite3"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        metadata_exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'metadata'"
        ).fetchone()
        current_version = 0
        existing_name = None
        if metadata_exists:
            version_row = conn.execute("SELECT value FROM metadata WHERE key = 'schema_version'").fetchone()
            current_version = int(version_row[0]) if version_row else 1
            name_row = conn.execute("SELECT value FROM metadata WHERE key = 'workspace_name'").fetchone()
            existing_name = name_row[0] if name_row else None
        if current_version > DATABASE_SCHEMA_VERSION:
            raise ValueError(
                f"workspace database schema {current_version} is newer than supported schema {DATABASE_SCHEMA_VERSION}"
            )

        conn.executescript("BEGIN;\n" + SCHEMA)
        conn.execute(
            "INSERT INTO metadata(key, value) VALUES ('schema_version', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (str(DATABASE_SCHEMA_VERSION),),
        )
        if name is not None:
            workspace_name = name
        else:
            workspace_name = existing_name or DEFAULT_WORKSPACE_NAME
        conn.execute(
            "INSERT INTO metadata(key, value) VALUES ('workspace_name', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (workspace_name,),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"set up {root.resolve()} ({workspace_name})")


def add_topic(root: Path, slug: str, name: str, parent: str | None) -> None:
    if not TOPIC_ID_PATTERN.fullmatch(slug):
        raise ValueError("topic ID must use lowercase ASCII letters, digits, and hyphens")
    conn = connect(root)
    try:
        conn.execute("INSERT INTO topics(topic_id, name, parent_id, created_at) VALUES (?, ?, ?, ?)", (slug, name, parent, now()))
        conn.commit()
    finally:
        conn.close()
    print(f"created topic {slug}")


def validate_topic_proposal(proposal: object) -> dict[str, object]:
    if not isinstance(proposal, dict):
        raise ValueError("topic proposal must be a JSON object")

    allowed = {
        "proposal_version",
        "topic_id",
        "name",
        "parent_id",
        "learning_goal",
        "prior_background",
        "constraints",
        "source_hints",
        "progress_signals",
    }
    unknown = set(proposal) - allowed
    if unknown:
        raise ValueError(f"unknown topic proposal fields: {', '.join(sorted(unknown))}")
    proposal_version = proposal.get("proposal_version")
    if type(proposal_version) is not int or proposal_version != PROPOSAL_VERSION:
        raise ValueError(f"proposal_version must be {PROPOSAL_VERSION}")

    topic_id = proposal.get("topic_id")
    if not isinstance(topic_id, str) or not TOPIC_ID_PATTERN.fullmatch(topic_id):
        raise ValueError("topic_id must use lowercase ASCII letters, digits, and hyphens")
    name = proposal.get("name")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 160:
        raise ValueError("name must contain 1 to 160 characters")
    name = name.strip()

    parent_id = proposal.get("parent_id")
    if parent_id is not None and (not isinstance(parent_id, str) or not TOPIC_ID_PATTERN.fullmatch(parent_id)):
        raise ValueError("parent_id must be null or a valid topic ID")
    if parent_id == topic_id:
        raise ValueError("a topic cannot be its own parent")

    def optional_text(field: str) -> str | None:
        value = proposal.get(field)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field} must be null or a non-empty string")
        value = value.strip()
        if len(value) > 1000:
            raise ValueError(f"{field} must not exceed 1000 characters")
        return value

    def optional_string_list(field: str) -> list[str] | None:
        value = proposal.get(field)
        if value is None:
            return None
        if not isinstance(value, list) or len(value) > 20:
            raise ValueError(f"{field} must be null or a list of at most 20 strings")
        result = []
        for item in value:
            if not isinstance(item, str) or not item.strip() or len(item.strip()) > 500:
                raise ValueError(f"each {field} item must contain 1 to 500 characters")
            result.append(item.strip())
        return result

    return {
        "topic_id": topic_id,
        "name": name,
        "parent_id": parent_id,
        "learning_goal": optional_text("learning_goal"),
        "prior_background": optional_text("prior_background"),
        "constraints": optional_string_list("constraints"),
        "source_hints": optional_string_list("source_hints"),
        "progress_signals": optional_string_list("progress_signals"),
    }


def save_topic_proposal(root: Path, proposal: object, approved: bool) -> None:
    if not approved:
        raise ValueError("topic proposal was not saved; obtain learner approval before passing --approved")
    values = validate_topic_proposal(proposal)
    conn = connect(root)
    try:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("SELECT 1 FROM topics WHERE topic_id = ?", (values["topic_id"],)).fetchone():
            raise ValueError(f"topic already exists: {values['topic_id']}")
        parent_id = values["parent_id"]
        if parent_id is not None and conn.execute(
            "SELECT 1 FROM topics WHERE topic_id = ?", (parent_id,)
        ).fetchone() is None:
            raise ValueError(f"unknown parent topic: {parent_id}")

        conn.execute(
            "INSERT INTO topics(topic_id, name, parent_id, created_at) VALUES (?, ?, ?, ?)",
            (values["topic_id"], values["name"], parent_id, now()),
        )
        conn.execute(
            """INSERT INTO topic_config(
                   topic_id, config_version, learning_goal, prior_background,
                   constraints_json, source_hints_json, progress_signals_json, approved_at
               ) VALUES (?, 1, ?, ?, ?, ?, ?, ?)""",
            (
                values["topic_id"],
                values["learning_goal"],
                values["prior_background"],
                json.dumps(values["constraints"], ensure_ascii=False) if values["constraints"] is not None else None,
                json.dumps(values["source_hints"], ensure_ascii=False) if values["source_hints"] is not None else None,
                json.dumps(values["progress_signals"], ensure_ascii=False) if values["progress_signals"] is not None else None,
                now(),
            ),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"created approved topic {values['topic_id']}")


def topic_ids(conn: sqlite3.Connection, topics: list[str]) -> list[str]:
    unique = list(dict.fromkeys(topics))
    for topic in unique:
        if conn.execute("SELECT 1 FROM topics WHERE topic_id = ?", (topic,)).fetchone() is None:
            raise ValueError(f"unknown topic: {topic}")
    if not unique:
        raise ValueError("at least one --topic is required")
    return unique


def add_source(root: Path, kind: str, title: str, locator: str, topics: list[str]) -> None:
    conn = connect(root)
    try:
        selected_topics = topic_ids(conn, topics)
        source_mode = "external-readonly"
        digest = None
        byte_size = None
        if kind == "web":
            parsed = urlparse(locator)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError("web source must be an http(s) URL")
        else:
            source_path = Path(locator).expanduser()
            resolved = source_path if source_path.is_absolute() else root / source_path
            if not resolved.is_file():
                raise ValueError(f"PDF path is not a readable file: {locator}")
            resolved = resolved.resolve(strict=True)
            try:
                stored_path = resolved.relative_to(root.resolve()).as_posix()
                source_mode = "workspace"
                locator = stored_path
            except ValueError:
                locator = str(resolved)
            hasher = hashlib.sha256()
            with resolved.open("rb") as source_file:
                for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
                    hasher.update(chunk)
            digest = hasher.hexdigest()
            byte_size = resolved.stat().st_size

        existing = conn.execute("SELECT source_id, sha256 FROM sources WHERE kind = ? AND locator = ?", (kind, locator)).fetchone()
        if existing:
            if existing["sha256"] != digest:
                raise ValueError("source content changed at this location; review it before updating the registered revision")
            source_id = existing["source_id"]
        else:
            row = conn.execute("SELECT COUNT(*) AS count FROM sources").fetchone()
            source_id = f"SRC-{row['count'] + 1:04d}"
            conn.execute(
                "INSERT INTO sources(source_id, kind, title, locator, source_mode, sha256, byte_size, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (source_id, kind, title, locator, source_mode, digest, byte_size, now()),
            )
        conn.executemany("INSERT OR IGNORE INTO source_topics(source_id, topic_id) VALUES (?, ?)", ((source_id, topic) for topic in selected_topics))
        conn.commit()
    finally:
        conn.close()
    print(f"registered {source_id} ({source_mode})")


def next_id(conn: sqlite3.Connection, table: str, prefix: str) -> str:
    count = conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
    return f"{prefix}-{count + 1:04d}"


def _checked_object(value: object, allowed: set[str], required: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    missing = required - set(value)
    unknown = set(value) - allowed
    if missing:
        raise ValueError(f"{label} is missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"unknown {label} fields: {', '.join(sorted(unknown))}")
    return value


def _bounded_text(value: object, field: str, maximum: int = 2000) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > maximum:
        raise ValueError(f"{field} must be null or a non-empty string of at most {maximum} characters")
    return value.strip()


def _parse_utc_timestamp(value: object, field: str) -> tuple[str | None, datetime | None]:
    if value is None:
        return None, None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be null or an ISO-8601 timestamp with timezone")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp with timezone") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a timezone")
    parsed = parsed.astimezone(timezone.utc)
    precision = "microseconds" if parsed.microsecond else "seconds"
    return parsed.isoformat(timespec=precision), parsed


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def validate_review_proposal(proposal: object) -> dict[str, object]:
    values = _checked_object(
        proposal,
        {"proposal_version", "idempotency_key", "topic_id", "activity_type", "occurred_at", "learner_input", "assistant_analysis", "evidence"},
        {"proposal_version", "idempotency_key", "topic_id", "activity_type", "learner_input", "evidence"},
        "review proposal",
    )
    version = values["proposal_version"]
    if type(version) is not int or version != PROPOSAL_VERSION:
        raise ValueError(f"proposal_version must be {PROPOSAL_VERSION}")
    idempotency_key = _bounded_text(values["idempotency_key"], "idempotency_key", 128)
    if idempotency_key is None:
        raise ValueError("idempotency_key is required")
    topic_id = values["topic_id"]
    if not isinstance(topic_id, str) or not TOPIC_ID_PATTERN.fullmatch(topic_id):
        raise ValueError("topic_id must use lowercase ASCII letters, digits, and hyphens")
    activity_type = values["activity_type"]
    if activity_type not in ACTIVITY_TYPES:
        raise ValueError(f"activity_type must be one of: {', '.join(ACTIVITY_TYPES)}")
    occurred_at, _ = _parse_utc_timestamp(values.get("occurred_at"), "occurred_at")

    learner_input = _checked_object(values["learner_input"], set(LEARNER_INPUT_FIELDS[activity_type]), set(), "learner_input")
    normalized_input: dict[str, object] = {}
    for field in LEARNER_INPUT_FIELDS[activity_type]:
        item = learner_input.get(field)
        if field in ("confidence",):
            if item is not None and (type(item) not in (int, float) or not 0 <= item <= 1):
                raise ValueError("confidence must be null or a learner-reported number from 0 to 1")
            normalized_input[field] = None if item is None else float(item)
        elif field == "duration_seconds":
            if item is not None and (type(item) is not int or not 0 <= item <= 86400):
                raise ValueError("duration_seconds must be null or an integer from 0 to 86400")
            normalized_input[field] = item
        else:
            normalized_input[field] = _bounded_text(item, f"learner_input.{field}")

    assistant_analysis = _bounded_text(values.get("assistant_analysis"), "assistant_analysis", 4000)
    evidence_input = values["evidence"]
    if not isinstance(evidence_input, list) or len(evidence_input) > 50:
        raise ValueError("evidence must be a list of at most 50 reviewed evidence items")
    evidence: list[dict[str, object]] = []
    for index, raw in enumerate(evidence_input):
        label = f"evidence[{index}]"
        item = _checked_object(
            raw,
            {"evidence_type", "statement", "status", "dimensions", "sources", "notes"},
            {"evidence_type", "statement", "status", "dimensions", "sources", "notes"},
            label,
        )
        evidence_type = item["evidence_type"]
        if evidence_type not in EVIDENCE_TYPES:
            raise ValueError(f"{label}.evidence_type must be one of: {', '.join(EVIDENCE_TYPES)}")
        statement = _bounded_text(item["statement"], f"{label}.statement")
        if statement is None:
            raise ValueError(f"{label}.statement is required")
        status = item["status"]
        if status not in EVIDENCE_STATUSES[:-1]:
            raise ValueError(f"{label}.status must be unknown, pending, confirmed, or conflicting")

        dimensions_input = item["dimensions"]
        if not isinstance(dimensions_input, list) or len(dimensions_input) > 20:
            raise ValueError(f"{label}.dimensions must be a list of at most 20 links")
        dimensions: list[dict[str, str]] = []
        seen_dimensions: set[str] = set()
        for link in dimensions_input:
            link = _checked_object(link, {"dimension_id", "direction"}, {"dimension_id", "direction"}, f"{label}.dimension")
            dimension_id = link["dimension_id"]
            direction = link["direction"]
            if not isinstance(dimension_id, str) or not TOPIC_ID_PATTERN.fullmatch(dimension_id):
                raise ValueError(f"{label}.dimension_id must be a valid lowercase slug")
            if dimension_id in seen_dimensions:
                raise ValueError(f"{label} has duplicate dimension links: {dimension_id}")
            if direction not in EVIDENCE_DIRECTIONS:
                raise ValueError(f"{label}.direction must be one of: {', '.join(EVIDENCE_DIRECTIONS)}")
            seen_dimensions.add(dimension_id)
            dimensions.append({"dimension_id": dimension_id, "direction": direction})
        dimensions.sort(key=lambda link: (link["dimension_id"], link["direction"]))

        sources_input = item["sources"]
        if not isinstance(sources_input, list) or len(sources_input) > 20:
            raise ValueError(f"{label}.sources must be a list of at most 20 links")
        sources: list[dict[str, str | None]] = []
        seen_sources: set[str] = set()
        for link in sources_input:
            link = _checked_object(link, {"source_id", "locator"}, {"source_id", "locator"}, f"{label}.source")
            source_id = _bounded_text(link["source_id"], f"{label}.source_id", 80)
            locator = _bounded_text(link["locator"], f"{label}.source.locator", 1000)
            if source_id is None:
                raise ValueError(f"{label}.source_id is required")
            if source_id in seen_sources:
                raise ValueError(f"{label} has duplicate source links: {source_id}")
            seen_sources.add(source_id)
            sources.append({"source_id": source_id, "locator": locator})
        sources.sort(key=lambda link: link["source_id"] or "")

        notes_input = item["notes"]
        if not isinstance(notes_input, list) or len(notes_input) > 20:
            raise ValueError(f"{label}.notes must be a list of at most 20 note IDs")
        notes: list[str] = []
        for note_id in notes_input:
            note_id = _bounded_text(note_id, f"{label}.note_id", 80)
            if note_id is None:
                raise ValueError(f"{label}.note_id is required")
            if note_id in notes:
                raise ValueError(f"{label} has duplicate note links: {note_id}")
            notes.append(note_id)
        notes.sort()
        evidence.append({
            "evidence_type": evidence_type,
            "statement": statement,
            "status": status,
            "dimensions": dimensions,
            "sources": sources,
            "notes": notes,
        })
    evidence.sort(key=_canonical_json)
    if not evidence and not any(item is not None for item in normalized_input.values()):
        raise ValueError("review proposal must include learner-provided activity data or reviewed evidence")
    return {
        "proposal_version": PROPOSAL_VERSION,
        "idempotency_key": idempotency_key,
        "topic_id": topic_id,
        "activity_type": activity_type,
        "occurred_at": occurred_at,
        "learner_input": normalized_input,
        "assistant_analysis": assistant_analysis,
        "evidence": evidence,
    }


def save_review_proposal(root: Path, proposal: object, approved: bool) -> str:
    if not approved:
        raise ValueError("review proposal was not saved; obtain learner approval before passing --approved")
    values = validate_review_proposal(proposal)
    payload_sha256 = hashlib.sha256(_canonical_json(values).encode("utf-8")).hexdigest()
    conn = connect(root)
    try:
        conn.execute("BEGIN IMMEDIATE")
        existing = conn.execute(
            "SELECT activity_id, payload_sha256 FROM learning_activities WHERE idempotency_key = ?",
            (values["idempotency_key"],),
        ).fetchone()
        if existing is not None:
            if existing["payload_sha256"] != payload_sha256:
                raise ValueError("idempotency_key was already used with a different review payload")
            conn.commit()
            print(f"reused activity {existing['activity_id']}")
            return existing["activity_id"]

        topic_id = values["topic_id"]
        if conn.execute("SELECT 1 FROM topics WHERE topic_id = ?", (topic_id,)).fetchone() is None:
            raise ValueError(f"unknown topic: {topic_id}")
        for evidence in values["evidence"]:
            for link in evidence["dimensions"]:
                dimension = conn.execute(
                    "SELECT eligible_activity_types_json, eligible_evidence_types_json FROM topic_profile_dimensions "
                    "WHERE topic_id = ? AND dimension_id = ?",
                    (topic_id, link["dimension_id"]),
                ).fetchone()
                if dimension is None:
                    raise ValueError(f"unknown profile dimension for topic {topic_id}: {link['dimension_id']}")
                if values["activity_type"] not in json.loads(dimension["eligible_activity_types_json"]):
                    raise ValueError(f"activity type is not eligible for dimension {link['dimension_id']}")
                if evidence["evidence_type"] not in json.loads(dimension["eligible_evidence_types_json"]):
                    raise ValueError(f"evidence type is not eligible for dimension {link['dimension_id']}")
            for source in evidence["sources"]:
                found = conn.execute(
                    "SELECT 1 FROM source_topics WHERE source_id = ? AND topic_id = ?",
                    (source["source_id"], topic_id),
                ).fetchone()
                if found is None:
                    raise ValueError(f"source {source['source_id']} is not registered for topic {topic_id}")
            for note_id in evidence["notes"]:
                found = conn.execute(
                    "SELECT 1 FROM note_topics WHERE note_id = ? AND topic_id = ?",
                    (note_id, topic_id),
                ).fetchone()
                if found is None:
                    raise ValueError(f"note {note_id} is not registered for topic {topic_id}")

        activity_id = next_id(conn, "learning_activities", "ACT")
        created_at = now()
        occurred_at = values["occurred_at"]
        conn.execute(
            """INSERT INTO learning_activities
               (activity_id, idempotency_key, payload_sha256, topic_id, activity_type, occurred_at,
                learner_input_json, assistant_analysis, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (activity_id, values["idempotency_key"], payload_sha256, topic_id, values["activity_type"],
             occurred_at, _canonical_json(values["learner_input"]), values["assistant_analysis"], created_at),
        )
        for evidence in values["evidence"]:
            evidence_id = next_id(conn, "learning_evidence", "EVD")
            conn.execute(
                """INSERT INTO learning_evidence
                   (evidence_id, activity_id, topic_id, evidence_type, statement, status, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (evidence_id, activity_id, topic_id, evidence["evidence_type"], evidence["statement"], evidence["status"], created_at),
            )
            conn.executemany(
                "INSERT INTO evidence_dimensions(evidence_id, topic_id, dimension_id, direction) VALUES (?, ?, ?, ?)",
                ((evidence_id, topic_id, link["dimension_id"], link["direction"]) for link in evidence["dimensions"]),
            )
            conn.executemany(
                "INSERT INTO evidence_sources(evidence_id, source_id, locator) VALUES (?, ?, ?)",
                ((evidence_id, link["source_id"], link["locator"]) for link in evidence["sources"]),
            )
            conn.executemany(
                "INSERT INTO evidence_notes(evidence_id, note_id) VALUES (?, ?)",
                ((evidence_id, note_id) for note_id in evidence["notes"]),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"recorded activity {activity_id} with {len(values['evidence'])} evidence items")
    return activity_id


def validate_status_transition(proposal: object) -> dict[str, object]:
    values = _checked_object(
        proposal,
        {"proposal_version", "evidence_id", "status", "reason"},
        {"proposal_version", "evidence_id", "status", "reason"},
        "evidence status proposal",
    )
    if type(values["proposal_version"]) is not int or values["proposal_version"] != PROPOSAL_VERSION:
        raise ValueError(f"proposal_version must be {PROPOSAL_VERSION}")
    evidence_id = _bounded_text(values["evidence_id"], "evidence_id", 80)
    if evidence_id is None:
        raise ValueError("evidence_id is required")
    status = values["status"]
    if status not in EVIDENCE_STATUSES:
        raise ValueError(f"status must be one of: {', '.join(EVIDENCE_STATUSES)}")
    reason = _bounded_text(values["reason"], "reason", 1000)
    if reason is None:
        raise ValueError("reason is required")
    return {"proposal_version": PROPOSAL_VERSION, "evidence_id": evidence_id, "status": status, "reason": reason}


def save_evidence_status(root: Path, proposal: object, approved: bool) -> None:
    if not approved:
        raise ValueError("evidence status was not changed; obtain learner approval before passing --approved")
    values = validate_status_transition(proposal)
    conn = connect(root)
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT status FROM learning_evidence WHERE evidence_id = ?", (values["evidence_id"],)).fetchone()
        if row is None:
            raise ValueError(f"unknown evidence: {values['evidence_id']}")
        previous = row["status"]
        if previous == "superseded":
            raise ValueError("superseded evidence is terminal and cannot be changed")
        if previous == values["status"]:
            raise ValueError(f"evidence already has status {previous}")
        changed_at = now()
        conn.execute(
            """INSERT INTO evidence_status_history
               (history_id, evidence_id, from_status, to_status, changed_at, approved_at, reason)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (next_id(conn, "evidence_status_history", "EVH"), values["evidence_id"], previous,
             values["status"], changed_at, changed_at, values["reason"]),
        )
        conn.execute("UPDATE learning_evidence SET status = ? WHERE evidence_id = ?", (values["status"], values["evidence_id"]))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"updated evidence {values['evidence_id']}: {previous} -> {values['status']}")


def validate_profile_dimension(proposal: object) -> dict[str, object]:
    values = _checked_object(
        proposal,
        {"proposal_version", "topic_id", "dimension_id", "name", "description", "eligible_activity_types", "eligible_evidence_types", "minimum_evidence_count", "recency_days"},
        {"proposal_version", "topic_id", "dimension_id", "name", "description", "eligible_activity_types", "eligible_evidence_types", "minimum_evidence_count", "recency_days"},
        "profile dimension proposal",
    )
    if type(values["proposal_version"]) is not int or values["proposal_version"] != PROPOSAL_VERSION:
        raise ValueError(f"proposal_version must be {PROPOSAL_VERSION}")
    topic_id = values["topic_id"]
    dimension_id = values["dimension_id"]
    if not isinstance(topic_id, str) or not TOPIC_ID_PATTERN.fullmatch(topic_id):
        raise ValueError("topic_id must use lowercase ASCII letters, digits, and hyphens")
    if not isinstance(dimension_id, str) or not TOPIC_ID_PATTERN.fullmatch(dimension_id):
        raise ValueError("dimension_id must use lowercase ASCII letters, digits, and hyphens")
    name = _bounded_text(values["name"], "name", 120)
    description = _bounded_text(values["description"], "description", 1000)
    if name is None or description is None:
        raise ValueError("name and description are required")

    def type_list(field: str, allowed: tuple[str, ...]) -> list[str]:
        value = values[field]
        if not isinstance(value, list) or not value or len(value) > len(allowed):
            raise ValueError(f"{field} must be a non-empty list")
        if any(not isinstance(item, str) or item not in allowed for item in value):
            raise ValueError(f"{field} contains an unsupported value")
        if len(set(value)) != len(value):
            raise ValueError(f"{field} must not contain duplicates")
        return sorted(value)

    minimum = values["minimum_evidence_count"]
    recency = values["recency_days"]
    if type(minimum) is not int or not 1 <= minimum <= 1000:
        raise ValueError("minimum_evidence_count must be an integer from 1 to 1000")
    if type(recency) is not int or not 1 <= recency <= 36500:
        raise ValueError("recency_days must be an integer from 1 to 36500")
    return {
        "proposal_version": PROPOSAL_VERSION,
        "topic_id": topic_id,
        "dimension_id": dimension_id,
        "name": name,
        "description": description,
        "eligible_activity_types": type_list("eligible_activity_types", ACTIVITY_TYPES),
        "eligible_evidence_types": type_list("eligible_evidence_types", EVIDENCE_TYPES),
        "minimum_evidence_count": minimum,
        "recency_days": recency,
    }


def save_profile_dimension(root: Path, proposal: object, approved: bool) -> None:
    if not approved:
        raise ValueError("profile dimension was not saved; obtain learner approval before passing --approved")
    values = validate_profile_dimension(proposal)
    conn = connect(root)
    try:
        conn.execute("BEGIN IMMEDIATE")
        if conn.execute("SELECT 1 FROM topics WHERE topic_id = ?", (values["topic_id"],)).fetchone() is None:
            raise ValueError(f"unknown topic: {values['topic_id']}")
        timestamp = now()
        conn.execute(
            """INSERT INTO topic_profile_dimensions
               (topic_id, dimension_id, name, description, eligible_activity_types_json,
                eligible_evidence_types_json, minimum_evidence_count, recency_days, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(topic_id, dimension_id) DO UPDATE SET
                 name = excluded.name,
                 description = excluded.description,
                 eligible_activity_types_json = excluded.eligible_activity_types_json,
                 eligible_evidence_types_json = excluded.eligible_evidence_types_json,
                 minimum_evidence_count = excluded.minimum_evidence_count,
                 recency_days = excluded.recency_days,
                 updated_at = excluded.updated_at""",
            (values["topic_id"], values["dimension_id"], values["name"], values["description"],
             _canonical_json(values["eligible_activity_types"]), _canonical_json(values["eligible_evidence_types"]),
             values["minimum_evidence_count"], values["recency_days"], timestamp, timestamp),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"saved profile dimension {values['topic_id']}/{values['dimension_id']}")


def _markdown_text(value: str) -> str:
    value = html.escape(value, quote=False)
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ").replace("`", "\\`")


def project_profile(root: Path, topic_filter: str | None = None, as_of: str | None = None) -> dict[str, object]:
    timestamp_text, timestamp = _parse_utc_timestamp(as_of, "as_of") if as_of is not None else _parse_utc_timestamp(now(), "as_of")
    assert timestamp_text is not None and timestamp is not None
    conn = connect(root)
    try:
        if topic_filter is not None:
            if not isinstance(topic_filter, str) or not TOPIC_ID_PATTERN.fullmatch(topic_filter):
                raise ValueError("topic must be a valid lowercase topic ID")
            topics = conn.execute("SELECT topic_id, name FROM topics WHERE topic_id = ?", (topic_filter,)).fetchall()
            if not topics:
                raise ValueError(f"unknown topic: {topic_filter}")
        else:
            topics = conn.execute("SELECT topic_id, name FROM topics ORDER BY topic_id").fetchall()

        projected_topics: list[dict[str, object]] = []
        for topic in topics:
            dimensions = conn.execute(
                """SELECT * FROM topic_profile_dimensions WHERE topic_id = ?
                   ORDER BY dimension_id""",
                (topic["topic_id"],),
            ).fetchall()
            projected_dimensions: list[dict[str, object]] = []
            for dimension in dimensions:
                eligible_activities = set(json.loads(dimension["eligible_activity_types_json"]))
                eligible_evidence = set(json.loads(dimension["eligible_evidence_types_json"]))
                rows = conn.execute(
                    """SELECT e.evidence_id, e.evidence_type, e.statement, e.status,
                              a.activity_type, a.occurred_at, ed.direction
                       FROM evidence_dimensions ed
                       JOIN learning_evidence e ON e.evidence_id = ed.evidence_id
                       JOIN learning_activities a ON a.activity_id = e.activity_id
                       WHERE ed.topic_id = ? AND ed.dimension_id = ?
                       ORDER BY e.evidence_id""",
                    (topic["topic_id"], dimension["dimension_id"]),
                ).fetchall()
                evidence_items: list[dict[str, object]] = []
                cutoff = timestamp - timedelta(days=dimension["recency_days"])
                for row in rows:
                    if row["activity_type"] not in eligible_activities or row["evidence_type"] not in eligible_evidence:
                        continue
                    item_time = None
                    if row["occurred_at"] is not None:
                        _, item_time = _parse_utc_timestamp(row["occurred_at"], "stored occurred_at")
                    if row["status"] == "superseded":
                        recency_state = "superseded"
                    elif item_time is None:
                        recency_state = "undated"
                    elif item_time < cutoff:
                        recency_state = "stale"
                    elif item_time > timestamp:
                        recency_state = "future"
                    else:
                        recency_state = "current"
                    source_rows = conn.execute(
                        "SELECT source_id, locator FROM evidence_sources WHERE evidence_id = ? ORDER BY source_id",
                        (row["evidence_id"],),
                    ).fetchall()
                    note_rows = conn.execute(
                        "SELECT note_id FROM evidence_notes WHERE evidence_id = ? ORDER BY note_id",
                        (row["evidence_id"],),
                    ).fetchall()
                    evidence_items.append({
                        "evidence_id": row["evidence_id"],
                        "evidence_type": row["evidence_type"],
                        "statement": row["statement"],
                        "status": row["status"],
                        "direction": row["direction"],
                        "occurred_at": row["occurred_at"],
                        "recency_state": recency_state,
                        "sources": [{"source_id": source["source_id"], "locator": source["locator"]} for source in source_rows],
                        "notes": [note["note_id"] for note in note_rows],
                    })

                active_items = [item for item in evidence_items if item["status"] != "superseded"]
                current_items = [item for item in active_items if item["recency_state"] == "current"]
                confirmed = [item for item in current_items if item["status"] == "confirmed"]
                supporting = [item for item in confirmed if item["direction"] == "supports"]
                contradicting = [item for item in confirmed if item["direction"] == "contradicts"]
                disputed = [item for item in current_items if item["status"] == "conflicting"]
                unresolved = [item for item in current_items if item["status"] in ("unknown", "pending")]
                minimum = dimension["minimum_evidence_count"]
                if disputed or (supporting and contradicting):
                    status = "conflicting"
                elif not active_items:
                    status = "unknown"
                elif unresolved or any(item["recency_state"] == "undated" for item in active_items):
                    status = "pending"
                elif len(supporting) >= minimum and not contradicting:
                    status = "confirmed"
                elif len(contradicting) >= minimum and not supporting:
                    status = "confirmed"
                else:
                    status = "pending"
                dated_claim_items = [
                    item for item in supporting + contradicting + disputed
                    if item["occurred_at"] is not None
                ]
                evidence_through = None
                if dated_claim_items:
                    latest = max(
                        _parse_utc_timestamp(item["occurred_at"], "stored occurred_at")[1]
                        for item in dated_claim_items
                    )
                    evidence_through = latest.isoformat(timespec="microseconds" if latest.microsecond else "seconds")
                projected_dimensions.append({
                    "dimension_id": dimension["dimension_id"],
                    "name": dimension["name"],
                    "description": dimension["description"],
                    "minimum_evidence_count": minimum,
                    "recency_days": dimension["recency_days"],
                    "status": status,
                    "evidence_through": evidence_through,
                    "supporting": supporting,
                    "contradicting": contradicting,
                    "disputed": disputed,
                    "evidence": evidence_items,
                })
            projected_topics.append({"topic_id": topic["topic_id"], "name": topic["name"], "dimensions": projected_dimensions})
    finally:
        conn.close()
    return {"as_of": timestamp_text, "topics": projected_topics}


def render_profile(root: Path, topic_filter: str | None = None, as_of: str | None = None) -> str:
    projection = project_profile(root, topic_filter, as_of)
    lines = ["<!-- Generated by learnbase profile report; do not edit. -->", "", "# 学习者 Profile", "", f"生成时间（UTC）：{projection['as_of']}", ""]
    if not projection["topics"]:
        lines.append("尚未创建 topic。")
        return "\n".join(lines).rstrip() + "\n"
    for topic in projection["topics"]:
        lines.extend([f"## {_markdown_text(topic['name'])} (`{topic['topic_id']}`)", ""])
        if not topic["dimensions"]:
            lines.extend(["尚未配置 profile 维度。", ""])
            continue
        for dimension in topic["dimensions"]:
            lines.extend([
                f"### {_markdown_text(dimension['name'])} (`{dimension['dimension_id']}`)",
                "",
                f"- 状态：`{dimension['status']}`",
                f"- 维度说明：{_markdown_text(dimension['description'])}",
                f"- 规则：至少 {dimension['minimum_evidence_count']} 条已确认依据，最近 {dimension['recency_days']} 天（含边界）",
                f"- 窗口内已确认方向证据：{len(dimension['supporting']) + len(dimension['contradicting'])} 条",
                f"- 证据截至：{dimension['evidence_through'] or '暂无近期已确认方向证据'}",
            ])
            for label, key in (("支持", "supporting"), ("相反", "contradicting"), ("争议", "disputed")):
                items = dimension[key]
                if items:
                    lines.append(f"- {label}依据：" + ", ".join(f"`{item['evidence_id']}`" for item in items))
            if dimension["evidence"]:
                lines.append("- 证据记录：")
                for item in dimension["evidence"]:
                    occurred = item["occurred_at"] or "日期未知"
                    details = [f"`{item['evidence_id']}`", f"{item['status']}/{item['direction']}", occurred, item["recency_state"], _markdown_text(item["statement"])]
                    provenance = [f"{source['source_id']}" + (f" {source['locator']}" if source["locator"] else "") for source in item["sources"]]
                    provenance.extend(item["notes"])
                    if provenance:
                        details.append("来源/笔记 " + ", ".join(f"`{value}`" for value in provenance))
                    lines.append("  - " + "；".join(details))
            else:
                lines.append("- 证据记录：无")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_profile_report(root: Path, report: str, relative: str) -> Path:
    reports_root = (root / "reports").resolve()
    reports_root.mkdir(parents=True, exist_ok=True)
    candidate = (reports_root / relative).resolve()
    try:
        candidate.relative_to(reports_root)
    except ValueError as exc:
        raise ValueError("profile report output must remain inside reports/") from exc
    if candidate == reports_root or candidate.suffix.lower() != ".md":
        raise ValueError("profile report output must be a Markdown file inside reports/")
    candidate.parent.mkdir(parents=True, exist_ok=True)
    marker = "<!-- Generated by learnbase profile report; do not edit. -->"
    if candidate.exists():
        existing = candidate.read_text(encoding="utf-8")
        if not existing.startswith(marker):
            raise ValueError(f"refusing to overwrite non-generated report: {candidate.relative_to(reports_root).as_posix()}")
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=candidate.parent, prefix=".learnbase-report-", delete=False) as temp_file:
            temp_name = temp_file.name
            temp_file.write(report)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        if candidate.exists():
            os.replace(temp_name, candidate)
        else:
            try:
                os.link(temp_name, candidate)
            except FileExistsError:
                existing = candidate.read_text(encoding="utf-8")
                if not existing.startswith(marker):
                    raise ValueError(f"refusing to overwrite non-generated report: {candidate.relative_to(reports_root).as_posix()}")
                os.replace(temp_name, candidate)
            else:
                os.unlink(temp_name)
        temp_name = None
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)
    print(f"wrote generated profile report {candidate.relative_to(reports_root).as_posix()}")
    return candidate


def create_note(root: Path, title: str, topics: list[str], sources: list[str], locators: list[str]) -> Path:
    conn = connect(root)
    output: Path | None = None
    created_file = False
    try:
        selected_topics = topic_ids(conn, topics)
        source_ids = list(dict.fromkeys(sources))
        if not source_ids:
            raise ValueError("at least one --source is required")
        locator_map: dict[str, str] = {}
        for item in locators:
            source_id, separator, locator = item.partition("=")
            if not separator or source_id not in source_ids or not locator.strip():
                raise ValueError("each --locator must be SOURCE-ID=position and match a --source")
            locator_map[source_id] = locator.strip()
        for source_id in source_ids:
            if conn.execute("SELECT 1 FROM sources WHERE source_id = ?", (source_id,)).fetchone() is None:
                raise ValueError(f"unknown source: {source_id}")
        note_id = next_id(conn, "notes", "NOTE")
        created = date.today().isoformat()
        relative = Path("02-notes") / selected_topics[0] / f"{created}-{note_id}.md"
        output = root / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        if output.exists():
            raise ValueError(f"refusing to overwrite existing note: {relative.as_posix()}")
        source_rows = conn.execute(
            "SELECT source_id, title, locator FROM sources WHERE source_id IN (%s)" % ",".join("?" for _ in source_ids),
            source_ids,
        ).fetchall()
        source_map = {row["source_id"]: row for row in source_rows}
        frontmatter = ["---", f"id: {note_id}", f"title: {json.dumps(title, ensure_ascii=False)}", "topics:"]
        frontmatter.extend(f"  - {topic}" for topic in selected_topics)
        frontmatter.extend([f"created: {created}", "sources:"])
        frontmatter.extend(f"  - id: {source_id}\n    locator: {json.dumps(locator_map.get(source_id, ''), ensure_ascii=False)}" for source_id in source_ids)
        source_lines = [
            f"- `{source_id}`: {source_map[source_id]['title']} ({source_map[source_id]['locator']}; {locator_map.get(source_id) or '定位待补充'})"
            for source_id in source_ids
        ]
        content = "\n".join(frontmatter + ["---", "", f"# {title}", "", "## 核心要点", "", "## 解释与例子", "", "## 边界与待核验", "", "## 来源", "", *source_lines, ""])
        conn.execute("INSERT INTO notes(note_id, title, path, created_at) VALUES (?, ?, ?, ?)", (note_id, title, relative.as_posix(), now()))
        conn.executemany("INSERT INTO note_topics(note_id, topic_id) VALUES (?, ?)", ((note_id, topic) for topic in selected_topics))
        conn.executemany(
            "INSERT INTO note_sources(note_id, source_id, locator) VALUES (?, ?, ?)",
            ((note_id, source_id, locator_map.get(source_id, "")) for source_id in source_ids),
        )
        output.write_text(content, encoding="utf-8")
        created_file = True
        conn.commit()
    except Exception:
        if created_file and output is not None and output.exists():
            output.unlink()
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"created {relative.as_posix()}")
    return output


def _validate_note_file(root: Path, relative: str) -> str:
    note_path = (root / relative).resolve()
    try:
        note_path.relative_to((root / "02-notes").resolve())
    except ValueError as exc:
        raise ValueError("note path must be inside 02-notes/") from exc
    if not note_path.is_file():
        raise ValueError(f"note not found: {relative}")
    content = note_path.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^---\s*\n(.*?)\n---\s*(?:\n|$)", content)
    if not match:
        raise ValueError("note is missing YAML frontmatter")
    note_id_match = re.search(r"(?m)^id:\s*(NOTE-\d{4})\s*$", match.group(1))
    if not note_id_match:
        raise ValueError("note frontmatter is missing a valid note ID")
    frontmatter_sources = set(re.findall(r"(?m)^  - id:\s*(SRC-\d{4})\s*$", match.group(1)))
    conn = connect(root)
    try:
        row = conn.execute("SELECT note_id FROM notes WHERE path = ?", (Path(relative).as_posix(),)).fetchone()
        if row is None or row["note_id"] != note_id_match.group(1):
            raise ValueError("note ID/path does not match the local registry")
        expected_rows = conn.execute("SELECT source_id, locator FROM note_sources WHERE note_id = ?", (row["note_id"],)).fetchall()
        expected = {item["source_id"] for item in expected_rows}
        actual_locators = {}
        for item in re.finditer(r"(?m)^  - id:[ \t]*(SRC-\d{4})[ \t]*\n    locator:[ \t]*(.*)$", match.group(1)):
            try:
                actual_locators[item.group(1)] = json.loads(item.group(2))
            except json.JSONDecodeError as exc:
                raise ValueError("note source locator must be a quoted YAML string") from exc
        expected_locators = {item["source_id"]: item["locator"] for item in expected_rows}
        if not frontmatter_sources or frontmatter_sources != expected or actual_locators != expected_locators:
            raise ValueError("note source citations do not match the local registry")
        missing = [sid for sid in frontmatter_sources if conn.execute("SELECT 1 FROM sources WHERE source_id = ?", (sid,)).fetchone() is None]
        if missing:
            raise ValueError(f"unregistered source IDs: {', '.join(sorted(missing))}")
    finally:
        conn.close()
    return row["note_id"]


def validate_note(root: Path, relative: str) -> None:
    note_id = _validate_note_file(root, relative)
    print(f"valid {relative} ({note_id})")


def validate_card_proposal(proposal: object) -> dict[str, object]:
    values = _checked_object(
        proposal,
        {"proposal_version", "topic_id", "objective_key", "front", "back", "note_ids", "evidence_ids", "card_id", "replace_content"},
        {"proposal_version", "topic_id", "objective_key", "front", "back", "note_ids", "evidence_ids"},
        "card proposal",
    )
    if type(values["proposal_version"]) is not int or values["proposal_version"] != CARD_PROPOSAL_VERSION:
        raise ValueError(f"proposal_version must be {CARD_PROPOSAL_VERSION}")
    topic_id = values["topic_id"]
    if not isinstance(topic_id, str) or not TOPIC_ID_PATTERN.fullmatch(topic_id):
        raise ValueError("topic_id must use lowercase ASCII letters, digits, and hyphens")
    objective_key = values["objective_key"]
    if not isinstance(objective_key, str) or not TOPIC_ID_PATTERN.fullmatch(objective_key) or len(objective_key) > 80:
        raise ValueError("objective_key must be a lowercase ASCII slug of at most 80 characters")
    front = _bounded_text(values["front"], "front", 5000)
    back = _bounded_text(values["back"], "back", 10000)
    if front is None or back is None:
        raise ValueError("front and back are required")
    if re.search(r"(?m)^#{1,6}\s", front) or re.search(r"(?m)^#{1,6}\s", back):
        raise ValueError("front and back must not contain Markdown heading lines")

    def id_list(field: str, pattern: str, maximum: int = 20) -> list[str]:
        items = values[field]
        if not isinstance(items, list) or not 1 <= len(items) <= maximum:
            raise ValueError(f"{field} must contain 1 to {maximum} IDs")
        if any(not isinstance(item, str) or not re.fullmatch(pattern, item) for item in items):
            raise ValueError(f"{field} contains an invalid ID")
        if len(set(items)) != len(items):
            raise ValueError(f"{field} must not contain duplicates")
        return sorted(items)

    card_id = values.get("card_id")
    if card_id is not None and (not isinstance(card_id, str) or not CARD_ID_PATTERN.fullmatch(card_id)):
        raise ValueError("card_id must be null or a valid CARD-NNNN identifier")
    replace_content = values.get("replace_content", False)
    if type(replace_content) is not bool or (replace_content and card_id is None):
        raise ValueError("replace_content must be a boolean; replacement requires an explicit card_id")
    return {
        "proposal_version": CARD_PROPOSAL_VERSION,
        "topic_id": topic_id,
        "objective_key": objective_key,
        "front": front,
        "back": back,
        "note_ids": id_list("note_ids", r"NOTE-\d{4,}"),
        "evidence_ids": id_list("evidence_ids", r"EVD-\d{4,}"),
        "card_id": card_id,
        "replace_content": replace_content,
    }


def _normalized_card_side(value: str) -> str:
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n")).strip()


def _render_card_markdown(
    card_id: str,
    topic_id: str,
    objective_key: str,
    created_at: str,
    updated_at: str,
    note_ids: list[str],
    evidence_ids: list[str],
    sources: list[tuple[str, str]],
    front: str,
    back: str,
) -> str:
    source_values = [{"id": source_id, "locator": locator} for source_id, locator in sources]
    frontmatter = [
        "---",
        f"id: {card_id}",
        f"topic: {topic_id}",
        f"objective_key: {json.dumps(objective_key, ensure_ascii=False)}",
        f"created: {json.dumps(created_at, ensure_ascii=False)}",
        f"updated: {json.dumps(updated_at, ensure_ascii=False)}",
        f"notes: {json.dumps(note_ids, ensure_ascii=False)}",
        f"evidence: {json.dumps(evidence_ids, ensure_ascii=False)}",
        f"sources: {json.dumps(source_values, ensure_ascii=False, sort_keys=True)}",
        "---",
    ]
    return "\n".join(frontmatter + ["", "## Front", front, "## Back", back, ""])


def _parse_card_markdown(content: str) -> dict[str, object]:
    match = re.search(r"(?s)\A---[ \t]*\n(.*?)\n---[ \t]*(?:\n|$)", content)
    if not match:
        raise ValueError("card draft is missing YAML frontmatter")
    metadata: dict[str, object] = {}
    for field in ("id", "topic", "objective_key", "created", "updated", "notes", "evidence", "sources"):
        field_matches = list(re.finditer(rf"(?m)^{field}:[ \t]*(.*)$", match.group(1)))
        if len(field_matches) != 1:
            raise ValueError(f"card draft frontmatter must contain exactly one {field}")
        field_match = field_matches[0]
        raw = field_match.group(1)
        if field in ("id", "topic"):
            metadata[field] = raw
        else:
            try:
                metadata[field] = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ValueError(f"card draft {field} must use a JSON-compatible YAML value") from exc
    sections = CARD_SECTION_PATTERN.fullmatch(content[match.end():].lstrip("\n"))
    if sections is None:
        raise ValueError("card draft must contain one Front section followed by one Back section")
    front = sections.group(1).strip()
    back = sections.group(2).removesuffix("\n").strip()
    if not front or not back:
        raise ValueError("card draft front and back sections must not be empty")
    metadata["front"] = front
    metadata["back"] = back
    validate_card_proposal({
        "proposal_version": 1, "topic_id": metadata["topic"], "objective_key": metadata["objective_key"],
        "front": front, "back": back, "note_ids": metadata["notes"], "evidence_ids": metadata["evidence"],
    })
    return metadata


def _card_sources(conn: sqlite3.Connection, note_ids: list[str], evidence_ids: list[str]) -> list[tuple[str, str]]:
    pairs: set[tuple[str, str]] = set()
    if note_ids:
        placeholders = ",".join("?" for _ in note_ids)
        rows = conn.execute(
            f"SELECT source_id, locator FROM note_sources WHERE note_id IN ({placeholders})",
            note_ids,
        ).fetchall()
        pairs.update((row["source_id"], row["locator"] or "") for row in rows)
    if evidence_ids:
        placeholders = ",".join("?" for _ in evidence_ids)
        rows = conn.execute(
            f"SELECT source_id, locator FROM evidence_sources WHERE evidence_id IN ({placeholders}) "
            f"UNION SELECT ns.source_id, ns.locator FROM evidence_notes en JOIN note_sources ns USING (note_id) "
            f"WHERE en.evidence_id IN ({placeholders})",
            evidence_ids + evidence_ids,
        ).fetchall()
        pairs.update((row["source_id"], row["locator"] or "") for row in rows)
    return sorted(pairs)


def _card_link_ids(conn: sqlite3.Connection, table: str, card_id: str, column: str) -> list[str]:
    if (table, column) not in (("card_notes", "note_id"), ("card_evidence", "evidence_id")):
        raise ValueError("unsupported card relation")
    rows = conn.execute(f"SELECT {column} FROM {table} WHERE card_id = ? ORDER BY {column}", (card_id,)).fetchall()
    return [row[column] for row in rows]


def _validate_card_file(root: Path, conn: sqlite3.Connection, relative: str) -> dict[str, object]:
    cards_root = (root / "04-cards" / "drafts").resolve()
    card_path = (root / relative).resolve()
    try:
        cards_root.relative_to(root.resolve())
        card_path.relative_to(cards_root)
    except ValueError as exc:
        raise ValueError("card path must be inside 04-cards/drafts/") from exc
    if not card_path.is_file():
        raise ValueError(f"card draft not found: {relative}")
    content = card_path.read_text(encoding="utf-8")
    parsed = _parse_card_markdown(content)
    card_id = parsed["id"]
    if not isinstance(card_id, str) or not CARD_ID_PATTERN.fullmatch(card_id):
        raise ValueError("card draft frontmatter is missing a valid card ID")
    row = conn.execute("SELECT * FROM cards WHERE path = ?", (Path(relative).as_posix(),)).fetchone()
    if row is None or row["card_id"] != card_id:
        raise ValueError("card ID/path does not match the local registry")
    if parsed["topic"] != row["topic_id"] or parsed["objective_key"] != row["objective_key"]:
        raise ValueError("card draft identity does not match the local registry")
    expected_notes = _card_link_ids(conn, "card_notes", card_id, "note_id")
    expected_evidence = _card_link_ids(conn, "card_evidence", card_id, "evidence_id")
    expected_sources = conn.execute(
        "SELECT source_id, locator FROM card_sources WHERE card_id = ? ORDER BY source_id, locator", (card_id,)
    ).fetchall()
    actual_sources = parsed["sources"]
    if parsed["notes"] != expected_notes or parsed["evidence"] != expected_evidence:
        raise ValueError("card note/evidence references do not match the local registry")
    if not isinstance(actual_sources, list) or any(
        not isinstance(item, dict) or set(item) != {"id", "locator"}
        or not isinstance(item["id"], str) or not isinstance(item["locator"], str) for item in actual_sources
    ):
        raise ValueError("card source references must contain id and locator")
    normalized_sources = sorted((item["id"], item["locator"]) for item in actual_sources)
    if normalized_sources != [(item["source_id"], item["locator"]) for item in expected_sources]:
        raise ValueError("card source citations do not match the local registry")
    for note_id in expected_notes:
        note = conn.execute("SELECT path FROM notes WHERE note_id = ?", (note_id,)).fetchone()
        if note is None:
            raise ValueError(f"card refers to a missing note: {note_id}")
        _validate_note_file(root, note["path"])
    parsed["evidence_statuses"] = {
        item["evidence_id"]: item["status"] for item in conn.execute(
            "SELECT e.evidence_id, e.status FROM learning_evidence e JOIN card_evidence c USING (evidence_id) "
            "WHERE c.card_id = ? ORDER BY e.evidence_id", (card_id,),
        )
    }
    parsed["card_id"] = card_id
    parsed["path"] = Path(relative).as_posix()
    return parsed


def validate_card(root: Path, relative: str) -> dict[str, object]:
    conn = connect(root)
    try:
        card = _validate_card_file(root, conn, relative)
    finally:
        conn.close()
    print(f"valid {relative} ({card['card_id']})")
    return card


def save_card_proposal(root: Path, proposal: object, approved: bool) -> str:
    if not approved:
        raise ValueError("card proposal was not saved; obtain learner approval before passing --approved")
    values = validate_card_proposal(proposal)
    conn = connect(root)
    temp_name: str | None = None
    output: Path | None = None
    old_content: str | None = None
    created_file = False
    replaced_file = False
    card_id = ""
    try:
        conn.execute("BEGIN IMMEDIATE")
        topic_id = values["topic_id"]
        if conn.execute("SELECT 1 FROM topics WHERE topic_id = ?", (topic_id,)).fetchone() is None:
            raise ValueError(f"unknown topic: {topic_id}")

        note_ids = values["note_ids"]
        evidence_ids = values["evidence_ids"]
        for note_id in note_ids:
            note_row = conn.execute(
                "SELECT path FROM notes n JOIN note_topics nt USING (note_id) WHERE n.note_id = ? AND nt.topic_id = ?",
                (note_id, topic_id),
            ).fetchone()
            if note_row is None:
                raise ValueError(f"note {note_id} is not registered under topic {topic_id}")
            _validate_note_file(root, note_row["path"])
        for evidence_id in evidence_ids:
            evidence_row = conn.execute(
                "SELECT 1 FROM learning_evidence WHERE evidence_id = ? AND topic_id = ?",
                (evidence_id, topic_id),
            ).fetchone()
            if evidence_row is None:
                raise ValueError(f"evidence {evidence_id} is not registered under topic {topic_id}")

        existing = conn.execute(
            "SELECT * FROM cards WHERE topic_id = ? AND objective_key = ?",
            (topic_id, values["objective_key"]),
        ).fetchone()
        requested_id = values["card_id"]
        if existing is not None:
            if requested_id is not None and requested_id != existing["card_id"]:
                raise ValueError("card_id does not match the existing card for this topic/objective")
            card_id = existing["card_id"]
            existing_card = _validate_card_file(root, conn, existing["path"])
            content_differs = (
                _normalized_card_side(existing_card["front"]) != _normalized_card_side(values["front"])
                or _normalized_card_side(existing_card["back"]) != _normalized_card_side(values["back"])
            )
            if content_differs and not values["replace_content"]:
                raise ValueError("card content conflicts with the existing objective; reviewed replacement is required")
            new_links = (set(note_ids) - set(existing_card["notes"])) or (
                set(evidence_ids) - set(existing_card["evidence"])
            )
            if new_links and requested_id is None:
                raise ValueError(f"merging provenance requires explicit card_id {card_id}")
            if not content_differs and not new_links:
                conn.rollback()
                print(f"reused card draft {card_id} ({existing['path']})")
                return card_id
            if not values["replace_content"]:
                values["front"], values["back"] = existing_card["front"], existing_card["back"]
            output = root / existing["path"]
            old_content = output.read_text(encoding="utf-8")
            created_at = existing["created_at"]
            created = False
        else:
            if requested_id is not None:
                raise ValueError(f"unknown card_id: {requested_id}")
            card_id = next_id(conn, "cards", "CARD")
            created_at = now()
            relative = Path("04-cards") / "drafts" / topic_id / f"{date.today().isoformat()}-{card_id}.md"
            output = root / relative
            try:
                drafts_root = (root / "04-cards" / "drafts").resolve()
                drafts_root.relative_to(root.resolve())
                output.resolve().relative_to(drafts_root)
            except ValueError as exc:
                raise ValueError("card path must be inside 04-cards/drafts/") from exc
            output.parent.mkdir(parents=True, exist_ok=True)
            if output.exists():
                raise ValueError(f"refusing to overwrite existing card draft: {relative.as_posix()}")
            created = True

        if created:
            conn.execute(
                "INSERT INTO cards(card_id, topic_id, objective_key, path, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (card_id, topic_id, values["objective_key"], output.relative_to(root).as_posix(), created_at, created_at),
            )
        conn.executemany(
            "INSERT OR IGNORE INTO card_notes(card_id, topic_id, note_id) VALUES (?, ?, ?)",
            ((card_id, topic_id, note_id) for note_id in note_ids),
        )
        conn.executemany(
            "INSERT OR IGNORE INTO card_evidence(card_id, topic_id, evidence_id) VALUES (?, ?, ?)",
            ((card_id, topic_id, evidence_id) for evidence_id in evidence_ids),
        )
        all_notes = _card_link_ids(conn, "card_notes", card_id, "note_id") if not created else note_ids
        all_evidence = _card_link_ids(conn, "card_evidence", card_id, "evidence_id") if not created else evidence_ids
        if len(all_notes) > 20 or len(all_evidence) > 20:
            raise ValueError("a card supports at most 20 note IDs and 20 evidence IDs")
        sources = _card_sources(conn, all_notes, all_evidence)
        if not sources:
            raise ValueError("card provenance has no registered source; link a note or evidence item to a source")
        if not created:
            conn.execute("UPDATE cards SET updated_at = ? WHERE card_id = ?", (now(), card_id))
        conn.executemany(
            "INSERT OR IGNORE INTO card_sources(card_id, source_id, locator) VALUES (?, ?, ?)",
            ((card_id, source_id, locator) for source_id, locator in sources),
        )
        all_sources_rows = conn.execute(
            "SELECT source_id, locator FROM card_sources WHERE card_id = ? ORDER BY source_id, locator", (card_id,)
        ).fetchall()
        all_sources = [(row["source_id"], row["locator"]) for row in all_sources_rows]
        updated_at = created_at if created else conn.execute(
            "SELECT updated_at FROM cards WHERE card_id = ?", (card_id,)
        ).fetchone()["updated_at"]
        content = _render_card_markdown(
            card_id, topic_id, values["objective_key"], created_at, updated_at,
            all_notes, all_evidence, all_sources, values["front"], values["back"],
        )
        fd, temp_name = tempfile.mkstemp(prefix=f".{card_id}.", suffix=".tmp", dir=output.parent)
        with os.fdopen(fd, "w", encoding="utf-8") as temp_file:
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())
        if created:
            os.link(temp_name, output)
            created_file = True
        else:
            if output.read_text(encoding="utf-8") != old_content:
                raise ValueError("card draft changed during save; review it and retry")
            os.replace(temp_name, output)
            temp_name = None
            replaced_file = True
        conn.commit()
    except Exception:
        conn.rollback()
        if created_file and output is not None:
            output.unlink(missing_ok=True)
        elif replaced_file and output is not None and old_content is not None:
            restore_name: str | None = None
            try:
                fd, restore_name = tempfile.mkstemp(prefix=f".{card_id}.restore.", suffix=".tmp", dir=output.parent)
                with os.fdopen(fd, "w", encoding="utf-8") as restore_file:
                    restore_file.write(old_content)
                    restore_file.flush()
                    os.fsync(restore_file.fileno())
                os.replace(restore_name, output)
                restore_name = None
            finally:
                if restore_name is not None:
                    Path(restore_name).unlink(missing_ok=True)
        raise
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)
        conn.close()
    print(f"saved card draft {card_id} ({output.relative_to(root).as_posix()})")
    return card_id


def list_cards(root: Path, topic_filter: str | None = None) -> list[dict[str, str]]:
    conn = connect(root)
    try:
        if topic_filter is not None and conn.execute(
            "SELECT 1 FROM topics WHERE topic_id = ?", (topic_filter,)
        ).fetchone() is None:
            raise ValueError(f"unknown topic: {topic_filter}")
        if topic_filter is None:
            rows = conn.execute(
                "SELECT card_id, topic_id, objective_key, path FROM cards ORDER BY topic_id, card_id"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT card_id, topic_id, objective_key, path FROM cards WHERE topic_id = ? ORDER BY card_id",
                (topic_filter,),
            ).fetchall()
        cards = []
        for row in rows:
            _validate_card_file(root, conn, row["path"])
            cards.append(dict(row))
        return cards
    finally:
        conn.close()


def _ankiconnect_request(action: str, params: dict[str, object] | None = None) -> object:
    if action not in ANKI_READ_ACTIONS:
        raise ValueError(f"AnkiConnect action is not allowed: {action}")
    body = _canonical_json({"action": action, "version": 6, "params": params or {}}).encode("utf-8")
    connection = http.client.HTTPConnection(
        ANKI_CONNECT_HOST, ANKI_CONNECT_PORT, timeout=ANKI_CONNECT_TIMEOUT_SECONDS
    )
    try:
        connection.request("POST", "/", body=body, headers={"Content-Type": "application/json"})
        response = connection.getresponse()
        if response.status != 200:
            raise ValueError(f"AnkiConnect returned HTTP {response.status}")
        content_length = response.getheader("Content-Length")
        if content_length is not None:
            try:
                length = int(content_length)
            except ValueError as exc:
                raise ValueError("AnkiConnect returned an invalid Content-Length") from exc
            if length < 0:
                raise ValueError("AnkiConnect returned an invalid Content-Length")
            if length > ANKI_CONNECT_MAX_RESPONSE_BYTES:
                raise ValueError("AnkiConnect response exceeds the 2 MiB limit")
        raw = response.read(ANKI_CONNECT_MAX_RESPONSE_BYTES + 1)
        if len(raw) > ANKI_CONNECT_MAX_RESPONSE_BYTES:
            raise ValueError("AnkiConnect response exceeds the 2 MiB limit")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("AnkiConnect returned invalid JSON") from exc
        if not isinstance(payload, dict) or set(payload) != {"result", "error"}:
            raise ValueError("AnkiConnect response must contain result and error")
        if payload["error"] is not None:
            raise ValueError(f"AnkiConnect {action} failed: {payload['error']}")
        return payload["result"]
    except (OSError, http.client.HTTPException) as exc:
        raise ValueError(f"AnkiConnect is unavailable at http://{ANKI_CONNECT_HOST}:{ANKI_CONNECT_PORT}: {exc}") from exc
    finally:
        connection.close()


def anki_decks(root: Path) -> list[str]:
    connect(root).close()
    result = _ankiconnect_request("deckNames")
    if not isinstance(result, list) or any(not isinstance(name, str) or not name for name in result):
        raise ValueError("AnkiConnect deckNames result must be a list of non-empty names")
    return sorted(set(result))


def add_anki_mapping(root: Path, topic_id: str, deck_name: str) -> None:
    deck_name = _bounded_text(deck_name, "deck", 500)
    if deck_name is None:
        raise ValueError("deck is required")
    conn = connect(root)
    try:
        if conn.execute("SELECT 1 FROM topics WHERE topic_id = ?", (topic_id,)).fetchone() is None:
            raise ValueError(f"unknown topic: {topic_id}")
    finally:
        conn.close()
    decks = anki_decks(root)
    if deck_name not in decks:
        raise ValueError(f"Anki deck does not exist: {deck_name}")
    conn = connect(root)
    try:
        conn.execute(
            "INSERT OR IGNORE INTO topic_anki_decks(topic_id, deck_name, created_at) VALUES (?, ?, ?)",
            (topic_id, deck_name, now()),
        )
        conn.commit()
    finally:
        conn.close()
    print(f"mapped {topic_id} -> {deck_name}")


def remove_anki_mapping(root: Path, topic_id: str, deck_name: str) -> None:
    conn = connect(root)
    try:
        if conn.execute("SELECT 1 FROM topics WHERE topic_id = ?", (topic_id,)).fetchone() is None:
            raise ValueError(f"unknown topic: {topic_id}")
        cursor = conn.execute(
            "DELETE FROM topic_anki_decks WHERE topic_id = ? AND deck_name = ?", (topic_id, deck_name)
        )
        if cursor.rowcount == 0:
            raise ValueError(f"topic/deck mapping does not exist: {topic_id} -> {deck_name}")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    print(f"unmapped {topic_id} -> {deck_name}")


def list_anki_mappings(root: Path, topic_filter: str | None = None) -> list[dict[str, str]]:
    conn = connect(root)
    try:
        if topic_filter is not None and conn.execute(
            "SELECT 1 FROM topics WHERE topic_id = ?", (topic_filter,)
        ).fetchone() is None:
            raise ValueError(f"unknown topic: {topic_filter}")
        if topic_filter is None:
            rows = conn.execute(
                "SELECT topic_id, deck_name FROM topic_anki_decks ORDER BY topic_id, deck_name"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT topic_id, deck_name FROM topic_anki_decks WHERE topic_id = ? ORDER BY deck_name",
                (topic_filter,),
            ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def _anki_query_quote(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


class _AnkiFieldText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("div", "p", "br", "li"):
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in ("div", "p", "li"):
            self.parts.append("\n")


def _anki_plain_text(value: str) -> str:
    parser = _AnkiFieldText()
    parser.feed(value)
    parser.close()
    return " ".join(unicodedata.normalize("NFC", "".join(parser.parts)).split())


def preview_anki(root: Path, topic_id: str, deck_name: str | None = None) -> list[dict[str, object]]:
    conn = connect(root)
    try:
        if conn.execute("SELECT 1 FROM topics WHERE topic_id = ?", (topic_id,)).fetchone() is None:
            raise ValueError(f"unknown topic: {topic_id}")
        if deck_name is None:
            deck_rows = conn.execute(
                "SELECT deck_name FROM topic_anki_decks WHERE topic_id = ? ORDER BY deck_name", (topic_id,)
            ).fetchall()
            selected_decks = [row["deck_name"] for row in deck_rows]
            if not selected_decks:
                raise ValueError(f"no Anki decks are mapped to topic {topic_id}")
        else:
            selected_decks = [_bounded_text(deck_name, "deck", 500) or ""]
        card_rows = conn.execute(
            "SELECT path, card_id FROM cards WHERE topic_id = ? ORDER BY card_id", (topic_id,)
        ).fetchall()
        cards = [_validate_card_file(root, conn, row["path"]) for row in card_rows]
    finally:
        conn.close()

    live_decks = anki_decks(root)
    missing = [deck for deck in selected_decks if deck not in live_decks]
    if missing:
        raise ValueError(f"mapped Anki deck is no longer available: {', '.join(missing)}")
    models = _ankiconnect_request("modelNames")
    if not isinstance(models, list) or any(not isinstance(model, str) for model in models):
        raise ValueError("AnkiConnect modelNames result must be a list of names")
    if "Basic" not in models:
        raise ValueError("AnkiConnect collection has no Basic model; choose or prepare that note type before preview")
    field_names = _ankiconnect_request("modelFieldNames", {"modelName": "Basic"})
    if (not isinstance(field_names, list) or any(not isinstance(item, str) for item in field_names)
            or sorted(field_names) != ["Back", "Front"]):
        raise ValueError("AnkiConnect Basic model must expose exactly Front and Back fields")

    previews: list[dict[str, object]] = []
    for deck in selected_decks:
        query = f"deck:{_anki_query_quote(deck)} note:{_anki_query_quote('Basic')}"
        note_ids = _ankiconnect_request("findNotes", {"query": query})
        if (not isinstance(note_ids, list) or any(type(note_id) is not int or note_id < 1 for note_id in note_ids)
                or len(set(note_ids)) != len(note_ids)):
            raise ValueError("AnkiConnect findNotes result must be a list of integer note IDs")
        if len(note_ids) > 10000:
            raise ValueError("Anki preview is limited to 10000 Basic notes per deck scope")
        note_infos: list[object] = []
        for offset in range(0, len(note_ids), 100):
            requested_ids = note_ids[offset:offset + 100]
            batch = _ankiconnect_request("notesInfo", {"notes": requested_ids})
            if (not isinstance(batch, list) or len(batch) != len(requested_ids)
                    or any(not isinstance(info, dict) or type(info.get("noteId")) is not int for info in batch)
                    or {info["noteId"] for info in batch} != set(requested_ids)):
                raise ValueError("AnkiConnect notesInfo result must cover all requested note IDs; retry preview")
            note_infos.extend(batch)
        existing_by_front: dict[str, list[dict[str, object]]] = {}
        for info in note_infos:
            if info.get("modelName") != "Basic":
                raise ValueError("AnkiConnect note type changed during preview; retry")
            fields = info.get("fields")
            if not isinstance(fields, dict) or not isinstance(fields.get("Front"), dict) or not isinstance(fields.get("Back"), dict):
                raise ValueError("AnkiConnect Basic note is missing Front/Back field values")
            front = fields["Front"].get("value")
            back = fields["Back"].get("value")
            if not isinstance(front, str) or not isinstance(back, str):
                raise ValueError("AnkiConnect Basic note fields must contain string values")
            existing_by_front.setdefault(_anki_plain_text(front), []).append({
                "note_id": info["noteId"], "front": front, "back": back,
            })
        for card in cards:
            # Draft sides are plain text with line breaks; never interpret them as HTML.
            front = _anki_plain_text(html.escape(card["front"]))
            back = _anki_plain_text(html.escape(card["back"]))
            matches = existing_by_front.get(front, [])
            reason = ""
            if any(status in ("conflicting", "superseded") for status in card["evidence_statuses"].values()):
                status, reason = "skipped", "linked evidence is conflicting or superseded; review it first"
            elif matches and all(_anki_plain_text(item["back"]) == back for item in matches):
                status = "already_present"
            elif matches:
                status = "conflict"
            else:
                status = "proposed_addition"
            previews.append({
                "card_id": card["card_id"], "deck": deck, "status": status, "reason": reason,
                "deck_scope": "selected deck and its subdecks (Anki search semantics)",
                "model": "Basic", "front": card["front"], "back": card["back"],
                "notes": card["notes"], "evidence": card["evidence_statuses"], "sources": card["sources"],
                "matches": matches, "read_only": True,
            })
    return previews


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="learnbase", description="Offline tools for a learnBase workspace")
    parser.add_argument("--workspace", type=Path, default=Path("."), help="workspace root (default: current directory)")
    commands = parser.add_subparsers(dest="command", required=True)
    setup = commands.add_parser("setup", help="initialize or safely update local workspace state")
    setup.add_argument("--name", help="set the workspace name; omitted names are preserved on rerun")
    topic = commands.add_parser("topic", help="manage topics")
    topic_commands = topic.add_subparsers(dest="topic_command", required=True)
    topic_add = topic_commands.add_parser("add")
    topic_add.add_argument("slug")
    topic_add.add_argument("--name", required=True)
    topic_add.add_argument("--parent")
    topic_onboard = topic_commands.add_parser("onboard", help="save an approved topic proposal")
    topic_onboard.add_argument("--proposal", required=True, help="JSON proposal path, or '-' to read stdin")
    topic_onboard.add_argument("--approved", action="store_true", help="confirm learner approval was obtained")
    review = commands.add_parser("review", help="record learner-reviewed activities and evidence")
    review_commands = review.add_subparsers(dest="review_command", required=True)
    review_add = review_commands.add_parser("add", help="save a reviewed activity proposal")
    review_add.add_argument("--proposal", required=True, help="JSON proposal path, or '-' to read stdin")
    review_add.add_argument("--approved", action="store_true", help="confirm learner approval was obtained")
    review_evidence = review_commands.add_parser("evidence")
    evidence_commands = review_evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_status = evidence_commands.add_parser("status", help="append an approved evidence status transition")
    evidence_status.add_argument("--proposal", required=True, help="JSON proposal path, or '-' to read stdin")
    evidence_status.add_argument("--approved", action="store_true", help="confirm learner approval was obtained")
    source = commands.add_parser("source", help="register a source")
    source_commands = source.add_subparsers(dest="source_kind", required=True)
    source_add = source_commands.add_parser("add")
    source_types = source_add.add_subparsers(dest="kind", required=True)
    for kind in ("pdf", "web"):
        source_type = source_types.add_parser(kind)
        source_type.add_argument("--title", required=True)
        source_type.add_argument("--topic", action="append", required=True)
        source_type.add_argument("--path" if kind == "pdf" else "--url", required=True)
    note = commands.add_parser("note", help="create or validate a knowledge note")
    note_commands = note.add_subparsers(dest="note_command", required=True)
    note_new = note_commands.add_parser("new")
    note_new.add_argument("--title", required=True)
    note_new.add_argument("--topic", action="append", required=True)
    note_new.add_argument("--source", action="append", required=True)
    note_new.add_argument("--locator", action="append", default=[], help="citation position as SOURCE-ID=page/section")
    note_validate = note_commands.add_parser("validate")
    note_validate.add_argument("path")
    card = commands.add_parser("card", help="manage local flashcard drafts")
    card_commands = card.add_subparsers(dest="card_command", required=True)
    card_draft = card_commands.add_parser("draft")
    card_draft_commands = card_draft.add_subparsers(dest="card_draft_command", required=True)
    card_save = card_draft_commands.add_parser("save", help="save a learner-approved draft proposal")
    card_save.add_argument("--proposal", required=True, help="JSON proposal path, or '-' to read stdin")
    card_save.add_argument("--approved", action="store_true", help="confirm learner approval was obtained")
    card_validate = card_draft_commands.add_parser("validate", help="validate draft file and local provenance")
    card_validate.add_argument("path")
    card_list = card_draft_commands.add_parser("list", help="list validated drafts")
    card_list.add_argument("--topic", help="limit to one topic ID")
    anki = commands.add_parser("anki", help="inspect and preview against an existing Anki collection")
    anki_commands = anki.add_subparsers(dest="anki_command", required=True)
    anki_commands.add_parser("decks", help="list existing Anki decks (read only)")
    anki_map = anki_commands.add_parser("map", help="manage local topic-to-existing-deck mappings")
    anki_map_commands = anki_map.add_subparsers(dest="anki_map_command", required=True)
    anki_map_add = anki_map_commands.add_parser("add")
    anki_map_add.add_argument("--topic", required=True)
    anki_map_add.add_argument("--deck", required=True)
    anki_map_list = anki_map_commands.add_parser("list")
    anki_map_list.add_argument("--topic")
    anki_map_remove = anki_map_commands.add_parser("remove")
    anki_map_remove.add_argument("--topic", required=True)
    anki_map_remove.add_argument("--deck", required=True)
    anki_preview = anki_commands.add_parser("preview", help="compare local drafts with existing Anki Basic notes")
    anki_preview.add_argument("--topic", required=True)
    anki_preview.add_argument("--deck", help="preview one existing deck instead of mapped decks")
    profile = commands.add_parser("profile", help="configure or inspect an evidence-backed profile")
    profile_commands = profile.add_subparsers(dest="profile_command", required=True)
    profile_dimension = profile_commands.add_parser("dimension")
    profile_dimension_commands = profile_dimension.add_subparsers(dest="dimension_command", required=True)
    dimension_set = profile_dimension_commands.add_parser("set", help="save a learner-approved topic dimension")
    dimension_set.add_argument("--proposal", required=True, help="JSON proposal path, or '-' to read stdin")
    dimension_set.add_argument("--approved", action="store_true", help="confirm learner approval was obtained")
    profile_show = profile_commands.add_parser("show", help="render a read-only profile summary")
    profile_show.add_argument("--topic", help="limit output to one topic")
    profile_show.add_argument("--as-of", help="UTC ISO-8601 projection time; defaults to current time")
    profile_report = profile_commands.add_parser("report", help="write a generated Markdown profile report")
    profile_report.add_argument("--topic", help="limit output to one topic")
    profile_report.add_argument("--as-of", help="UTC ISO-8601 projection time; defaults to current time")
    profile_report.add_argument("--output", required=True, help="generated report path inside reports/")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = args.workspace.resolve()
    try:
        if args.command == "setup":
            setup_workspace(root, args.name)
        elif args.command == "topic" and args.topic_command == "add":
            add_topic(root, args.slug, args.name, args.parent)
        elif args.command == "topic" and args.topic_command == "onboard":
            if not args.approved:
                raise ValueError("topic proposal was not saved; obtain learner approval before passing --approved")
            if args.proposal == "-":
                proposal = json.load(sys.stdin)
            else:
                with Path(args.proposal).open("r", encoding="utf-8") as proposal_file:
                    proposal = json.load(proposal_file)
            save_topic_proposal(root, proposal, approved=True)
        elif args.command == "review" and args.review_command == "add":
            if args.proposal == "-":
                proposal = json.load(sys.stdin)
            else:
                with Path(args.proposal).open("r", encoding="utf-8") as proposal_file:
                    proposal = json.load(proposal_file)
            save_review_proposal(root, proposal, approved=args.approved)
        elif args.command == "review" and args.review_command == "evidence" and args.evidence_command == "status":
            if args.proposal == "-":
                proposal = json.load(sys.stdin)
            else:
                with Path(args.proposal).open("r", encoding="utf-8") as proposal_file:
                    proposal = json.load(proposal_file)
            save_evidence_status(root, proposal, approved=args.approved)
        elif args.command == "profile" and args.profile_command == "dimension" and args.dimension_command == "set":
            if args.proposal == "-":
                proposal = json.load(sys.stdin)
            else:
                with Path(args.proposal).open("r", encoding="utf-8") as proposal_file:
                    proposal = json.load(proposal_file)
            save_profile_dimension(root, proposal, approved=args.approved)
        elif args.command == "profile" and args.profile_command == "show":
            print(render_profile(root, args.topic, args.as_of))
        elif args.command == "profile" and args.profile_command == "report":
            report = render_profile(root, args.topic, args.as_of)
            write_profile_report(root, report, args.output)
        elif args.command == "source":
            locator = getattr(args, "path", None) or getattr(args, "url", None)
            add_source(root, args.kind, args.title, locator, args.topic)
        elif args.command == "note" and args.note_command == "new":
            create_note(root, args.title, args.topic, args.source, args.locator)
        elif args.command == "note" and args.note_command == "validate":
            validate_note(root, args.path)
        elif args.command == "card" and args.card_command == "draft" and args.card_draft_command == "save":
            if args.proposal == "-":
                proposal = json.load(sys.stdin)
            else:
                with Path(args.proposal).open("r", encoding="utf-8") as proposal_file:
                    proposal = json.load(proposal_file)
            save_card_proposal(root, proposal, approved=args.approved)
        elif args.command == "card" and args.card_command == "draft" and args.card_draft_command == "validate":
            validate_card(root, args.path)
        elif args.command == "card" and args.card_command == "draft" and args.card_draft_command == "list":
            for card_row in list_cards(root, args.topic):
                print(f"{card_row['card_id']}\t{card_row['topic_id']}\t{card_row['objective_key']}\t{card_row['path']}")
        elif args.command == "anki" and args.anki_command == "decks":
            for deck in anki_decks(root):
                print(deck)
        elif args.command == "anki" and args.anki_command == "map" and args.anki_map_command == "add":
            add_anki_mapping(root, args.topic, args.deck)
        elif args.command == "anki" and args.anki_command == "map" and args.anki_map_command == "list":
            for mapping in list_anki_mappings(root, args.topic):
                print(f"{mapping['topic_id']}\t{mapping['deck_name']}")
        elif args.command == "anki" and args.anki_command == "map" and args.anki_map_command == "remove":
            remove_anki_mapping(root, args.topic, args.deck)
        elif args.command == "anki" and args.anki_command == "preview":
            print(json.dumps(preview_anki(root, args.topic, args.deck), ensure_ascii=False, indent=2))
        return 0
    except (OSError, sqlite3.Error, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
