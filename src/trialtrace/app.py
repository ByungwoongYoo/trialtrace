"""FastAPI application for the frozen TrialTrace corpus."""

from __future__ import annotations

import json
import os
import re
from contextlib import asynccontextmanager, closing
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .db import DATA_DIR, DEFAULT_DB_PATH, build_database, connect

NCT_PATTERN = re.compile(r"^NCT\d{8}$")
STATIC_DIR = Path(__file__).with_name("static")


def normalize_nct_id(raw: str) -> str:
    nct_id = raw.strip().upper()
    if not NCT_PATTERN.fullmatch(nct_id):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_nct_id",
                "message": "NCT identifiers must use the form NCT followed by exactly eight digits.",
            },
        )
    return nct_id


def _not_found(nct_id: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "trial_not_found", "message": f"{nct_id} is not present in the frozen 400-trial corpus."},
    )


def _transition(row: Any) -> dict[str, Any]:
    return {
        "nct_id": row["nct_id"],
        "version": row["version"],
        "from_posted_version": row["from_posted_version"],
        "to_posted_version": row["to_posted_version"],
        "history_version_date": row["history_version_date"],
        "mixed_event_date": row["mixed_event_date"],
        "index_change_date": row["index_change_date"],
        "is_posted_state_transition": bool(row["is_posted_state_transition"]),
        "first_results_posted_transition": bool(row["first_results_posted_transition"]),
        "review_not_passed": bool(row["review_not_passed"]),
        "has_results_before": bool(row["has_results_before"]),
        "has_results_after": bool(row["has_results_after"]),
        "module_labels": json.loads(row["module_labels_json"]),
        "before_primary_outcome_count": row["before_primary_outcome_count"],
        "after_primary_outcome_count": row["after_primary_outcome_count"],
        "before_overall_status": row["before_overall_status"],
        "after_overall_status": row["after_overall_status"],
        "changes": json.loads(row["changes_json"]),
        "source_url": row["source_url"],
    }


def create_app(db_path: Path | str | None = None, data_dir: Path | str = DATA_DIR) -> FastAPI:
    resolved_db = Path(db_path or os.environ.get("TRIALTRACE_DB", DEFAULT_DB_PATH))
    resolved_data = Path(data_dir)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        if not resolved_db.is_file():
            build_database(resolved_db, resolved_data)
        yield

    application = FastAPI(
        title="TrialTrace",
        description="Source-linked exploration of a frozen, derived ClinicalTrials.gov history corpus.",
        version=__version__,
        lifespan=lifespan,
        license_info={"name": "MIT (code); CC BY 4.0 (derived data)"},
    )
    application.state.db_path = resolved_db
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @application.get("/healthz", tags=["service"])
    def health(request: Request) -> dict[str, Any]:
        with closing(connect(request.app.state.db_path)) as database:
            trials = database.execute("SELECT COUNT(*) FROM trials").fetchone()[0]
        return {"status": "ok", "version": __version__, "trials": trials}

    @application.get("/api/trials/{nct_id}", tags=["trials"])
    def get_trial(nct_id: str, request: Request) -> dict[str, Any]:
        normalized = normalize_nct_id(nct_id)
        with closing(connect(request.app.state.db_path)) as database:
            row = database.execute("SELECT * FROM trials WHERE nct_id = ?", (normalized,)).fetchone()
            if row is None:
                raise _not_found(normalized)
            transition_count = database.execute(
                "SELECT COUNT(*) FROM transitions WHERE nct_id = ?", (normalized,)
            ).fetchone()[0]
            changed_transition_count = database.execute(
                "SELECT COUNT(*) FROM transitions WHERE nct_id = ? AND changes_json != '[]'", (normalized,)
            ).fetchone()[0]
        return {
            "nct_id": row["nct_id"],
            "pair_id": row["pair_id"],
            "group": row["cohort_group"],
            "first_results_date": row["first_results_date"],
            "first_results_date_source": row["first_results_date_source"],
            "first_results_posted_version": row["first_results_posted_version"],
            "pre_episode_posted_version": row["pre_episode_posted_version"],
            "history_versions": row["history_versions"],
            "posted_history_versions": row["posted_history_versions"],
            "review_not_passed_versions": row["review_not_passed_versions"],
            "transition_count": transition_count,
            "changed_transition_count": changed_transition_count,
            "source_url": row["source_url"],
        }

    @application.get("/api/trials/{nct_id}/timeline", tags=["trials"])
    def get_timeline(
        nct_id: str,
        request: Request,
        version: int | None = Query(default=None, ge=0),
    ) -> dict[str, Any]:
        normalized = normalize_nct_id(nct_id)
        with closing(connect(request.app.state.db_path)) as database:
            exists = database.execute("SELECT 1 FROM trials WHERE nct_id = ?", (normalized,)).fetchone()
            if exists is None:
                raise _not_found(normalized)
            if version is None:
                rows = database.execute(
                    "SELECT * FROM transitions WHERE nct_id = ? ORDER BY version", (normalized,)
                ).fetchall()
            else:
                rows = database.execute(
                    "SELECT * FROM transitions WHERE nct_id = ? AND version = ? ORDER BY version",
                    (normalized, version),
                ).fetchall()
                if not rows:
                    raise HTTPException(
                        status_code=404,
                        detail={
                            "code": "version_not_found",
                            "message": f"Version {version} is not present for {normalized}.",
                        },
                    )
        return {"nct_id": normalized, "count": len(rows), "items": [_transition(row) for row in rows]}

    @application.get("/api/trials/{nct_id}/changes", tags=["trials"])
    def get_changes(
        nct_id: str,
        request: Request,
        version: int | None = Query(default=None, ge=0),
    ) -> dict[str, Any]:
        normalized = normalize_nct_id(nct_id)
        with closing(connect(request.app.state.db_path)) as database:
            exists = database.execute("SELECT 1 FROM trials WHERE nct_id = ?", (normalized,)).fetchone()
            if exists is None:
                raise _not_found(normalized)
            if version is None:
                rows = database.execute(
                    "SELECT * FROM transitions WHERE nct_id = ? AND changes_json != '[]' ORDER BY version",
                    (normalized,),
                ).fetchall()
            else:
                rows = database.execute(
                    """
                    SELECT * FROM transitions
                    WHERE nct_id = ? AND changes_json != '[]' AND version = ?
                    ORDER BY version
                    """,
                    (normalized, version),
                ).fetchall()
            if version is not None and not rows:
                version_exists = database.execute(
                    "SELECT 1 FROM transitions WHERE nct_id = ? AND version = ?", (normalized, version)
                ).fetchone()
                if version_exists is None:
                    raise HTTPException(
                        status_code=404,
                        detail={
                            "code": "version_not_found",
                            "message": f"Version {version} is not present for {normalized}.",
                        },
                    )
        return {"nct_id": normalized, "count": len(rows), "items": [_transition(row) for row in rows]}

    @application.get("/api/provenance", tags=["provenance"])
    def get_provenance(request: Request) -> dict[str, Any]:
        with closing(connect(request.app.state.db_path)) as database:
            rows = database.execute("SELECT key, value_json FROM provenance ORDER BY key").fetchall()
        return {row["key"]: json.loads(row["value_json"]) for row in rows}

    return application


app = create_app()
