# Contributing

TrialTrace welcomes focused fixes to its code, tests, documentation, and public derived-data checks.

1. Open an issue before a large change so its scope and data boundary are clear.
2. Fork the repository and create a short branch from `main`.
3. Install the test dependencies with `python -m pip install -e ".[test]"`.
4. Run `python scripts/build_db.py` and `pytest`.
5. Open a pull request that states the trigger, resulting behavior, validation performed, and any data or license effect.

Do not add raw ClinicalTrials.gov history payloads, private archive paths, undocumented internal API URLs, participant-level information, contact details, credentials, or secrets. New derived data must identify its source, retrieval date, transformation, license boundary, and deterministic validation rule.

Major new functionality must include automated tests. Tests should detect a meaningful failure rather than restating the implementation. Keep the API backward compatible within a minor release, or explain the breaking change and update `CHANGELOG.md`.

By participating, contributors agree to follow `CODE_OF_CONDUCT.md`. Contributions are accepted under the repository's existing licenses: MIT for code and CC BY 4.0 for author-created derived data and documentation, unless a file clearly states otherwise.
