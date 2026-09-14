# Using TrialTrace

TrialTrace is a local, read-only explorer for a fixed set of 400 ClinicalTrials.gov studies. It does not query the live registry or accept data uploads.

## Install and start

Use Python 3.11 or later and a virtual environment.

```bash
git clone https://github.com/ByungwoongYoo/trialtrace.git
cd trialtrace
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[test]"
python scripts/build_db.py
uvicorn trialtrace.app:app --app-dir src
```

Open <http://127.0.0.1:8000>. Enter an identifier in the form `NCT` followed by eight digits, such as `NCT04153409`. Results show only the fields in the frozen derived corpus and link to the official record-history page.

## Verify an installation

`GET /healthz` returns the installed version and the number of loaded trials. A valid installation of this release reports 400 trials. Run `pytest` to exercise the database builder, API, static interface, error handling, and public-data boundaries.

## Deployment boundary

The documented command binds only to `127.0.0.1`. If TrialTrace is made reachable from another computer, run it under an unprivileged operating-system account and place it behind a maintained HTTPS reverse proxy with request-size limits and rate limiting. The application has no authentication, write API, or multi-user authorization model, so do not add privileged or private data without designing and reviewing those controls first.

## Limits

TrialTrace does not determine why a registry entry changed and does not establish wrongdoing, causality, or regulatory noncompliance. The bundled corpus is historical and does not replace the current ClinicalTrials.gov record.
