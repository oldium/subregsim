"""Unit tests for the transport-agnostic api.py core."""
import pytest

from subregsim.api import ApiError


class TestApiError:
    def test_is_exception(self):
        assert issubclass(ApiError, Exception)

    def test_carries_major_minor_message(self):
        err = ApiError(524, 1009, "Invalid domain")
        assert err.major == 524
        assert err.minor == 1009
        assert err.message == "Invalid domain"

    def test_str_representation_includes_codes(self):
        err = ApiError(500, 104, "Incorrect login or password")
        assert "500" in str(err)
        assert "104" in str(err)
        assert "Incorrect login or password" in str(err)
