from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from trialtrace import __version__
from trialtrace.app import create_app
from trialtrace.db import DATA_DIR


def test_home_serves_search_interface(client) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Search history" in response.text
    assert "TrialTrace" in response.text
    assert f"TrialTrace v{__version__}" in response.text
    assert "U.S. National Library of Medicine" in response.text
    assert "2026-07-30 UTC" in response.text


def test_health_reports_loaded_trial_count(client) -> None:
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": __version__, "trials": 400}


def test_startup_builds_missing_database(tmp_path) -> None:
    database_path = tmp_path / "startup" / "trialtrace.db"
    with TestClient(create_app(database_path, DATA_DIR)) as startup_client:
        response = startup_client.get("/healthz")
    assert response.json() == {"status": "ok", "version": __version__, "trials": 400}
    assert database_path.is_file()


def test_known_trial_summary(client) -> None:
    response = client.get("/api/trials/NCT04153409")
    assert response.status_code == 200
    payload = response.json()
    assert payload["nct_id"] == "NCT04153409"
    assert payload["first_results_posted_version"] == 2
    assert payload["source_url"] == "https://clinicaltrials.gov/study/NCT04153409?tab=history"


def test_lowercase_identifier_is_normalized(client) -> None:
    response = client.get("/api/trials/nct03845075")
    assert response.status_code == 200
    assert response.json()["nct_id"] == "NCT03845075"


def test_invalid_identifier_returns_structured_422(client) -> None:
    response = client.get("/api/trials/NCT123")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_nct_id"


@pytest.mark.parametrize(
    "hostile_identifier",
    [
        "NCT04153409' OR 1=1--",
        "NCT04153409; DROP TABLE trials;--",
        "<script>alert(1)</script>",
        "../../etc/passwd",
    ],
)
def test_hostile_identifiers_fail_closed_without_changing_the_corpus(client, hostile_identifier: str) -> None:
    rejected = client.get(f"/api/trials/{hostile_identifier}")
    assert rejected.status_code in {404, 422}

    health = client.get("/healthz")
    assert health.json()["trials"] == 400


def test_valid_but_absent_identifier_returns_404(client) -> None:
    response = client.get("/api/trials/NCT00000000")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "trial_not_found"


def test_timeline_is_sorted_and_source_linked(client) -> None:
    response = client.get("/api/trials/NCT04153409/timeline")
    assert response.status_code == 200
    items = response.json()["items"]
    versions = [item["version"] for item in items]
    assert versions == sorted(versions)
    assert all(item["source_url"].endswith("NCT04153409?tab=history") for item in items)


def test_timeline_version_filter_returns_exact_version(client) -> None:
    response = client.get("/api/trials/NCT04153409/timeline?version=2")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["items"][0]["first_results_posted_transition"] is True


def test_missing_timeline_version_returns_structured_404(client) -> None:
    response = client.get("/api/trials/NCT04153409/timeline?version=9999")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "version_not_found"


def test_timeline_for_absent_trial_returns_structured_404(client) -> None:
    response = client.get("/api/trials/NCT00000000/timeline")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "trial_not_found"


def test_changes_endpoint_exposes_flags_values_and_signatures(client) -> None:
    response = client.get("/api/trials/NCT04153409/changes?version=2")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    fields = {change["field"] for change in payload["items"][0]["changes"]}
    assert "primary_measure_signature" in fields
    assert "primary_outcome_signature" in fields


def test_unfiltered_changes_returns_ordered_items(client) -> None:
    response = client.get("/api/trials/NCT04153409/changes")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert [item["version"] for item in items] == sorted(item["version"] for item in items)


def test_changes_for_absent_trial_returns_structured_404(client) -> None:
    response = client.get("/api/trials/NCT00000000/changes")
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "trial_not_found"


def test_version_without_tracked_changes_returns_empty_result(client) -> None:
    timeline = client.get("/api/trials/NCT04153409/timeline").json()["items"]
    unchanged = next(item for item in timeline if not item["changes"])
    response = client.get(f"/api/trials/NCT04153409/changes?version={unchanged['version']}")
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_provenance_exposes_counts_hashes_and_stable_sources(client) -> None:
    response = client.get("/api/provenance")
    assert response.status_code == 200
    payload = response.json()
    assert payload["corpus"]["history_versions"] == 6_029
    assert payload["corpus"]["posted_transitions"] == 5_411
    serialized = response.text
    assert "clinicaltrials.gov/study/{nct_id}?tab=history" in serialized
    assert "/api/int/" not in serialized


def test_openapi_lists_public_endpoints(client) -> None:
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/api/trials/{nct_id}" in paths
    assert "/api/trials/{nct_id}/timeline" in paths
    assert "/api/trials/{nct_id}/changes" in paths
    assert "/api/provenance" in paths


def test_responses_include_browser_security_headers(client) -> None:
    response = client.get("/")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert "object-src 'none'" in response.headers["content-security-policy"]
    assert "'unsafe-inline'" not in response.headers["content-security-policy"]


def test_interactive_docs_receive_their_required_csp_sources(client) -> None:
    response = client.get("/docs")
    assert response.status_code == 200
    policy = response.headers["content-security-policy"]
    directives: dict[str, set[str]] = {}
    for directive in policy.split(";"):
        parts = directive.split()
        if parts:
            directives[parts[0]] = set(parts[1:])
    assert directives["script-src"] == {"'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net"}
