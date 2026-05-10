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
