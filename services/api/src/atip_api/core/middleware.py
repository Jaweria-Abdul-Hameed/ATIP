"""HTTP middleware for request IDs, timing, tenant context, and security headers."""

import json
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = f"req_{uuid.uuid4().hex[:16]}"

        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        # If it's a standard JSON response, ensure meta.request_id matches
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            body = [chunk async for chunk in response.body_iterator]
            full_body = b"".join(body)
            try:
                payload = json.loads(full_body)
                if isinstance(payload, dict) and "meta" in payload:
                    if not payload["meta"].get("request_id"):
                        payload["meta"]["request_id"] = request_id
                        new_body = json.dumps(payload).encode("utf-8")
                        response_headers = dict(response.headers)
                        response_headers["content-length"] = str(len(new_body))
                        return Response(
                            content=new_body,
                            status_code=response.status_code,
                            headers=response_headers,
                            media_type="application/json",
                        )
            except Exception:
                pass

            return Response(
                content=full_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="application/json",
            )

        return response


class TenantContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        org_id = request.headers.get("X-Organization-ID")
        request.state.organization_id = org_id
        response = await call_next(request)
        if org_id:
            response.headers["X-Organization-ID"] = org_id
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        process_time_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Response-Time-Ms"] = f"{process_time_ms:.2f}"
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
