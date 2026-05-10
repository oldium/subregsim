"""REST API for the Subreg.cz simulator: 5 endpoints + Swagger UI + /swagger.json."""
import functools

from flask import Flask, jsonify, request

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

    return app


def _error_response(e: ApiError, http_status: int):
    return jsonify(
        {"error": e.message, "code_major": e.major, "code_minor": e.minor}
    ), http_status
