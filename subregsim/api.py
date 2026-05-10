"""Subreg.cz simulator domain core (transport-agnostic).

Methods return plain Python data on success and raise `ApiError(major, minor, message)`
on failure. Both SOAP and REST adapters translate this into their wire formats.
"""
import logging
import threading
from typing import Any

log = logging.getLogger(__name__)

_VALID_RECORD_TYPES = frozenset(
    ["A", "AAAA", "CNAME", "MX", "TXT", "SPF", "SRV", "NS", "TLSA", "CAA", "SSHFP"]
)


class ApiError(Exception):
    """Raised by Api methods to signal a domain-level failure."""

    def __init__(self, major: int, minor: int, message: str) -> None:
        super().__init__(message)
        self.major = major
        self.minor = minor
        self.message = message

    def __str__(self) -> str:
        return f"ApiError({self.major}, {self.minor}): {self.message}"


class Api:
    """In-memory domain/zone store.

    Stores DNS records per configured domain, assigns incrementing integer IDs,
    and tracks a serial number for the DNS zone view. Thread-safe writes.
    """

    def __init__(self, domains: list[str]) -> None:
        self._domains = list(domains)
        self._db: dict[str, list[dict[str, Any]]] = {d: [] for d in self._domains}
        self._next_id = 1
        self._serial = 1
        self._lock = threading.Lock()

    @property
    def domains(self) -> list[str]:
        return list(self._domains)

    @property
    def serial(self) -> int:
        return self._serial

    def list_domains(self) -> list[dict[str, Any]]:
        return [
            {"name": d, "expire": "2023-10-20", "autorenew": 0} for d in self._domains
        ]

    def get_dns_zone(self, domain: str) -> list[dict[str, Any]]:
        self._require_domain(domain)
        return [dict(r) for r in self._db[domain]]

    def add_dns_record(self, domain: str, record: dict[str, Any]) -> int:
        self._require_domain(domain)
        rtype = record.get("type")
        if rtype not in _VALID_RECORD_TYPES:
            raise ApiError(524, 1007, "Unknown record type")
        if "name" not in record:
            raise ApiError(524, 1006, "Invalid domain name in record")
        with self._lock:
            if rtype == "CNAME" and any(
                r["name"] == record["name"]
                and r["type"] == "CNAME"
                and r.get("content") == record.get("content")
                for r in self._db[domain]
            ):
                raise ApiError(
                    524, 1008, "Cannot create CNAME, where another record already exists"
                )
            new_record = dict(record)
            new_record["id"] = self._next_id
            self._next_id += 1
            new_record.setdefault("ttl", 600)
            new_record.setdefault("prio", 0)
            self._db[domain].append(new_record)
            self._serial += 1
            return new_record["id"]

    def modify_dns_record(
        self, domain: str, record_id: int, record: dict[str, Any]
    ) -> None:
        self._require_domain(domain)
        if "type" in record and record["type"] not in _VALID_RECORD_TYPES:
            raise ApiError(524, 1007, "Unknown record type")
        with self._lock:
            matches = [r for r in self._db[domain] if r["id"] == record_id]
            if not matches:
                raise ApiError(524, 1003, "Record does not exist")
            matches[0].update(record)
            self._serial += 1

    def delete_dns_record(self, domain: str, record_id: int) -> None:
        self._require_domain(domain)
        with self._lock:
            before = len(self._db[domain])
            self._db[domain] = [r for r in self._db[domain] if r["id"] != record_id]
            if len(self._db[domain]) == before:
                raise ApiError(524, 1003, "Record does not exist")
            self._serial += 1

    def to_zone(self) -> str:
        lines = ["$ORIGIN .", "$TTL 1800"]
        with self._lock:
            for domain in self._domains:
                lines.append(
                    f"{domain} IN SOA ns.example.com admin.example.com "
                    f"( {self._serial} 86400 900 1209600 1800 )"
                )
                for rr in self._db[domain]:
                    name = rr["name"]
                    rtype = rr["type"]
                    content = rr.get("content", "")
                    prio = rr["prio"] if rtype == "MX" else ""
                    ttl = rr["ttl"] if rr["ttl"] != 1800 else ""
                    if rtype == "TXT":
                        content = '"{}"'.format(content.replace('"', r"\""))
                    lines.append(f"{name} {ttl} IN {rtype} {prio} {content}")
        return "\n".join(lines)

    def _require_domain(self, domain: str) -> None:
        if domain not in self._db:
            raise ApiError(524, 1009, "Invalid domain")
