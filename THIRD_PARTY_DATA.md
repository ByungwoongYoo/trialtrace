# Third-party data boundary

TrialTrace was derived from public ClinicalTrials.gov record-history material. ClinicalTrials.gov is operated by the U.S. National Library of Medicine. The official service and its current terms and notices govern use of its records.

This repository does not contain the raw ClinicalTrials.gov study records or raw record-history payload archive. It also omits the private reconstruction manifest's archive paths and undocumented retrieval endpoints. Public responses link to stable study history pages in the form `https://clinicaltrials.gov/study/{NCT_ID}?tab=history`.

The CC BY 4.0 grant in `LICENSE-DATA` applies only to Byungwoong Yoo's derived tables, reduced provenance table, and repository documentation. It does not assert ownership of or relicense the underlying ClinicalTrials.gov records. Users who retrieve source records should review the [ClinicalTrials.gov terms and conditions](https://clinicaltrials.gov/about-site/terms-conditions) and cite the service as requested there.

The reduced manifest contains canonical payload hashes solely to identify the material used in the frozen reconstruction. A hash is provenance metadata; the underlying payload is not included.
