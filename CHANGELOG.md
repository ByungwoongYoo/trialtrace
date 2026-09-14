# Changelog

This project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- Parsed content-security-policy directives in the regression test so CodeQL does not mistake an assertion for URL sanitization.

## [0.1.2] - 2026-09-14

### Security

- Added browser security headers and regression tests for injection-shaped identifiers.
- Expanded CodeQL analysis to the Python service and browser JavaScript, with workflow actions pinned to immutable upstream release commits.
- Documented the project's threat boundaries, common vulnerability classes, reporting process, and release security checks.

### Changed

- Added automated package builds, installed-wheel smoke tests, formatting checks, dependency consistency checks, and branch coverage to CI.
- Bundled the frozen derived corpus in the installation package so a wheel installation can start without a source checkout.
- Added project usage, API, architecture, testing, security, and release documentation.

### Fixed

- Preserved the archived CRLF bytes of `version_counts.csv` so its declared SHA-256 remains identical on every Git checkout.

## [0.1.1] - 2026-09-14

### Changed

- Updated the Python build, runtime, lint, security, and dependency-audit toolchain to current compatible releases.
- Updated GitHub Actions to supported releases and explicitly upgraded `setuptools` before dependency auditing.

## [0.1.0] - 2026-09-14

### Added

- Deterministic SQLite builder with frozen SHA-256 and count validation.
- Read-only FastAPI endpoints for trial summaries, timelines, changes, and provenance.
- Static NCT search interface with official ClinicalTrials.gov history links.
- Frozen derived tables for 400 trials and 5,629 transitions.
- Reduced provenance manifest for 400 history indexes and 6,029 versions.
- Automated API, database, provenance-boundary, and validation tests.
- Initial public repository structure and automated security checks.

[Unreleased]: https://github.com/ByungwoongYoo/trialtrace/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/ByungwoongYoo/trialtrace/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/ByungwoongYoo/trialtrace/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ByungwoongYoo/trialtrace/tree/v0.1.0
