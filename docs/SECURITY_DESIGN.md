# Security design

This document records TrialTrace's current security boundaries and the controls that maintain them. It is also a study reference for maintainers; its existence alone does not certify any person's security knowledge.

## Assets and trust boundaries

TrialTrace protects the integrity of its frozen derived corpus, avoids exposing excluded source material, and keeps runtime access read-only. It accepts an NCT identifier and an optional version number over HTTP. It does not accept uploads, execute user commands, manage accounts, store passwords, or implement cryptographic keys or protocols.

The main trust boundaries are untrusted HTTP input, repository dependencies, frozen CSV inputs, browser rendering, and outbound links. ClinicalTrials.gov remains authoritative for current records.

## Secure design principles in this project

| Principle | TrialTrace application |
| --- | --- |
| Economy of mechanism | A small FastAPI application, SQLite database, and static client provide the complete runtime. |
| Fail-safe defaults | Invalid identifiers and versions are rejected; database connections are query-only; there are no write routes. |
| Complete mediation | Not applicable to the current public, read-only runtime because it has no authorization boundary. Any future protected resource must enforce authorization on every access path. |
| Open design | The code, validation rules, data boundaries, tests, and security process are public. No control depends on hiding its design. |
| Separation of privilege | Not applicable at runtime: the application exposes no privileged operation that can be authorized by one or more conditions. |
| Least privilege | CI receives read-only repository contents except for the narrow CodeQL security-events permission. Request-handling database connections are query-only; the startup builder creates the configured parent directory when needed, writes a temporary database beside the configured path, and then replaces that path. |
| Least common mechanism | The application has no shared mutable session, account, or per-user state. |
| Psychological acceptability | Errors distinguish malformed identifiers, absent trials, and absent versions without exposing internal paths. |
| Limited attack surface | There are no accounts, uploads, write endpoints, arbitrary queries, plugin execution, or shell calls. |
| Allowlist input validation | NCT identifiers must match `^NCT\d{8}$`; version filters are non-negative integers. |

## Common errors and mitigations

| Error class | Exposure and mitigation |
| --- | --- |
| SQL injection | Values use SQLite parameter binding. Injection-shaped identifiers fail the NCT allowlist before a query. |
| Cross-site scripting | The client uses `textContent` or `escapeHtml` before inserting derived values into HTML. Source URLs are generated for validated NCT identifiers. |
| Command injection | The runtime never invokes a shell or constructs a command from HTTP input. |
| Path traversal | HTTP input is not used to construct filesystem paths. Static files come from a fixed package directory. |
| Missing authentication or authorization | The service is intentionally public and read-only; it exposes no user-specific or privileged operation. |
| Dependency vulnerability | Direct dependencies are exact-pinned, checked with `pip-audit`, monitored by Dependabot, and analyzed in CI. Canonical package names are reviewed before acceptance. |
| Secret leakage | The application requires no runtime secrets. Contribution rules prohibit committing credentials or secrets. |
| Resource exhaustion | Identifiers have a fixed format, versions are non-negative, and successful queries are confined to the frozen corpus. A remotely reachable deployment needs the proxy request limits and rate limiting described in the [usage guide](USAGE.md). |
| Data disclosure | Tests enforce the reduced manifest field set, a public source URL prefix, the absence of `/api/int/`, and frozen input hashes. |

## Cryptography boundary

TrialTrace uses Python's standard SHA-256 implementation to verify file integrity. It does not implement encryption, key agreement, authentication tokens, password storage, nonce generation, or a custom cryptographic algorithm. Source delivery and repository access use GitHub HTTPS. Browser responses include a content security policy, frame denial, MIME-sniffing protection, a restrictive permissions policy, and a no-referrer policy.

## Reporting and repair

Use the private GitHub Security Advisory link in [`SECURITY.md`](../SECURITY.md). The maintainer acknowledges reports within 14 days, prioritizes critical issues immediately, and keeps confirmed medium-or-higher vulnerabilities from remaining unpatched beyond 60 days. Public release notes identify fixed publicly known project vulnerabilities that have a CVE or similar identifier.
