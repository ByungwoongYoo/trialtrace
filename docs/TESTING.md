# Testing and change policy

Every major behavior change must include an automated regression test. Pull requests must explain the behavior under test and run the local validation sequence below.

```bash
python -m pip install -e ".[test,dev]"
python -m pip check
python -m build
ruff check .
ruff format --check .
bandit -r src scripts -ll
pip-audit --skip-editable
python scripts/build_db.py
coverage run -m pytest
coverage report --show-missing --fail-under=80
coverage json -o coverage.json
python scripts/check_branch_coverage.py coverage.json --minimum 80
```

The suite checks frozen hashes and counts, schema requirements, successful database replacement and resulting database integrity, query-only database access, known and invalid identifiers, version filters, structured errors, provenance disclosure boundaries, browser security headers, the static interface, and the OpenAPI contract. Injection-shaped identifiers are regression-tested to ensure they fail closed without changing the corpus. CI requires both 80% total coverage and 80% branch coverage; the second threshold is calculated directly from Coverage.py's JSON report.

Ruff enables every rule family and records narrow, file-scoped exceptions in `pyproject.toml`. Pytest treats warnings as errors except for one exact upstream Starlette/AnyIO deprecation. Bandit inspects Python, while CodeQL covers the Python service and browser JavaScript. `pip-audit` checks dependencies against known advisories. CI runs these checks on every push to `main` and every pull request using Python 3.11, 3.12, and 3.13. Scheduled CodeQL analysis and weekly Dependabot checks continue between releases.

CI also creates a clean virtual environment, installs the newly built wheel without an editable source-tree installation, and runs `scripts/smoke_installed_wheel.py`. This confirms that the distribution contains the frozen corpus and can build a verified database after installation.
