# Changelog

This project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

[Unreleased]: https://github.com/ByungwoongYoo/trialtrace/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/ByungwoongYoo/trialtrace/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/ByungwoongYoo/trialtrace/releases/tag/v0.1.0
