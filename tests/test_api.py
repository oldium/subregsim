"""Unit tests for the transport-agnostic api.py core."""
import pytest
from dnslib import QTYPE, RR

from subregsim.api import Api, ApiError


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


def make_api() -> Api:
    return Api(["example.com", "example.net"])


class TestListDomains:
    def test_returns_list_of_domain_dicts(self):
        api = make_api()
        result = api.list_domains()
        assert result == [
            {"name": "example.com", "expire": "2023-10-20", "autorenew": 0},
            {"name": "example.net", "expire": "2023-10-20", "autorenew": 0},
        ]

    def test_lists_a_repeated_domain_once(self):
        api = Api(["example.com", "example.com"])
        assert [d["name"] for d in api.list_domains()] == ["example.com"]


class TestGetDnsZone:
    def test_unknown_domain_raises_524_1009(self):
        api = make_api()
        with pytest.raises(ApiError) as ei:
            api.get_dns_zone("not-configured.tld")
        assert ei.value.major == 524
        assert ei.value.minor == 1009

    def test_empty_zone_returns_empty_list(self):
        api = make_api()
        assert api.get_dns_zone("example.com") == []

    def test_returns_added_records(self):
        api = make_api()
        api.add_dns_record("example.com", {"name": "www", "type": "A", "content": "1.2.3.4"})
        records = api.get_dns_zone("example.com")
        assert len(records) == 1
        r = records[0]
        assert r["name"] == "www"
        assert r["type"] == "A"
        assert r["content"] == "1.2.3.4"
        assert r["ttl"] == 600
        assert r["prio"] == 0
        assert isinstance(r["id"], int)


class TestAddDnsRecord:
    def test_returns_new_int_id(self):
        api = make_api()
        rid = api.add_dns_record("example.com", {"name": "www", "type": "A", "content": "1.2.3.4"})
        assert isinstance(rid, int)
        assert rid >= 1

    def test_cname_content_with_trailing_dot_raises_524_1001(self):
        # Observed on the real API: "example.org." is rejected, "example.org" accepted.
        api = make_api()
        with pytest.raises(ApiError) as ei:
            api.add_dns_record(
                "example.com", {"name": "www", "type": "CNAME", "content": "example.org."}
            )
        assert (ei.value.major, ei.value.minor) == (524, 1001)
        assert ei.value.message == "Invalid domain name in record"
        assert api.get_dns_zone("example.com") == []

    def test_accepts_empty_name_for_the_apex(self):
        api = make_api()
        api.add_dns_record("example.com", {"name": "", "type": "A", "content": "1.2.3.4"})
        assert api.get_dns_zone("example.com")[0]["name"] == ""

    def test_unknown_domain_raises_524_1009(self):
        api = make_api()
        with pytest.raises(ApiError) as ei:
            api.add_dns_record("nope.tld", {"name": "x", "type": "A", "content": "1.2.3.4"})
        assert (ei.value.major, ei.value.minor) == (524, 1009)

    def test_unknown_type_raises_524_1007(self):
        api = make_api()
        with pytest.raises(ApiError) as ei:
            api.add_dns_record("example.com", {"name": "x", "type": "ZZZ", "content": "x"})
        assert (ei.value.major, ei.value.minor) == (524, 1007)

    def test_missing_name_raises_524_1006(self):
        api = make_api()
        with pytest.raises(ApiError) as ei:
            api.add_dns_record("example.com", {"type": "A", "content": "1.2.3.4"})
        assert (ei.value.major, ei.value.minor) == (524, 1006)

    def test_duplicate_cname_raises_524_1008(self):
        api = make_api()
        api.add_dns_record(
            "example.com", {"name": "alias", "type": "CNAME", "content": "target.example.com"}
        )
        with pytest.raises(ApiError) as ei:
            api.add_dns_record(
                "example.com", {"name": "alias", "type": "CNAME", "content": "target.example.com"}
            )
        assert (ei.value.major, ei.value.minor) == (524, 1008)

    def test_defaults_ttl_600_and_prio_0(self):
        api = make_api()
        api.add_dns_record("example.com", {"name": "a", "type": "A", "content": "1.2.3.4"})
        rec = api.get_dns_zone("example.com")[0]
        assert rec["ttl"] == 600
        assert rec["prio"] == 0

    def test_increments_serial(self):
        api = make_api()
        before = api.serial
        api.add_dns_record("example.com", {"name": "a", "type": "A", "content": "1.2.3.4"})
        assert api.serial == before + 1


class TestModifyDnsRecord:
    def test_modifies_existing_record(self):
        api = make_api()
        rid = api.add_dns_record(
            "example.com", {"name": "www", "type": "A", "content": "1.2.3.4"}
        )
        api.modify_dns_record("example.com", rid, {"content": "5.6.7.8"})
        rec = api.get_dns_zone("example.com")[0]
        assert rec["content"] == "5.6.7.8"

    def test_cname_content_with_trailing_dot_raises_524_1001(self):
        api = make_api()
        rid = api.add_dns_record(
            "example.com", {"name": "www", "type": "CNAME", "content": "example.org"}
        )
        with pytest.raises(ApiError) as ei:
            api.modify_dns_record("example.com", rid, {"type": "CNAME", "content": "example.net."})
        assert (ei.value.major, ei.value.minor) == (524, 1001)
        assert api.get_dns_zone("example.com")[0]["content"] == "example.org"

    def test_unknown_id_raises_524_1003(self):
        api = make_api()
        with pytest.raises(ApiError) as ei:
            api.modify_dns_record("example.com", 9999, {"content": "x"})
        assert (ei.value.major, ei.value.minor) == (524, 1003)

    def test_unknown_domain_raises_524_1009(self):
        api = make_api()
        with pytest.raises(ApiError) as ei:
            api.modify_dns_record("nope.tld", 1, {"content": "x"})
        assert (ei.value.major, ei.value.minor) == (524, 1009)

    def test_unknown_type_raises_524_1007(self):
        api = make_api()
        rid = api.add_dns_record(
            "example.com", {"name": "www", "type": "A", "content": "1.2.3.4"}
        )
        with pytest.raises(ApiError) as ei:
            api.modify_dns_record("example.com", rid, {"type": "ZZZ"})
        assert (ei.value.major, ei.value.minor) == (524, 1007)


class TestDeleteDnsRecord:
    def test_deletes_existing_record(self):
        api = make_api()
        rid = api.add_dns_record(
            "example.com", {"name": "www", "type": "A", "content": "1.2.3.4"}
        )
        api.delete_dns_record("example.com", rid)
        assert api.get_dns_zone("example.com") == []

    def test_unknown_id_raises_524_1003(self):
        api = make_api()
        with pytest.raises(ApiError) as ei:
            api.delete_dns_record("example.com", 9999)
        assert (ei.value.major, ei.value.minor) == (524, 1003)

    def test_unknown_domain_raises_524_1009(self):
        api = make_api()
        with pytest.raises(ApiError) as ei:
            api.delete_dns_record("nope.tld", 1)
        assert (ei.value.major, ei.value.minor) == (524, 1009)


class TestToZone:
    def test_emits_origin_and_ttl(self):
        api = make_api()
        zone = api.to_zone()
        assert "$ORIGIN ." in zone
        assert "$TTL 1800" in zone
        assert "example.com IN SOA" in zone

    def test_emits_added_record(self):
        api = make_api()
        api.add_dns_record("example.com", {"name": "www", "type": "A", "content": "1.2.3.4"})
        zone = api.to_zone()
        assert "www" in zone
        assert "IN A" in zone
        assert "1.2.3.4" in zone

    def test_record_owner_is_fully_qualified(self):
        api = make_api()
        api.add_dns_record("example.com", {"name": "www", "type": "A", "content": "1.2.3.4"})
        owners = {(str(rr.rname), QTYPE[rr.rtype]) for rr in RR.fromZone(api.to_zone())}
        assert ("www.example.com.", "A") in owners

    def test_apex_record_owner_is_the_domain(self):
        # An empty zone-file owner would mean "same as the previous record".
        api = make_api()
        api.add_dns_record("example.com", {"name": "www", "type": "A", "content": "1.2.3.4"})
        api.add_dns_record("example.com", {"name": "", "type": "A", "content": "5.6.7.8"})
        owners = {
            (str(rr.rname), QTYPE[rr.rtype], str(rr.rdata)) for rr in RR.fromZone(api.to_zone())
        }
        assert ("example.com.", "A", "5.6.7.8") in owners
