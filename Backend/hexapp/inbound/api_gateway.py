from __future__ import annotations

import base64
import json
import urllib.parse
from dataclasses import dataclass
from typing import Any

from ..application import (
    CreateInstanceForUser,
    GetRequestStatus,
    RequestInstanceTermination,
    RequestInstanceCreation,
    TerminateInstancesForUser,
    TerminateSingleInstance,
)
from ..config import Settings
from ..domain import UserIdentity


@dataclass(frozen=True)
class HttpResponse:
    statusCode: int
    headers: dict[str, str]
    body: str


def _json_response(status: int, payload: dict[str, Any]) -> HttpResponse:
    return HttpResponse(
        statusCode=status,
        headers={"Content-Type": "application/json"},
        body=json.dumps(payload),
    )


def _redirect(location: str) -> HttpResponse:
    return HttpResponse(statusCode=302, headers={"Location": location}, body="")


def _get_path_and_method(event: dict[str, Any]) -> tuple[str, str]:
    path = (
        event.get("rawPath")
        or event.get("requestContext", {}).get("http", {}).get("path")
        or ""
    )
    method = (
        event.get("requestContext", {}).get("http", {}).get("method")
        or event.get("httpMethod")
        or "GET"
    )
    return str(path), str(method).upper()


def _extract_identity(event: dict[str, Any]) -> UserIdentity:
    authorizer = event.get("requestContext", {}).get("authorizer", {}) or {}
    jwt_ctx = authorizer.get("jwt") or {}
    claims = jwt_ctx.get("claims", {}) or {}

    cognito_sub = claims.get("sub")
    cognito_email = claims.get("email") or claims.get("cognito:username")

    if not cognito_sub:
        headers = event.get("headers", {}) or {}
        auth_header = headers.get("authorization") or headers.get("Authorization")
        if auth_header and isinstance(auth_header, str) and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
            try:
                parts = token.split(".")
                if len(parts) == 3:
                    payload_b64 = parts[1]
                    padding = "=" * (-len(payload_b64) % 4)
                    payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
                    payload = json.loads(payload_bytes.decode("utf-8"))
                    cognito_sub = payload.get("sub")
                    cognito_email = payload.get("email") or payload.get("cognito:username")
            except Exception:
                pass

    return UserIdentity(sub=cognito_sub, email=cognito_email)


def _parse_json_body(event: dict[str, Any]) -> dict[str, Any]:
    body = event.get("body")
    if isinstance(body, str) and body:
        try:
            return json.loads(body)
        except Exception:
            return {}
    if body is None:
        return {}
    if isinstance(body, dict):
        return body
    return {}


def build_login_url(settings: Settings) -> str:
    settings.validate_auth_config()
    params = {
        "client_id": settings.cognito_client_id,
        "response_type": "token",
        "scope": settings.oidc_scopes,
        "redirect_uri": settings.cognito_redirect_uri,
        "state": "login",
    }
    return f"https://{settings.cognito_hosted_domain}/oauth2/authorize?{urllib.parse.urlencode(params)}"


def build_logout_url(settings: Settings) -> str:
    settings.validate_auth_config()
    params = {
        "client_id": settings.cognito_client_id,
        "logout_uri": settings.cognito_redirect_uri,
    }
    return f"https://{settings.cognito_hosted_domain}/logout?{urllib.parse.urlencode(params)}"


def handle_event(event: dict[str, Any], _context: Any = None) -> dict[str, Any]:
    settings = Settings.from_env()
    path, method = _get_path_and_method(event)
    identity = _extract_identity(event)

    # Lazy imports keep the core importable without AWS SDKs present (useful for local tests).
    from ..adapters.aws.clock import UtcClock
    from ..adapters.aws.dynamodb_repo import DynamoDbInstanceRepository
    from ..adapters.aws.dynamodb_requests import DynamoDbRequestRepository
    from ..adapters.aws.ec2_compute import Ec2ComputeAdapter
    from ..adapters.aws.eventbridge_bus import EventBridgeBusAdapter

    compute = Ec2ComputeAdapter(region=settings.aws_region, ami_id_override=settings.ami_id)
    repo = DynamoDbInstanceRepository(region=settings.aws_region, table_name=settings.ddb_table_name)
    request_repo = DynamoDbRequestRepository(region=settings.aws_region, table_name=settings.ddb_table_name)
    clock = UtcClock()
    event_bus = EventBridgeBusAdapter(region=settings.aws_region)
    event_source = "app.ec2-control-plane"

    try:
        if path.endswith("/logout") and method == "GET":
            return _redirect(build_logout_url(settings)).__dict__

        if path.endswith("/login") and method == "GET":
            return _redirect(build_login_url(settings)).__dict__

        if path.endswith("/create-ec2") and method == "POST":
            body = _parse_json_body(event)
            instance_type = body.get("instance_type") or settings.default_instance_type
            key_name = body.get("key_name") or body.get("KeyName")

            if not identity.sub:
                return _json_response(400, {"message": "Missing user id"}).__dict__

            use_case = RequestInstanceCreation(
                request_repo=request_repo,
                event_bus=event_bus,
                clock=clock,
                event_source=event_source,
            )
            result = use_case.execute(
                user_id=identity.sub,
                email=identity.email,
                instance_type=str(instance_type),
                key_name=str(key_name) if key_name else None,
            )
            resp = _json_response(202, {"request_id": result.request_id})
            return resp.__dict__

        if path.startswith("/requests/") and method == "GET":
            if not identity.sub:
                return _json_response(400, {"message": "Missing user id"}).__dict__

            request_id = path.split("/requests/", 1)[1].strip().strip("/")
            if not request_id:
                return _json_response(400, {"message": "Missing request id"}).__dict__

            use_case = GetRequestStatus(request_repo=request_repo)
            status = use_case.execute(user_id=identity.sub, request_id=request_id)
            if not status:
                return _json_response(404, {"message": "Not found"}).__dict__

            return _json_response(
                200,
                {
                    "request_id": status.request_id,
                    "status": status.status,
                    "instance_id": status.instance_id,
                    "error": status.error,
                    "terminated": status.terminated,
                },
            ).__dict__

        if path.startswith("/instances") and method == "DELETE":
            raw_path = path
            if raw_path.rstrip("/") == "/instances":
                inst_id = ""
            else:
                parts = raw_path.split("/instances/", 1)
                inst_id = parts[1].strip() if len(parts) == 2 else ""

            if not identity.sub:
                return _json_response(
                    400,
                    {"message": "Missing user id; cannot resolve which instances to delete"},
                ).__dict__

            # Event-driven delete: publish a request and let the worker do termination.
            use_case = RequestInstanceTermination(
                request_repo=request_repo,
                event_bus=event_bus,
                clock=clock,
                event_source=event_source,
            )
            result = use_case.execute(
                user_id=identity.sub,
                email=identity.email,
                instance_id=inst_id or None,
            )
            return _json_response(202, {"request_id": result.request_id}).__dict__

        # default: redirect to login
        return _redirect(build_login_url(settings)).__dict__

    except ValueError as cfg_err:
        return _json_response(500, {"error": str(cfg_err)}).__dict__
    except Exception as e:
        return _json_response(500, {"error": str(e)}).__dict__
