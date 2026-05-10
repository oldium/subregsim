"""Marshmallow schemas for REST request validation and response shaping.

Schemas double as the source of truth for the apispec-generated OpenAPI doc.
Shapes are aligned with the real upstream swagger at https://api.subreg.cz/swagger.json.
"""
from marshmallow import Schema, fields, validate


class ErrorSchema(Schema):
    """Body of any non-2xx response."""
    error = fields.String(required=True, metadata={"description": "Detailed error message"})
    code_major = fields.Integer(required=True, metadata={"description": "Major error code"})
    code_minor = fields.Integer(required=True, metadata={"description": "Minor error code"})


class DomainSchema(Schema):
    name = fields.String(required=True, metadata={"description": "domain name"})
    expire = fields.String(required=True, metadata={"description": "domain expiration date"})
    autorenew = fields.Function(
        lambda obj: str(obj.get("autorenew", 0)) if isinstance(obj, dict) else str(getattr(obj, "autorenew", 0)),
        metadata={"description": "domain autorenew setting (0 - EXPIRE, 1 - AUTORENEW, 2 - RENEWONCE)"},
    )


class DomainsListResponseSchema(Schema):
    domains = fields.List(fields.Nested(DomainSchema), required=True)
    count = fields.Integer(required=True)


class DnsRecordSchema(Schema):
    """Single DNS record in a getDns response."""
    id = fields.Function(
        lambda obj: str(obj["id"]) if isinstance(obj, dict) else str(obj.id),
        metadata={"description": "ID of the record"},
    )
    name = fields.String(required=True, metadata={"description": "hostname"})
    type = fields.String(required=True, metadata={"description": "type of DNS record"})
    content = fields.String(required=True, metadata={"description": "value of this record"})
    prio = fields.Integer(metadata={"description": "priority (MX only)"})
    ttl = fields.Integer(metadata={"description": "TTL value"})


class DnsZoneResponseSchema(Schema):
    domain = fields.String(required=True)
    records = fields.List(fields.Nested(DnsRecordSchema), required=True)


class CreateRecordRequestSchema(Schema):
    name = fields.String(
        required=True,
        validate=validate.Length(max=255),
        metadata={"description": "hostname (without registered domain)"},
    )
    type = fields.String(
        required=True,
        validate=[validate.Length(max=6), validate.Regexp(r"^[A-Z]+$")],
        metadata={"description": "type of DNS record"},
    )
    content = fields.String(
        required=True,
        validate=validate.Length(max=4096),
        metadata={"description": "value of this record"},
    )
    prio = fields.Integer(
        validate=validate.Range(min=0, max=65535),
        metadata={"description": "priority (MX only)"},
    )
    ttl = fields.Integer(
        validate=validate.Range(min=0),
        metadata={"description": "TTL value"},
    )


class CreateRecordResponseSchema(Schema):
    domain = fields.String(required=True)
    record_id = fields.String(required=True)


class ModifyRecordRequestSchema(Schema):
    type = fields.String(
        required=True,
        validate=[validate.Length(max=6), validate.Regexp(r"^[A-Z]+$")],
    )
    content = fields.String(required=True, validate=validate.Length(max=4096))
    prio = fields.Integer(validate=validate.Range(min=0, max=65535))
    ttl = fields.Integer(validate=validate.Range(min=0))
