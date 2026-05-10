"""Tests for the REST surface (Flask test client)."""
import json


def test_unauthenticated_request_returns_401(client):
    resp = client.get("/domains")
    assert resp.status_code == 401
    body = resp.get_json()
    assert body == {
        "error": "Incorrect authorization token",
        "code_major": 500,
        "code_minor": 104,
    }


def test_wrong_bearer_returns_401(client):
    resp = client.get("/domains", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401


def test_non_bearer_scheme_returns_401(client):
    resp = client.get("/domains", headers={"Authorization": "Basic foo"})
    assert resp.status_code == 401


def test_correct_bearer_lets_request_through(client):
    resp = client.get("/domains", headers={"Authorization": "Bearer secret-token"})
    assert resp.status_code == 200


def test_get_dns_zone_unknown_domain_returns_400(client):
    resp = client.get(
        "/dns/not-configured.tld",
        headers={"Authorization": "Bearer secret-token"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code_major"] == 524
    assert body["code_minor"] == 1009


def test_get_dns_zone_empty(client, api):
    resp = client.get(
        "/dns/example.com",
        headers={"Authorization": "Bearer secret-token"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body == {"domain": "example.com", "records": []}


def test_get_dns_zone_returns_records(client, api):
    api.add_dns_record("example.com", {"name": "www", "type": "A", "content": "1.2.3.4"})
    resp = client.get(
        "/dns/example.com",
        headers={"Authorization": "Bearer secret-token"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["domain"] == "example.com"
    assert len(body["records"]) == 1
    rec = body["records"][0]
    assert rec["name"] == "www"
    assert rec["type"] == "A"
    assert rec["content"] == "1.2.3.4"
    assert rec["id"].isdigit()  # IDs must be stringified at the REST boundary
    assert rec["ttl"] == 600
    assert rec["prio"] == 0
