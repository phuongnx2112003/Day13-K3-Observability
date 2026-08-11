from __future__ import annotations

import re
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Context variables live for the current async task.  Clear them first so
        # a reused worker never attaches the previous request's identity to a log.
        clear_contextvars()

        supplied_id = request.headers.get("x-request-id", "")
        if re.fullmatch(r"req-[0-9a-f]{8}", supplied_id):
            correlation_id = supplied_id
        else:
            correlation_id = f"req-{uuid.uuid4().hex[:8]}"

        bind_contextvars(correlation_id=correlation_id)
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = correlation_id
            response.headers["x-response-time-ms"] = str(
                int((time.perf_counter() - start) * 1000)
            )
            return response
        finally:
            clear_contextvars()
