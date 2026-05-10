"""Integration tests for the WSGI dispatcher (Spyne + Flask on one listener)."""
import io
import pytest

from subregsim.api import Api
from subregsim.auth import BearerAuth, SoapSession
from subregsim.server import build_wsgi_app


@pytest.fixture
def wsgi_app():
    api = Api(["example.com"])
    session = SoapSession("user", "pass")
    bearer = BearerAuth("secret-token")
    return build_wsgi_app(api, session, bearer, service_url="http://localhost/")


def _call(app, method, path, body=b"", content_type="application/json"):
    environ = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "SERVER_NAME": "localhost",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "HTTP_HOST": "localhost",
        "wsgi.input": io.BytesIO(body),
        "wsgi.errors": io.BytesIO(),
        "wsgi.url_scheme": "http",
        "wsgi.multithread": False,
        "wsgi.multiprocess": False,
        "wsgi.run_once": False,
        "wsgi.version": (1, 0),
        "CONTENT_TYPE": content_type,
        "CONTENT_LENGTH": str(len(body)),
    }
    captured = {}
    def start_response(status, headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = dict(headers)
    body_iter = app(environ, start_response)
    body_bytes = b"".join(body_iter)
    if hasattr(body_iter, "close"):
        body_iter.close()
    return captured["status"], captured["headers"], body_bytes


def test_post_root_goes_to_spyne(wsgi_app):
    envelope = b'''<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:t="http://subreg.cz/types">
  <soapenv:Body>
    <t:Login><t:login>user</t:login><t:password>pass</t:password></t:Login>
  </soapenv:Body>
</soapenv:Envelope>'''
    status, _, body = _call(wsgi_app, "POST", "/", envelope, "text/xml; charset=utf-8")
    assert status.startswith("200")
    assert b"<ssid" in body or b":ssid" in body  # tolerant of namespace prefix


def test_get_wsdl_goes_to_spyne(wsgi_app):
    status, headers, body = _call(wsgi_app, "GET", "/wsdl")
    assert status.startswith("200")
    assert b"SubregCzService" in body
    assert "xml" in headers.get("Content-Type", "").lower()


def test_get_root_goes_to_swagger_ui(wsgi_app):
    status, headers, body = _call(wsgi_app, "GET", "/")
    assert status.startswith("200")
    assert "text/html" in headers.get("Content-Type", "").lower()
    assert b"swagger" in body.lower()


def test_get_swagger_json_goes_to_flask(wsgi_app):
    status, _, body = _call(wsgi_app, "GET", "/swagger.json")
    assert status.startswith("200")
    import json
    data = json.loads(body)
    assert data["openapi"] == "3.0.0"


def test_get_domains_with_bearer_goes_to_flask(wsgi_app):
    status, _, body = _call(
        wsgi_app, "GET", "/domains",
        content_type="application/json",
    )
    # No bearer → 401 from Flask, not 404 from Spyne
    assert status.startswith("401")
