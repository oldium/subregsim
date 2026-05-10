"""REST API for the Subreg.cz simulator: 5 endpoints + Swagger UI + /swagger.json."""
import functools

from flask import Flask, jsonify, request
from marshmallow import ValidationError

from .api import Api, ApiError
from .auth import BearerAuth


def build_flask_app(api: Api, bearer: BearerAuth) -> Flask:
    app = Flask(__name__)
    app.config["api"] = api
    app.config["bearer"] = bearer

    def require_bearer(view):
        @functools.wraps(view)
        def wrapper(*args, **kwargs):
            try:
                bearer.validate(request.headers.get("Authorization"))
            except ApiError as e:
                return _error_response(e, http_status=401)
            return view(*args, **kwargs)

        return wrapper

    @app.errorhandler(ApiError)
    def _handle_api_error(e: ApiError):
        return _error_response(e, http_status=400)

    @app.route("/domains", methods=["GET"])
    @require_bearer
    def list_domains():
        from .schemas import DomainsListResponseSchema

        domains = api.list_domains()
        return jsonify(
            DomainsListResponseSchema().dump({"domains": domains, "count": len(domains)})
        )

    @app.route("/dns/<string:domain>", methods=["GET"])
    @require_bearer
    def get_dns_zone(domain: str):
        from .schemas import DnsZoneResponseSchema

        records = api.get_dns_zone(domain)
        return jsonify(DnsZoneResponseSchema().dump({"domain": domain, "records": records}))

    @app.route("/dns/<string:domain>/record", methods=["POST"])
    @require_bearer
    def create_dns_record(domain: str):
        from .schemas import CreateRecordRequestSchema, CreateRecordResponseSchema

        try:
            payload = CreateRecordRequestSchema().load(request.get_json(silent=True) or {})
        except ValidationError as e:
            _raise_from_validation(e)
        rid = api.add_dns_record(domain, payload)
        return jsonify(
            CreateRecordResponseSchema().dump({"domain": domain, "record_id": str(rid)})
        )

    @app.route("/dns/<string:domain>/record/<string:record_id>", methods=["PUT"])
    @require_bearer
    def modify_dns_record(domain: str, record_id: str):
        from .schemas import ModifyRecordRequestSchema

        rid = _parse_record_id(record_id)
        try:
            payload = ModifyRecordRequestSchema().load(request.get_json(silent=True) or {})
        except ValidationError as e:
            _raise_from_validation(e)
        api.modify_dns_record(domain, rid, payload)
        return jsonify({})

    @app.route("/dns/<string:domain>/record/<string:record_id>", methods=["DELETE"])
    @require_bearer
    def delete_dns_record(domain: str, record_id: str):
        rid = _parse_record_id(record_id)
        api.delete_dns_record(domain, rid)
        return jsonify({})

    return app


def _error_response(e: ApiError, http_status: int):
    return jsonify(
        {"error": e.message, "code_major": e.major, "code_minor": e.minor}
    ), http_status


_VALIDATION_FIELD_TO_CODE = {
    "name": (524, 1006, "Invalid domain name in record"),
    "type": (524, 1007, "Unknown record type"),
    "content": (524, 1010, "Missing or invalid record content"),
}


def _raise_from_validation(err: ValidationError) -> None:
    """Map Marshmallow validation errors to subreg's (major, minor) codes."""
    messages = err.messages if isinstance(err.messages, dict) else {}
    for field, (major, minor, msg) in _VALIDATION_FIELD_TO_CODE.items():
        if field in messages:
            raise ApiError(major, minor, msg)
    raise ApiError(400, 0, str(err.messages))


def _parse_record_id(raw: str) -> int:
    """Parse a record id from path. The upstream swagger restricts it to ^[a-zA-Z0-9]+$
    but the simulator only knows integer IDs, so non-numeric is treated as 'not found'."""
    try:
        return int(raw)
    except ValueError:
        raise ApiError(524, 1003, "Record does not exist")
