"""Asserts the generated /swagger.json is a structural subset of the real upstream spec."""
import json
from pathlib import Path

UPSTREAM = json.loads((Path(__file__).parent / "swagger_upstream.json").read_text(encoding="utf-8"))


def test_swagger_json_is_served(client):
    resp = client.get("/swagger.json")
    assert resp.status_code == 200
    spec = resp.get_json()
    assert spec["openapi"] == "3.0.0"
    assert "paths" in spec


def test_swagger_documents_only_five_endpoints(client):
    spec = client.get("/swagger.json").get_json()
    documented = set(spec["paths"].keys())
    expected = {
        "/domains",
        "/dns/{domain}",
        "/dns/{domain}/record",
        "/dns/{domain}/record/{id}",
    }
    assert documented == expected


def test_documented_paths_are_subset_of_upstream(client):
    spec = client.get("/swagger.json").get_json()
    for path in spec["paths"]:
        assert path in UPSTREAM["paths"], f"path {path} not in upstream swagger"


def test_documented_operations_are_subset_of_upstream(client):
    spec = client.get("/swagger.json").get_json()
    for path, ops in spec["paths"].items():
        for method in ops:
            assert method in UPSTREAM["paths"][path], (
                f"{method.upper()} {path} not in upstream swagger"
            )


def test_bearer_security_scheme_declared(client):
    spec = client.get("/swagger.json").get_json()
    schemes = spec["components"]["securitySchemes"]
    assert schemes["bearer"] == {"type": "http", "scheme": "bearer"}
    assert spec["security"] == [{"bearer": []}]


def test_error_schema_matches_upstream_shape(client):
    spec = client.get("/swagger.json").get_json()
    err = spec["components"]["schemas"]["Error"]
    upstream_err = UPSTREAM["components"]["schemas"]["Error"]
    # Required fields must match
    assert set(err["required"]) == set(upstream_err["required"])
    # Property names must match
    assert set(err["properties"]) == set(upstream_err["properties"])
