"""Middlewares de segurança: cabeçalhos de proteção e rate limiting.

Ver docs/security/privacy-and-security.md (CSP, rate limiting). O rate limiting usa janela
fixa em memória — adequado ao MVP; em produção, prefira um store compartilhado (Redis) ou
o limitador da borda (Nginx/WAF).
"""

from __future__ import annotations

import threading
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

_SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        for header, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, *, limit: int, window_seconds: int) -> None:
        super().__init__(app)
        self._limit = limit
        self._window = window_seconds
        self._lock = threading.Lock()
        self._hits: dict[str, tuple[int, int]] = {}  # client -> (window_start, count)

    async def dispatch(self, request: Request, call_next) -> Response:
        client = request.client.host if request.client else "unknown"
        now = int(time.time())
        window_start = now - (now % self._window)

        with self._lock:
            start, count = self._hits.get(client, (window_start, 0))
            if start != window_start:
                start, count = window_start, 0
            count += 1
            self._hits[client] = (start, count)
            over_limit = count > self._limit

        if over_limit:
            retry_after = self._window - (now - window_start)
            return JSONResponse(
                status_code=429,
                content={"detail": "limite de requisições excedido"},
                headers={"Retry-After": str(retry_after)},
            )
        return await call_next(request)
