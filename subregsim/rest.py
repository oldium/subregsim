"""REST API for the Subreg.cz simulator: 5 endpoints + Swagger UI + /swagger.json."""
import functools

from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flask import Flask, jsonify, request
from flask_swagger_ui import get_swaggerui_blueprint
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
        """List all domains in your account.
        ---
        get:
          tags: [Domains]
          operationId: listDomains
          summary: List all domains in your account.
          security:
            - bearer: []
          responses:
            '200':
              description: Command completed successfully
              content:
                application/json:
                  schema: DomainsListResponse
            '401':
              description: Missing or incorrect authorization
              content:
                application/json:
                  schema: Error
        """
        from .schemas import DomainsListResponseSchema

        domains = api.list_domains()
        return jsonify(
            DomainsListResponseSchema().dump({"domains": domains, "count": len(domains)})
        )

    @app.route("/dns/<string:domain>", methods=["GET"])
    @require_bearer
    def get_dns_zone(domain: str):
        """List of DNS records for specified domain.
        ---
        get:
          tags: [DNS]
          operationId: getDns
          summary: List of DNS records for specified domain.
          security:
            - bearer: []
          parameters:
            - in: path
              name: domain
              required: true
              schema: {type: string, maxLength: 255}
          responses:
            '200':
              description: Command completed successfully
              content:
                application/json:
                  schema: DnsZoneResponse
            '400':
              description: An error has occured
              content:
                application/json:
                  schema: Error
            '401':
              description: Missing or incorrect authorization
              content:
                application/json:
                  schema: Error
        """
        from .schemas import DnsZoneResponseSchema

        records = api.get_dns_zone(domain)
        return jsonify(DnsZoneResponseSchema().dump({"domain": domain, "records": records}))

    @app.route("/dns/<string:domain>/record", methods=["POST"])
    @require_bearer
    def create_dns_record(domain: str):
        """Add single DNS record to zone.
        ---
        post:
          tags: [DNS]
          operationId: createDnsRecord
          summary: Add single DNS record to zone.
          security:
            - bearer: []
          parameters:
            - in: path
              name: domain
              required: true
              schema: {type: string, maxLength: 255}
          requestBody:
            required: true
            content:
              application/json:
                schema: CreateRecordRequest
          responses:
            '200':
              description: Command completed successfully
              content:
                application/json:
                  schema: CreateRecordResponse
            '400':
              description: An error has occured
              content:
                application/json:
                  schema: Error
            '401':
              description: Missing or incorrect authorization
              content:
                application/json:
                  schema: Error
        """
        from .schemas import CreateRecordRequestSchema, CreateRecordResponseSchema

        try:
            payload = CreateRecordRequestSchema().load(request.get_json(silent=True) or {})
        except ValidationError as e:
            _raise_from_validation(e)
        rid = api.add_dns_record(domain, payload)
        return jsonify(
            CreateRecordResponseSchema().dump({"domain": domain, "record_id": rid})
        )

    @app.route("/dns/<string:domain>/record/<string:id>", methods=["PUT"])
    @require_bearer
    def modify_dns_record(domain: str, id: str):
        """Modify single DNS record in zone.
        ---
        put:
          tags: [DNS]
          operationId: modifyDnsRecord
          summary: Modify single DNS record in zone.
          security:
            - bearer: []
          parameters:
            - in: path
              name: domain
              required: true
              schema: {type: string, maxLength: 255}
            - in: path
              name: id
              required: true
              schema: {type: string, maxLength: 100, pattern: '^[a-zA-Z0-9]+$'}
          requestBody:
            required: true
            content:
              application/json:
                schema: ModifyRecordRequest
          responses:
            '200':
              description: Command completed successfully
            '400':
              description: An error has occured
              content:
                application/json:
                  schema: Error
            '401':
              description: Missing or incorrect authorization
              content:
                application/json:
                  schema: Error
        """
        from .schemas import ModifyRecordRequestSchema

        rid = _parse_record_id(id)
        try:
            payload = ModifyRecordRequestSchema().load(request.get_json(silent=True) or {})
        except ValidationError as e:
            _raise_from_validation(e)
        api.modify_dns_record(domain, rid, payload)
        return jsonify({})

    @app.route("/dns/<string:domain>/record/<string:id>", methods=["DELETE"])
    @require_bearer
    def delete_dns_record(domain: str, id: str):
        """Remove single DNS record from zone.
        ---
        delete:
          tags: [DNS]
          operationId: deleteDnsRecord
          summary: Remove single DNS record from zone.
          security:
            - bearer: []
          parameters:
            - in: path
              name: domain
              required: true
              schema: {type: string, maxLength: 255}
            - in: path
              name: id
              required: true
              schema: {type: string, maxLength: 100, pattern: '^[a-zA-Z0-9]+$'}
          responses:
            '200':
              description: Command completed successfully
            '400':
              description: An error has occured
              content:
                application/json:
                  schema: Error
            '401':
              description: Missing or incorrect authorization
              content:
                application/json:
                  schema: Error
        """
        rid = _parse_record_id(id)
        api.delete_dns_record(domain, rid)
        return jsonify({})

    spec = _build_spec(app)

    @app.route("/swagger.json", methods=["GET"])
    def swagger_json():
        return jsonify(spec.to_dict())

    swagger_ui_blueprint = get_swaggerui_blueprint(
        base_url="/",
        api_url="/swagger.json",
        config={"app_name": "Subreg.cz API Simulator"},
    )
    app.register_blueprint(swagger_ui_blueprint)

    return app


def _build_spec(app: Flask) -> APISpec:
    """Construct the OpenAPI 3.0 spec for the 5 implemented endpoints."""
    from .schemas import (
        CreateRecordRequestSchema,
        CreateRecordResponseSchema,
        DnsZoneResponseSchema,
        DomainsListResponseSchema,
        ErrorSchema,
        ModifyRecordRequestSchema,
    )

    spec = APISpec(
        title="Subreg.CZ API",
        version="1",
        openapi_version="3.0.0",
        plugins=[FlaskPlugin(), MarshmallowPlugin()],
    )
    spec.components.security_scheme("bearer", {"type": "http", "scheme": "bearer"})
    spec.options["security"] = [{"bearer": []}]

    spec.components.schema("Error", schema=ErrorSchema)
    spec.components.schema("DomainsListResponse", schema=DomainsListResponseSchema)
    spec.components.schema("DnsZoneResponse", schema=DnsZoneResponseSchema)
    spec.components.schema("CreateRecordRequest", schema=CreateRecordRequestSchema)
    spec.components.schema("CreateRecordResponse", schema=CreateRecordResponseSchema)
    spec.components.schema("ModifyRecordRequest", schema=ModifyRecordRequestSchema)

    # Register each implemented Flask view with apispec
    with app.test_request_context():
        for view_name in (
            "list_domains",
            "get_dns_zone",
            "create_dns_record",
            "modify_dns_record",
            "delete_dns_record",
        ):
            spec.path(view=app.view_functions[view_name])

    return spec


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
