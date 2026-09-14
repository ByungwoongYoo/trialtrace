# Release process

TrialTrace follows Semantic Versioning. Every user-facing release receives a unique version in `pyproject.toml` and `src/trialtrace/__init__.py`, an annotated Git tag named `vMAJOR.MINOR.PATCH`, and a human-readable entry in `CHANGELOG.md`.

Before tagging a release, the maintainer:

1. runs the full sequence in [`TESTING.md`](TESTING.md);
2. confirms CI and CodeQL complete successfully;
3. reviews dependency-audit results and the release diff for credentials or secrets;
4. checks that documentation matches the external interface and current version;
5. records every fixed publicly known project vulnerability that already has a CVE or similar identifier; and
6. creates the annotated tag from the tested commit and pushes it to the public repository.

The source archive and Python distributions are built from the tagged commit with standard FLOSS tools. A release is withheld if a confirmed medium-or-higher project vulnerability is unresolved.
