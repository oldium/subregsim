"""WSGI dispatcher composing the Spyne SOAP service and the Flask REST app.

Path-and-method routing:
    POST /         -> Spyne (SOAP envelope)
    GET  /wsdl     -> Spyne (WSDL)
    * everything else -> Flask (Werkzeug handles internal routing)
"""
import logging
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer

from .api import Api
from .auth import BearerAuth, SoapSession
from .rest import build_flask_app
from .soap import build_spyne_wsgi

log = logging.getLogger(__name__)


def build_wsgi_app(api: Api, session: SoapSession, bearer: BearerAuth, *, service_url: str):
    """Return a top-level WSGI callable that dispatches between Spyne and Flask."""
    spyne_app = build_spyne_wsgi(api, session, service_url)
    flask_app = build_flask_app(api, bearer)

    def dispatch(environ, start_response):
        method = environ["REQUEST_METHOD"]
        path = environ["PATH_INFO"]
        if method == "POST" and path == "/":
            return spyne_app(environ, start_response)
        if method == "GET" and path == "/wsdl":
            return spyne_app(environ, start_response)
        return flask_app(environ, start_response)

    return dispatch


class SubregsimHttpServer(ThreadingMixIn, WSGIServer):
    """Threaded WSGI server hosting the composed dispatcher."""
    daemon_threads = True

    def __init__(self, server_address, app, *, is_ssl: bool):
        WSGIServer.__init__(self, server_address, WSGIRequestHandler)
        self.is_ssl = is_ssl
        if self.is_ssl:
            self.base_environ["HTTPS"] = "yes"
        self.set_app(app)

    def handle_error(self, _request, client_address):
        if self.is_ssl:
            log.exception("HTTPS request handling from %s failed", client_address[0])
        else:
            log.exception("HTTP request handling from %s failed", client_address[0])


def build_server(host: str, port: int, url: str, api: Api,
                 session: SoapSession, bearer: BearerAuth, is_ssl: bool) -> SubregsimHttpServer:
    """Construct and return a ready-to-serve HTTP(S) server."""
    app = build_wsgi_app(api, session, bearer, service_url=url)
    return SubregsimHttpServer((host, port), app, is_ssl=is_ssl)
