# Data files

This directory contains the frozen, author-created tables used by TrialTrace and a reduced provenance record.

| File | Rows | Purpose |
| --- | ---: | --- |
| `raw_event_ledger.csv` | 5,629 | One derived transition per row |
| `raw_trial_anchors.csv` | 400 | One trial anchor per row |
| `provenance/retrieval_manifest_reduced.csv` | 6,429 | 400 history-index records and 6,029 version records |
| `provenance/version_counts.csv` | 400 | Retrieved version count by NCT identifier |
| `provenance/download_summary.json` | n/a | Aggregate retrieval summary |
| `SHA256SUMS` | n/a | Frozen SHA-256 values enforced by the database builder |

`retrieval_manifest_reduced.csv` retains only the source identifier, version, retrieval time, canonical payload SHA-256, record type, and stable public record-history link. It excludes the raw archive path and undocumented retrieval endpoint from the private analysis manifest.

The author-created derived tables and documentation are licensed under CC BY 4.0 as described in [`LICENSE-DATA`](../../../LICENSE-DATA). Raw ClinicalTrials.gov records and history payloads are excluded from this repository and from that license grant. See [`THIRD_PARTY_DATA.md`](../../../THIRD_PARTY_DATA.md).
