"""Authentication helpers for SOAP (ssid-based) and REST (Bearer token)."""
import hmac
import random
import string

from .api import ApiError


class SoapSession:
    """Holds the SOAP login state.

    On login, validates username/password and issues a fresh 32-char alphanumeric ssid.
    Only the most recently issued ssid is valid (re-login invalidates prior ones).
    """

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self._ssid: str | None = None

    def login(self, login: str, password: str) -> str:
        if login != self._username or password != self._password:
            self._ssid = None
            raise ApiError(500, 104, "Incorrect login or password")
        self._ssid = "".join(
            random.SystemRandom().choice(string.digits + string.ascii_lowercase)
            for _ in range(32)
        )
        return self._ssid

    def validate(self, ssid: str) -> None:
        if self._ssid is None or ssid != self._ssid:
            raise ApiError(500, 101, "You are not logged")


class BearerAuth:
    """Validates an HTTP `Authorization: Bearer <token>` header against a configured token."""

    def __init__(self, token: str) -> None:
        self._token = token

    def validate(self, header: str | None) -> None:
        if not header:
            raise ApiError(500, 104, "Incorrect authorization token")
        parts = header.split(None, 1)
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise ApiError(500, 104, "Incorrect authorization token")
        if not hmac.compare_digest(parts[1], self._token):
            raise ApiError(500, 104, "Incorrect authorization token")
