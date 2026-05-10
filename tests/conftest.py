"""Shared pytest fixtures."""
import pytest

from subregsim.api import Api
from subregsim.auth import BearerAuth, SoapSession
from subregsim.rest import build_flask_app


@pytest.fixture
def api():
    return Api(["example.com", "example.net"])


@pytest.fixture
def session():
    return SoapSession("user", "pass")


@pytest.fixture
def bearer():
    return BearerAuth("secret-token")


@pytest.fixture
def flask_app(api, bearer):
    return build_flask_app(api, bearer)


@pytest.fixture
def client(flask_app):
    return flask_app.test_client()
