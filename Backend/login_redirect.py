"""Lambda entrypoint.

This file stays as the Terraform handler target (login_redirect.lambda_handler),
but delegates all request handling to the hexagonal architecture layers under
`hexapp/`.
"""

from __future__ import annotations

from typing import Any

from hexapp.inbound.api_gateway import handle_event


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    return handle_event(event, context)
