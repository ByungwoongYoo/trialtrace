from __future__ import annotations

import csv
import shutil
import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from trialtrace import __version__
from trialtrace.db import (
    DATA_DIR,
    EXPECTED_COUNTS,
    CorpusValidationError,
    build_database,
    connect,
    validate_inputs,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def test_release_metadata_matches_package_version() -> None:
    citation = (REPOSITORY_ROOT / "CITATION.cff").read_text(encoding="utf-8")
    changelog = (REPOSITORY_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"version: {__version__}" in citation
    assert f"## [{__version__}]" in changelog


def test_frozen_corpus_invariants() -> None:
    corpus = validate_inputs()
    assert corpus["counts"] == EXPECTED_COUNTS


def test_reduced_manifest_has_only_public_fields() -> None:
    path = DATA_DIR / "provenance" / "retrieval_manifest_reduced.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        row = next(reader)
        fields = set(reader.fieldnames or [])
    assert fields == {
        "kind",
        "nct_id",
        "version",
        "retrieved_at_utc",
        "canonical_json_sha256",
        "source_url",
    }
    assert row["source_url"].startswith("https://clinicaltrials.gov/study/NCT")
    assert "/api/int/" not in path.read_text(encoding="utf-8")


def test_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    copied = tmp_path / "data"
    shutil.copytree(DATA_DIR, copied)
    with (copied / "raw_event_ledger.csv").open("a", encoding="utf-8") as handle:
        handle.write("\n")
    with pytest.raises(CorpusValidationError, match="SHA-256 mismatch"):
        validate_inputs(copied)


def test_database_contains_required_tables(database_path: Path) -> None:
    with closing(sqlite3.connect(database_path)) as database:
        tables = {row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"trials", "transitions", "outcome_changes", "provenance"} <= tables


def test_database_counts_match_frozen_invariants(database_path: Path) -> None:
    with closing(sqlite3.connect(database_path)) as database:
        assert database.execute("SELECT COUNT(*) FROM trials").fetchone()[0] == 400
        assert database.execute("SELECT COUNT(*) FROM transitions").fetchone()[0] == 5_629
        assert (
            database.execute("SELECT COUNT(*) FROM transitions WHERE is_posted_state_transition = 1").fetchone()[0]
            == 5_411
        )
        assert (
            database.execute("SELECT COUNT(*) FROM transitions WHERE first_results_posted_transition = 1").fetchone()[0]
            == 400
        )


def test_database_connection_is_query_only(database_path: Path) -> None:
    with closing(connect(database_path)) as database:
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            database.execute("DELETE FROM trials")


def test_build_replaces_output_atomically(tmp_path: Path) -> None:
    destination = tmp_path / "nested" / "trialtrace.db"
    destination.parent.mkdir()
    destination.write_text("old", encoding="utf-8")
    result = build_database(destination, DATA_DIR, True)
    assert result["trials"] == 400
    with closing(sqlite3.connect(destination)) as database:
        assert database.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
