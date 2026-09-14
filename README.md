# TrialTrace

[![CI](https://github.com/ByungwoongYoo/trialtrace/actions/workflows/ci.yml/badge.svg)](https://github.com/ByungwoongYoo/trialtrace/actions/workflows/ci.yml)
[![CodeQL](https://github.com/ByungwoongYoo/trialtrace/actions/workflows/codeql.yml/badge.svg)](https://github.com/ByungwoongYoo/trialtrace/actions/workflows/codeql.yml)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/14628/badge)](https://www.bestpractices.dev/projects/14628)
[![License: MIT](https://img.shields.io/badge/code%20license-MIT-0c6d66.svg)](LICENSE)
[![Data license: CC BY 4.0](https://img.shields.io/badge/derived%20data-CC%20BY%204.0-df6b4f.svg)](LICENSE-DATA)

TrialTrace is a read-only explorer for changes reconstructed from a frozen ClinicalTrials.gov record-history corpus. Enter an NCT identifier to inspect version dates, changed modules, selected status and count fields, deterministic change flags, and hashed signatures. Each result links to the official ClinicalTrials.gov history page for verification.

The bundled release covers:

- 400 trials;
- 400 retrieved history indexes recorded in the reduced provenance manifest;
- 6,029 retrieved history versions recorded in the reduced provenance manifest;
- 5,629 reconstructed transitions;
- 5,411 publicly posted transitions; and
- 400 first-posted-results transitions.

These are corpus counts, not claims about all registered trials or current ClinicalTrials.gov records.

## Documentation

- [Use TrialTrace](docs/USAGE.md)
- [API reference](docs/API.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Testing and change policy](docs/TESTING.md)
- [Security design](docs/SECURITY_DESIGN.md)
- [Release process](docs/RELEASE_PROCESS.md)

## Run locally

TrialTrace requires Python 3.11 or later.

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

Open <http://127.0.0.1:8000>. Interactive API documentation is available at <http://127.0.0.1:8000/docs>.

The database builder validates four frozen SHA-256 values, the required CSV fields, identifier agreement across inputs, SQLite integrity, and the six corpus counts listed above. It writes the database atomically and fails without replacing an existing database if validation fails.

## API

| Endpoint | Response |
| --- | --- |
| `GET /api/trials/{nct_id}` | Trial anchor, corpus coverage, and official history link |
| `GET /api/trials/{nct_id}/timeline` | Ordered derived transitions; accepts `?version=` |
| `GET /api/trials/{nct_id}/changes` | Transitions with tracked changed fields; accepts `?version=` |
| `GET /api/provenance` | Frozen counts, input hashes, retrieval window, sources, licenses, and limitations |
| `GET /healthz` | Service and loaded-trial check |

Identifiers are case-insensitive on input and must match `NCT` followed by eight digits. A malformed identifier returns `422`; a well-formed identifier outside this corpus returns `404`. A requested version that is absent for a known trial also returns `404` with a distinct error code.

## Data and provenance

The public data files are bundled in [`src/trialtrace/data/`](src/trialtrace/data/README.md):

- `raw_event_ledger.csv`: author-created transition-level derived table;
- `raw_trial_anchors.csv`: author-created trial-level anchor table;
- `provenance/retrieval_manifest_reduced.csv`: NCT identifier, version, retrieval timestamp, canonical payload hash, and stable official history link;
- `provenance/version_counts.csv`: number of retrieved versions per trial; and
- `provenance/download_summary.json`: aggregate retrieval counts from the archived analysis.

The reduced manifest deliberately omits raw archive paths, compressed-object hashes, and undocumented internal API URLs. The raw ClinicalTrials.gov history payloads are not included. See [THIRD_PARTY_DATA.md](THIRD_PARTY_DATA.md) for the boundary between the author-created tables and third-party source records.

The underlying reproducibility archive is identified by [Zenodo DOI 10.5281/zenodo.22162352](https://doi.org/10.5281/zenodo.22162352). Current official records are available through the [ClinicalTrials.gov Data API](https://clinicaltrials.gov/data-api/api), while each TrialTrace response links to the corresponding public record-history page.

## What the fields mean

TrialTrace reports selected values already present in the derived ledger: version and event dates, posted-state flags, changed module labels, overall status, primary-outcome counts, change flags, and before/after hashed signatures. A signature indicates that normalized source content differed; it does not reproduce or paraphrase the outcome text.

This release does not infer why a registry field changed. It does not establish causality, regulatory noncompliance, strategic editing, scientific impropriety, or sponsor intent.

## Test

```bash
python -m pip install -e ".[test,dev]"
ruff check .
bandit -r src scripts -ll
pip-audit --skip-editable
python scripts/build_db.py
pytest
```

Ruff checks the Python source and repository scripts, Bandit reports medium- and high-severity Python security findings, and pip-audit checks the installed dependency set against known vulnerability advisories. The test suite then checks corpus hashes and counts, reduced-manifest disclosure boundaries, atomic database construction, required tables, read-only database access, both regression NCT identifiers, ordering and version filters, source links, structured validation errors, provenance output, the static interface, and the OpenAPI contract.

## Contributing and security

Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a change. Use [GitHub Security Advisories](https://github.com/ByungwoongYoo/trialtrace/security/advisories/new) for vulnerabilities rather than a public issue. Project decisions and maintainer responsibilities are described in [GOVERNANCE.md](GOVERNANCE.md).

## License and citation

Source code is licensed under the [MIT License](LICENSE). The bundled author-created derived tables and documentation identified in [LICENSE-DATA](LICENSE-DATA) are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). That license does not apply to, or relicense, ClinicalTrials.gov source records.

Citation metadata is provided in [CITATION.cff](CITATION.cff).
