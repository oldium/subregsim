"""Unit tests for auth.py (SoapSession + BearerAuth)."""
import pytest

from subregsim.api import ApiError
from subregsim.auth import BearerAuth, SoapSession


class TestSoapSession:
    def test_login_with_correct_credentials_returns_ssid(self):
        session = SoapSession("alice", "secret")
        ssid = session.login("alice", "secret")
        assert isinstance(ssid, str)
        assert len(ssid) == 32
        assert ssid.isalnum()

    def test_login_with_wrong_password_raises_500_104(self):
        session = SoapSession("alice", "secret")
        with pytest.raises(ApiError) as ei:
            session.login("alice", "wrong")
        assert ei.value.major == 500
        assert ei.value.minor == 104

    def test_login_with_wrong_username_raises_500_104(self):
        session = SoapSession("alice", "secret")
        with pytest.raises(ApiError) as ei:
            session.login("bob", "secret")
        assert ei.value.major == 500
        assert ei.value.minor == 104

    def test_validate_accepts_current_ssid(self):
        session = SoapSession("alice", "secret")
        ssid = session.login("alice", "secret")
        session.validate(ssid)  # Should not raise

    def test_validate_rejects_unknown_ssid_with_500_101(self):
        session = SoapSession("alice", "secret")
        session.login("alice", "secret")
        with pytest.raises(ApiError) as ei:
            session.validate("00000000000000000000000000000000")
        assert ei.value.major == 500
        assert ei.value.minor == 101

    def test_validate_rejects_when_never_logged_in(self):
        session = SoapSession("alice", "secret")
        with pytest.raises(ApiError) as ei:
            session.validate("anything")
        assert ei.value.major == 500
        assert ei.value.minor == 101

    def test_re_login_invalidates_previous_ssid(self):
        session = SoapSession("alice", "secret")
        first = session.login("alice", "secret")
        second = session.login("alice", "secret")
        assert first != second
        session.validate(second)
        with pytest.raises(ApiError):
            session.validate(first)


class TestBearerAuth:
    def test_accepts_correct_token(self):
        auth = BearerAuth("hunter2")
        auth.validate("Bearer hunter2")  # Should not raise

    def test_rejects_missing_header(self):
        auth = BearerAuth("hunter2")
        with pytest.raises(ApiError) as ei:
            auth.validate(None)
        assert ei.value.major == 500
        assert ei.value.minor == 104

    def test_rejects_empty_header(self):
        auth = BearerAuth("hunter2")
        with pytest.raises(ApiError) as ei:
            auth.validate("")
        assert ei.value.major == 500
        assert ei.value.minor == 104

    def test_rejects_non_bearer_scheme(self):
        auth = BearerAuth("hunter2")
        with pytest.raises(ApiError) as ei:
            auth.validate("Basic dXNlcjpwYXNz")
        assert ei.value.major == 500
        assert ei.value.minor == 104

    def test_rejects_wrong_token(self):
        auth = BearerAuth("hunter2")
        with pytest.raises(ApiError) as ei:
            auth.validate("Bearer wrong")
        assert ei.value.major == 500
        assert ei.value.minor == 104

    def test_accepts_case_insensitive_scheme(self):
        auth = BearerAuth("hunter2")
        auth.validate("bearer hunter2")
        auth.validate("BEARER hunter2")
