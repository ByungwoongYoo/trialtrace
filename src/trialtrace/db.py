"""Deterministic SQLite build for the frozen TrialTrace corpus."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import sqlite3
import tempfile
from collections import Counter
from collections.abc import Iterable
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPOSITORY_ROOT / "data"
DEFAULT_DB_PATH = REPOSITORY_ROOT / "trialtrace.db"

EXPECTED_COUNTS = {
    "trials": 400,
    "transitions": 5_629,
    "posted_transitions": 5_411,
    "first_results_transitions": 400,
    "history_indexes": 400,
    "history_versions": 6_029,
}

EXPECTED_SHA256 = {
    "raw_event_ledger.csv": "192f580c472c52159cb63e777521d362bd33fcfce321d87e3ae824907cd51ea8",
    "raw_trial_anchors.csv": "17494820e7389eca8cb135e64288c9b8516f10b388874829591ad78712250b53",
    "provenance/retrieval_manifest_reduced.csv": "14c61e0652d0f86b692ac925c7a374807f8dae39a25fc7fb02b5f2386a6b8825",
    "provenance/version_counts.csv": "cc21442d90ec9d70cfb880da9779a7b17700428b95bffae84fb346402e251d47",
}

BOOL_FIELDS = {
    "has_results_before",
    "has_results_after",
    "is_posted_state_transition",
    "historical_first_results_label_version",
    "first_results_attempt",
    "first_results_posted_transition",
    "in_first_results_episode",
    "review_not_passed",
}

CHANGE_FIELDS = {
    "primary_outcome_count_changed": "primary_outcome_count",
    "primary_measure_signature_changed": "primary_measure_signature",
    "primary_description_signature_changed": "primary_description_signature",
    "primary_timeframe_signature_changed": "primary_timeframe_signature",
    "primary_outcome_signature_changed": "primary_outcome_signature",
    "secondary_outcome_count_changed": "secondary_outcome_count",
    "secondary_outcome_signature_changed": "secondary_outcome_signature",
    "enrollment_changed": "enrollment",
    "enrollment_count_changed": "enrollment_count",
    "enrollment_type_changed": "enrollment_type",
    "enrollment_struct_signature_changed": "enrollment_struct_signature",
    "overall_status_changed": "overall_status",
    "pcd_changed": "pcd",
    "pcd_date_changed": "pcd_date",
    "pcd_type_changed": "pcd_type",
    "pcd_struct_signature_changed": "pcd_struct_signature",
}

OUTCOME_FIELDS = {
    "primary_outcome_count",
    "primary_measure_signature",
    "primary_description_signature",
    "primary_timeframe_signature",
    "primary_outcome_signature",
    "secondary_outcome_count",
    "secondary_outcome_signature",
}


class CorpusValidationError(ValueError):
    """Raised when a frozen input violates a hash, schema, or count invariant."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_bool(value: Any) -> bool:
    return str(value).strip().lower() == "true"


def as_int(value: Any) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    return int(float(str(value)))


def source_url(nct_id: str) -> str:
    return f"https://clinicaltrials.gov/study/{nct_id}?tab=history"


def _assert_fields(rows: list[dict[str, str]], required: Iterable[str], name: str) -> None:
    fields = set(rows[0]) if rows else set()
    missing = set(required) - fields
    if missing:
        raise CorpusValidationError(f"{name} is missing required fields: {sorted(missing)}")


def validate_inputs(data_dir: Path = DATA_DIR, verify_hashes: bool = True) -> dict[str, Any]:
    """Validate the frozen inputs and return parsed data plus corpus statistics."""
    paths = {name: data_dir / name for name in EXPECTED_SHA256}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise CorpusValidationError(f"Missing corpus files: {missing}")

    hashes = {name: sha256_file(path) for name, path in paths.items()}
    if verify_hashes:
        mismatches = {
            name: {"expected": EXPECTED_SHA256[name], "actual": digest}
            for name, digest in hashes.items()
            if digest != EXPECTED_SHA256[name]
        }
        if mismatches:
            raise CorpusValidationError(f"SHA-256 mismatch: {json.dumps(mismatches, sort_keys=True)}")

    ledger = read_csv(paths["raw_event_ledger.csv"])
    anchors = read_csv(paths["raw_trial_anchors.csv"])
    manifest = read_csv(paths["provenance/retrieval_manifest_reduced.csv"])
    version_counts = read_csv(paths["provenance/version_counts.csv"])

    _assert_fields(
        ledger,
        {
            "nct_id",
            "version",
            "is_posted_state_transition",
            "first_results_posted_transition",
            "history_version_date",
            "module_labels",
            "before_primary_outcome_count",
            "after_primary_outcome_count",
        },
        "raw_event_ledger.csv",
    )
    _assert_fields(anchors, {"nct_id", "history_versions", "first_results_posted_version"}, "raw_trial_anchors.csv")
    _assert_fields(
        manifest,
        {"kind", "nct_id", "retrieved_at_utc", "canonical_json_sha256", "source_url", "version"},
        "retrieval_manifest_reduced.csv",
    )
    _assert_fields(version_counts, {"nct_id", "versions"}, "version_counts.csv")

    counts = {
        "trials": len({row["nct_id"] for row in anchors}),
        "transitions": len(ledger),
        "posted_transitions": sum(as_bool(row["is_posted_state_transition"]) for row in ledger),
        "first_results_transitions": sum(as_bool(row["first_results_posted_transition"]) for row in ledger),
        "history_indexes": sum(row["kind"] == "history_index" for row in manifest),
        "history_versions": sum(row["kind"] == "version" for row in manifest),
    }
    if counts != EXPECTED_COUNTS:
        raise CorpusValidationError(f"Corpus count mismatch: expected {EXPECTED_COUNTS}, got {counts}")

    anchor_ids = {row["nct_id"] for row in anchors}
    ledger_ids = {row["nct_id"] for row in ledger}
    manifest_ids = {row["nct_id"] for row in manifest}
    if anchor_ids != ledger_ids or anchor_ids != manifest_ids:
        raise CorpusValidationError("Trial identifiers differ across anchors, ledger, and manifest")
    if len(version_counts) != EXPECTED_COUNTS["trials"]:
        raise CorpusValidationError("version_counts.csv must contain exactly one row per trial")
    if sum(int(row["versions"]) for row in version_counts) != EXPECTED_COUNTS["history_versions"]:
        raise CorpusValidationError("version_counts.csv total does not equal the manifest version count")

    manifest_kind_counts = Counter(row["kind"] for row in manifest)
    retrieved = sorted(row["retrieved_at_utc"] for row in manifest if row["retrieved_at_utc"])
    return {
        "ledger": ledger,
        "anchors": anchors,
        "manifest": manifest,
        "version_counts": version_counts,
        "counts": counts,
        "hashes": hashes,
        "manifest_kind_counts": dict(manifest_kind_counts),
        "retrieved_at_min": retrieved[0] if retrieved else None,
        "retrieved_at_max": retrieved[-1] if retrieved else None,
    }


def _change_items(row: dict[str, str]) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for flag, field in CHANGE_FIELDS.items():
        if as_bool(row.get(flag, "False")):
            changes.append(
                {
                    "field": field,
                    "before": row.get(f"before_{field}") or None,
                    "after": row.get(f"after_{field}") or None,
                }
            )
    return changes


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;
        CREATE TABLE trials (
            nct_id TEXT PRIMARY KEY CHECK (nct_id GLOB 'NCT[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
            pair_id INTEGER,
            cohort_group TEXT,
            first_results_date TEXT,
            first_results_date_source TEXT,
            first_results_posted_version INTEGER,
            pre_episode_posted_version INTEGER,
            history_versions INTEGER NOT NULL,
            posted_history_versions INTEGER NOT NULL,
            review_not_passed_versions INTEGER NOT NULL,
            source_url TEXT NOT NULL
        );

        CREATE TABLE transitions (
            id INTEGER PRIMARY KEY,
            nct_id TEXT NOT NULL REFERENCES trials(nct_id),
            version INTEGER NOT NULL,
            from_posted_version INTEGER,
            to_posted_version INTEGER,
            history_version_date TEXT,
            mixed_event_date TEXT,
            index_change_date TEXT,
            is_posted_state_transition INTEGER NOT NULL CHECK (is_posted_state_transition IN (0, 1)),
            first_results_posted_transition INTEGER NOT NULL CHECK (first_results_posted_transition IN (0, 1)),
            review_not_passed INTEGER NOT NULL CHECK (review_not_passed IN (0, 1)),
            has_results_before INTEGER NOT NULL CHECK (has_results_before IN (0, 1)),
            has_results_after INTEGER NOT NULL CHECK (has_results_after IN (0, 1)),
            module_labels_json TEXT NOT NULL,
            before_primary_outcome_count INTEGER,
            after_primary_outcome_count INTEGER,
            before_overall_status TEXT,
            after_overall_status TEXT,
            source_url TEXT NOT NULL,
            changes_json TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            UNIQUE (nct_id, version)
        );

        CREATE TABLE outcome_changes (
            id INTEGER PRIMARY KEY,
            transition_id INTEGER NOT NULL REFERENCES transitions(id) ON DELETE CASCADE,
            nct_id TEXT NOT NULL REFERENCES trials(nct_id),
            version INTEGER NOT NULL,
            field TEXT NOT NULL,
            before_value TEXT,
            after_value TEXT,
            UNIQUE (transition_id, field)
        );

        CREATE TABLE provenance (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL
        );

        CREATE INDEX idx_transitions_nct_version ON transitions(nct_id, version);
        CREATE INDEX idx_transitions_first_results ON transitions(first_results_posted_transition);
        CREATE INDEX idx_outcome_changes_nct_version ON outcome_changes(nct_id, version);
        """
    )


def build_database(
    db_path: Path | str = DEFAULT_DB_PATH,
    data_dir: Path | str = DATA_DIR,
    verify_hashes: bool = True,
) -> dict[str, Any]:
    """Build the complete SQLite database atomically and return its verified counts."""
    db_path = Path(db_path)
    data_dir = Path(data_dir)
    corpus = validate_inputs(data_dir, verify_hashes=verify_hashes)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    fd, temp_name = tempfile.mkstemp(prefix=f".{db_path.name}.", suffix=".tmp", dir=db_path.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        connection = sqlite3.connect(temp_path)
        try:
            _create_schema(connection)
            connection.executemany(
                """
                INSERT INTO trials (
                    nct_id, pair_id, cohort_group, first_results_date,
                    first_results_date_source, first_results_posted_version,
                    pre_episode_posted_version, history_versions,
                    posted_history_versions, review_not_passed_versions, source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        row["nct_id"],
                        as_int(row.get("pair_id")),
                        row.get("group") or None,
                        row.get("first_results_date") or None,
                        row.get("first_results_date_source") or None,
                        as_int(row.get("first_results_posted_version")),
                        as_int(row.get("pre_episode_posted_version")),
                        as_int(row.get("history_versions")) or 0,
                        as_int(row.get("posted_history_versions")) or 0,
                        as_int(row.get("review_not_passed_versions")) or 0,
                        source_url(row["nct_id"]),
                    )
                    for row in corpus["anchors"]
                ],
            )

            for row in corpus["ledger"]:
                changes = _change_items(row)
                cursor = connection.execute(
                    """
                    INSERT INTO transitions (
                        nct_id, version, from_posted_version, to_posted_version,
                        history_version_date, mixed_event_date, index_change_date,
                        is_posted_state_transition, first_results_posted_transition,
                        review_not_passed, has_results_before, has_results_after,
                        module_labels_json, before_primary_outcome_count,
                        after_primary_outcome_count, before_overall_status,
                        after_overall_status, source_url, changes_json, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["nct_id"],
                        as_int(row["version"]),
                        as_int(row.get("from_posted_version")),
                        as_int(row.get("to_posted_version")),
                        row.get("history_version_date") or None,
                        row.get("mixed_event_date") or None,
                        row.get("index_change_date") or None,
                        int(as_bool(row.get("is_posted_state_transition"))),
                        int(as_bool(row.get("first_results_posted_transition"))),
                        int(as_bool(row.get("review_not_passed"))),
                        int(as_bool(row.get("has_results_before"))),
                        int(as_bool(row.get("has_results_after"))),
                        json.dumps([label for label in row.get("module_labels", "").split("|") if label]),
                        as_int(row.get("before_primary_outcome_count")),
                        as_int(row.get("after_primary_outcome_count")),
                        row.get("before_overall_status") or None,
                        row.get("after_overall_status") or None,
                        source_url(row["nct_id"]),
                        json.dumps(changes, sort_keys=True),
                        json.dumps(row, sort_keys=True),
                    ),
                )
                transition_id = int(cursor.lastrowid)
                connection.executemany(
                    """
                    INSERT INTO outcome_changes (
                        transition_id, nct_id, version, field, before_value, after_value
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (
                            transition_id,
                            row["nct_id"],
                            as_int(row["version"]),
                            change["field"],
                            change["before"],
                            change["after"],
                        )
                        for change in changes
                        if change["field"] in OUTCOME_FIELDS
                    ],
                )

            provenance = {
                "corpus": corpus["counts"],
                "sha256": corpus["hashes"],
                "retrieval_window_utc": {
                    "first": corpus["retrieved_at_min"],
                    "last": corpus["retrieved_at_max"],
                },
                "sources": {
                    "current_api": "https://clinicaltrials.gov/data-api/api",
                    "record_history": "https://clinicaltrials.gov/study/{nct_id}?tab=history",
                    "archive_doi": "https://doi.org/10.5281/zenodo.22162352",
                },
                "licenses": {
                    "code": "MIT",
                    "derived_data": "CC-BY-4.0",
                    "clinicaltrials_source_notice": (
                        "The data license does not relicense ClinicalTrials.gov source records."
                    ),
                },
                "limitations": [
                    "This release contains author-created derived tables and payload hashes, not raw history records.",
                    (
                        "ClinicalTrials.gov history interfaces may change and are not part of the documented "
                        "Data API v2 contract."
                    ),
                    (
                        "The derived history corpus is frozen at its recorded retrieval timestamps and is not "
                        "live registry state."
                    ),
                    (
                        "Changes are descriptive registry-history events and do not establish causality, "
                        "noncompliance, or intent."
                    ),
                ],
            }
            connection.executemany(
                "INSERT INTO provenance (key, value_json) VALUES (?, ?)",
                [(key, json.dumps(value, sort_keys=True)) for key, value in provenance.items()],
            )
            connection.commit()

            db_counts = {
                "trials": connection.execute("SELECT COUNT(*) FROM trials").fetchone()[0],
                "transitions": connection.execute("SELECT COUNT(*) FROM transitions").fetchone()[0],
                "posted_transitions": connection.execute(
                    "SELECT COUNT(*) FROM transitions WHERE is_posted_state_transition = 1"
                ).fetchone()[0],
                "first_results_transitions": connection.execute(
                    "SELECT COUNT(*) FROM transitions WHERE first_results_posted_transition = 1"
                ).fetchone()[0],
            }
            for key in ("trials", "transitions", "posted_transitions", "first_results_transitions"):
                if db_counts[key] != EXPECTED_COUNTS[key]:
                    raise CorpusValidationError(f"SQLite count mismatch for {key}: {db_counts[key]}")
            check = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if check != "ok":
                raise CorpusValidationError(f"SQLite integrity check failed: {check}")
        finally:
            connection.close()
        os.replace(temp_path, db_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return {**corpus["counts"], "database": str(db_path), "sha256": sha256_file(db_path)}


def connect(db_path: Path | str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    connection = sqlite3.connect(Path(db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA query_only = ON")
    return connection
