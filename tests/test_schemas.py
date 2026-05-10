"""Tests for Marshmallow schemas: request validation + response shaping."""
import pytest
from marshmallow import ValidationError

from subregsim.schemas import (
    CreateRecordRequestSchema,
    DnsRecordSchema,
    DomainSchema,
    ErrorSchema,
    ModifyRecordRequestSchema,
)


class TestErrorSchema:
    def test_dump_shape(self):
        out = ErrorSchema().dump(
            {"error": "msg", "code_major": 524, "code_minor": 1009}
        )
        assert out == {"error": "msg", "code_major": 524, "code_minor": 1009}


class TestDomainSchema:
    def test_dump_coerces_autorenew_to_string(self):
        out = DomainSchema().dump(
            {"name": "example.com", "expire": "2023-10-20", "autorenew": 0}
        )
        # Upstream spec types autorenew as string; dump it stringified
        assert out == {"name": "example.com", "expire": "2023-10-20", "autorenew": "0"}


class TestDnsRecordSchema:
    def test_dump_stringifies_id(self):
        out = DnsRecordSchema().dump(
            {"id": 173, "name": "www", "type": "A", "content": "1.2.3.4", "prio": 0, "ttl": 600}
        )
        assert out["id"] == "173"
        assert out["name"] == "www"
        assert out["prio"] == 0
        assert out["ttl"] == 600


class TestCreateRecordRequestSchema:
    def test_loads_required_fields(self):
        out = CreateRecordRequestSchema().load(
            {"name": "www", "type": "A", "content": "1.2.3.4"}
        )
        assert out == {"name": "www", "type": "A", "content": "1.2.3.4"}

    def test_loads_with_optional_prio_and_ttl(self):
        out = CreateRecordRequestSchema().load(
            {"name": "mail", "type": "MX", "content": "smtp.x.com", "prio": 3, "ttl": 900}
        )
        assert out["prio"] == 3
        assert out["ttl"] == 900

    def test_missing_name_raises(self):
        with pytest.raises(ValidationError) as ei:
            CreateRecordRequestSchema().load({"type": "A", "content": "1.2.3.4"})
        assert "name" in ei.value.messages

    def test_missing_type_raises(self):
        with pytest.raises(ValidationError) as ei:
            CreateRecordRequestSchema().load({"name": "x", "content": "1.2.3.4"})
        assert "type" in ei.value.messages

    def test_missing_content_raises(self):
        with pytest.raises(ValidationError) as ei:
            CreateRecordRequestSchema().load({"name": "x", "type": "A"})
        assert "content" in ei.value.messages

    def test_bad_type_pattern_raises(self):
        with pytest.raises(ValidationError) as ei:
            CreateRecordRequestSchema().load(
                {"name": "x", "type": "lowercase", "content": "x"}
            )
        assert "type" in ei.value.messages


class TestModifyRecordRequestSchema:
    def test_requires_type_and_content(self):
        with pytest.raises(ValidationError):
            ModifyRecordRequestSchema().load({})

    def test_loads_full(self):
        out = ModifyRecordRequestSchema().load(
            {"type": "A", "content": "1.2.3.4", "prio": 0, "ttl": 1800}
        )
        assert out == {"type": "A", "content": "1.2.3.4", "prio": 0, "ttl": 1800}
