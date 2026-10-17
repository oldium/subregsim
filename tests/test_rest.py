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


def test_create_record_returns_200_with_record_id(client, api):
    resp = client.post(
        "/dns/example.com/record",
        headers={"Authorization": "Bearer secret-token"},
        json={"name": "www", "type": "A", "content": "1.2.3.4"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["domain"] == "example.com"
    # Upstream swagger documents a string; the real API returns a number.
    assert isinstance(body["record_id"], int)
    # Confirm it landed in the api
    records = api.get_dns_zone("example.com")
    assert len(records) == 1


def test_create_record_missing_name_returns_400_524_1006(client):
    resp = client.post(
        "/dns/example.com/record",
        headers={"Authorization": "Bearer secret-token"},
        json={"type": "A", "content": "1.2.3.4"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code_major"] == 524
    assert body["code_minor"] == 1006


def test_create_cname_with_trailing_dot_returns_400_524_1001(client):
    resp = client.post(
        "/dns/example.com/record",
        headers={"Authorization": "Bearer secret-token"},
        json={"name": "www", "type": "CNAME", "content": "example.org."},
    )
    assert resp.status_code == 400
    assert resp.get_json() == {
        "error": "Invalid domain name in record",
        "code_major": 524,
        "code_minor": 1001,
    }


def test_create_record_missing_type_returns_400_524_1007(client):
    resp = client.post(
        "/dns/example.com/record",
        headers={"Authorization": "Bearer secret-token"},
        json={"name": "x", "content": "1.2.3.4"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code_major"] == 524
    assert body["code_minor"] == 1007


def test_create_record_bad_type_pattern_returns_400_524_1007(client):
    resp = client.post(
        "/dns/example.com/record",
        headers={"Authorization": "Bearer secret-token"},
        json={"name": "x", "type": "lowercase", "content": "x"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code_major"] == 524
    assert body["code_minor"] == 1007


def test_create_record_unknown_domain_returns_400_524_1009(client):
    resp = client.post(
        "/dns/not-configured.tld/record",
        headers={"Authorization": "Bearer secret-token"},
        json={"name": "x", "type": "A", "content": "1.2.3.4"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code_major"] == 524
    assert body["code_minor"] == 1009


def test_modify_record_updates_existing(client, api):
    rid = api.add_dns_record(
        "example.com", {"name": "www", "type": "A", "content": "1.2.3.4"}
    )
    resp = client.put(
        f"/dns/example.com/record/{rid}",
        headers={"Authorization": "Bearer secret-token"},
        json={"type": "A", "content": "5.6.7.8"},
    )
    assert resp.status_code == 200
    rec = api.get_dns_zone("example.com")[0]
    assert rec["content"] == "5.6.7.8"


def test_modify_record_unknown_id_returns_400_524_1003(client):
    resp = client.put(
        "/dns/example.com/record/99999",
        headers={"Authorization": "Bearer secret-token"},
        json={"type": "A", "content": "1.2.3.4"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code_major"] == 524
    assert body["code_minor"] == 1003


def test_modify_record_non_numeric_id_returns_400_524_1003(client):
    resp = client.put(
        "/dns/example.com/record/abc",
        headers={"Authorization": "Bearer secret-token"},
        json={"type": "A", "content": "1.2.3.4"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code_major"] == 524
    assert body["code_minor"] == 1003


def test_modify_record_unknown_domain_returns_400_524_1009(client):
    resp = client.put(
        "/dns/not-configured.tld/record/1",
        headers={"Authorization": "Bearer secret-token"},
        json={"type": "A", "content": "1.2.3.4"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code_major"] == 524
    assert body["code_minor"] == 1009


def test_delete_record_removes_it(client, api):
    rid = api.add_dns_record(
        "example.com", {"name": "www", "type": "A", "content": "1.2.3.4"}
    )
    resp = client.delete(
        f"/dns/example.com/record/{rid}",
        headers={"Authorization": "Bearer secret-token"},
    )
    assert resp.status_code == 200
    assert api.get_dns_zone("example.com") == []


def test_delete_record_unknown_id_returns_400_524_1003(client):
    resp = client.delete(
        "/dns/example.com/record/99999",
        headers={"Authorization": "Bearer secret-token"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code_major"] == 524
    assert body["code_minor"] == 1003


def test_delete_record_non_numeric_id_returns_400_524_1003(client):
    resp = client.delete(
        "/dns/example.com/record/abc",
        headers={"Authorization": "Bearer secret-token"},
    )
    assert resp.status_code == 400
    body = resp.get_json()
    assert body["code_major"] == 524
    assert body["code_minor"] == 1003


def test_swagger_ui_at_root_returns_html(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["Content-Type"]
    assert b"swagger" in resp.data.lower()


def test_swagger_ui_assets_served(client):
    resp = client.get("/swagger-ui-bundle.js")
    assert resp.status_code == 200
    assert "javascript" in resp.headers["Content-Type"].lower()


def test_rest_routes_take_precedence_over_swagger_ui_catchall(client):
    # /domains is a literal route; must hit our handler, not the catch-all.
    resp = client.get("/domains", headers={"Authorization": "Bearer secret-token"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert "domains" in body and "count" in body


def test_root_swagger_ui_does_not_require_bearer(client):
    # Browser users have no Bearer; the docs must be reachable anonymously.
    resp = client.get("/")
    assert resp.status_code == 200
