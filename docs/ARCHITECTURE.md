# Architecture

TrialTrace has three small layers:

1. `scripts/build_db.py` invokes the deterministic builder in `src/trialtrace/db.py`.
2. `src/trialtrace/app.py` opens the resulting SQLite database in query-only mode and serves read-only JSON endpoints.
3. `src/trialtrace/static/` provides a browser interface that calls those endpoints and links results to ClinicalTrials.gov.

The builder verifies the declared SHA-256 values, required columns, identifier agreement, corpus counts, and SQLite integrity before atomically replacing the output database. A failed validation leaves any previous database in place.

The application accepts an NCT identifier and an optional numeric version. It normalizes and validates the identifier, uses bound SQL parameters, returns a limited set of derived fields, and escapes values before inserting them into generated HTML. The database connection enables foreign keys and `query_only` mode.

The project has no account system, write endpoint, upload route, background worker, or secret store. Its external trust boundaries are the frozen files at build time, HTTP input at runtime, dependency packages during installation, and links to the official ClinicalTrials.gov site.
