# API reference

The FastAPI application exposes JSON endpoints under `/api` and interactive OpenAPI documentation at `/docs`. All endpoints are read-only.

## Trial identifier

`nct_id` is case-insensitive on input and is normalized to uppercase. It must match the allowlist pattern `NCT` followed by exactly eight digits. An invalid value returns HTTP 422. A valid identifier outside the frozen corpus returns HTTP 404 with `detail.code` set to `trial_not_found`.

## Endpoints

### `GET /api/trials/{nct_id}`

Returns the trial anchor, corpus coverage counts, first-results fields, transition counts, and an official ClinicalTrials.gov history URL.

### `GET /api/trials/{nct_id}/timeline`

Returns ordered derived transitions. The optional integer query parameter `version` must be zero or greater. A version absent from a known trial returns HTTP 404 with `detail.code` set to `version_not_found`.

### `GET /api/trials/{nct_id}/changes`

Returns only transitions that contain tracked changed fields. It accepts the same `version` filter and error behavior as the timeline endpoint.

### `GET /api/provenance`

Returns corpus counts, input SHA-256 values, the recorded retrieval window, source locations, license boundaries, and interpretation limits.

### `GET /healthz`

Returns `status`, the package `version`, and the number of loaded `trials`.

## Output boundary

Responses can contain public derived values, normalized labels, hashes, and official source URLs. They do not expose raw ClinicalTrials.gov history payloads, local archive paths, credentials, participant-level data, or undocumented internal API URLs. The OpenAPI document at `/openapi.json` is the machine-readable contract.
