"""Regression: SOAP wire shape and WSDL output must match pre-refactor behavior."""
import os
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from subregsim.api import Api
from subregsim.auth import SoapSession
from subregsim.soap import build_spyne_wsgi

GOLDEN_WSDL = Path(__file__).parent / "wsdl_golden.xml"


@pytest.fixture
def wsgi_app():
    api = Api(["example.com"])
    session = SoapSession("user", "pass")
    app = build_spyne_wsgi(api, session, "http://127.0.0.1:18080/")
    yield app, api, session


def _call(wsgi_app, method, path, body=b"", content_type="text/xml; charset=utf-8"):
    """Invoke the WSGI app directly with a synthesized environ. Returns (status, headers, body_bytes)."""
    import io
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
        captured["headers"] = headers
    result = wsgi_app(environ, start_response)
    body_bytes = b"".join(result)
    if hasattr(result, "close"):
        result.close()
    return captured["status"], captured["headers"], body_bytes


def test_wsdl_byte_identical(wsgi_app):
    app, _, _ = wsgi_app
    status, _, body = _call(app, "GET", "/wsdl")
    assert status.startswith("200")
    expected = GOLDEN_WSDL.read_bytes()
    # Normalize possible CRLF differences if the golden was captured under Windows
    actual = body.replace(b"\r\n", b"\n")
    expected_norm = expected.replace(b"\r\n", b"\n")
    assert actual == expected_norm, "WSDL output differs from golden — Spyne service signature changed"


def _login_envelope(login: str, password: str) -> bytes:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:t="http://subreg.cz/types">
  <soapenv:Body>
    <t:Login>
      <t:login>{login}</t:login>
      <t:password>{password}</t:password>
    </t:Login>
  </soapenv:Body>
</soapenv:Envelope>'''.encode("utf-8")


def _get_dns_zone_envelope(ssid: str, domain: str) -> bytes:
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:t="http://subreg.cz/types">
  <soapenv:Body>
    <t:Get_DNS_Zone>
      <t:ssid>{ssid}</t:ssid>
      <t:domain>{domain}</t:domain>
    </t:Get_DNS_Zone>
  </soapenv:Body>
</soapenv:Envelope>'''.encode("utf-8")


def test_login_success(wsgi_app):
    app, _, _ = wsgi_app
    body = _login_envelope("user", "pass")
    status, _, resp = _call(app, "POST", "/", body)
    assert status.startswith("200"), resp
    text = resp.decode("utf-8")
    assert re.search(r"<\w+:status>ok</\w+:status>", text)
    assert re.search(r"<\w+:ssid>", text)


def test_login_failure_emits_500_104(wsgi_app):
    app, _, _ = wsgi_app
    body = _login_envelope("user", "wrong")
    _, _, resp = _call(app, "POST", "/", body)
    text = resp.decode("utf-8")
    assert re.search(r"<\w+:status>error</\w+:status>", text)
    assert re.search(r"<\w+:major>500</\w+:major>", text)
    assert re.search(r"<\w+:minor>104</\w+:minor>", text)


def test_get_dns_zone_after_login(wsgi_app):
    app, _, _ = wsgi_app
    login_body = _login_envelope("user", "pass")
    _, _, login_resp = _call(app, "POST", "/", login_body)
    match = re.search(r"<\w+:ssid>([a-z0-9]{32})</\w+:ssid>", login_resp.decode("utf-8"))
    assert match, login_resp
    ssid = match.group(1)
    body = _get_dns_zone_envelope(ssid, "example.com")
    _, _, resp = _call(app, "POST", "/", body)
    text = resp.decode("utf-8")
    assert re.search(r"<\w+:status>ok</\w+:status>", text)
    assert re.search(r"<\w+:domain>example.com</\w+:domain>", text)
