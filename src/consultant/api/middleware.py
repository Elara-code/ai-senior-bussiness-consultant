import re
from collections.abc import Awaitable, Callable
from typing import cast
from uuid import uuid4

from fastapi import FastAPI, Request, Response

from consultant.application.audit import InMemoryAuditLog

_SECRET_PATTERNS = [
    re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+"),
    re.compile(r"(?i)((?:api[_-]?key|password|secret)\s*[:=]\s*)[^\s,;]+"),
]


def redact_sensitive(value: str) -> str:
    redacted = value
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub(r"\1[REDACTED]", redacted)
    return redacted


def install_security_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def security_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        audit = cast(InMemoryAuditLog, request.app.state.audit_log)
        audit.append(
            action=f"http.{request.method.lower()}",
            resource_type="api_request",
            request_id=request_id,
            outcome="success" if response.status_code < 400 else "rejected",
            metadata={"path": request.url.path, "status": response.status_code},
        )
        return response
