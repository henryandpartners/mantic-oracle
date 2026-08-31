"""Public, hardened MCP endpoint for the Mantic Oracle (serverless deploy).

Security model (defense against deletion / damage / destruction):

1. READ-ONLY SURFACE - only ``consult_mantic_oracle`` and ``lookup_figure``
   are registered. There is no tool that can mutate the knowledge base.
2. STATELESS & IMMUTABLE - no database is attached in this tier. If Neo4j
   is unreachable the Oracle automatically serves from the in-memory
   knowledge base loaded from the git-tracked TTL files. A public request
   cannot corrupt state that does not persist anywhere.
3. AUTHORIZED ACCESS ONLY - every request must carry
   ``Authorization: Bearer <key>`` matching ``ORACLE_API_KEY`` (a comma
   separated list is allowed for multiple agents). Fails CLOSED (503)
   when the variable is unset, so a misconfigured deploy is never open.
4. REGENERABLE BY CONSTRUCTION - the source of truth is the git repo;
   the public tier is re-cloned from it on every deploy. "Destroying"
   the public instance is impossible: worst case it is redeployed.
"""

from __future__ import annotations

import os

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

# Import the FastMCP instance carrying the two read-only tools.
from src.api.mcp_server import mcp

_KEYS = [k.strip() for k in os.environ.get("ORACLE_API_KEY", "").split(",") if k.strip()]


class BearerGate(BaseHTTPMiddleware):
    """Bearer-token gate + Vercel path routing. Fails closed."""

    async def dispatch(self, request, call_next):
        # per-IP throttle first: stops brute-force hammering before auth
        try:
            from api.guardian import rate_limited, rate_ok

            if not rate_ok(request, per_minute=60):
                return rate_limited()
        except Exception:
            pass  # limiter is best-effort; never lock the door because of it
        path = request.url.path

        # Unauthenticated liveness probe only.
        if path.rstrip("/") in ("/api/ping", "/ping"):
            return JSONResponse({"status": "ok", "service": "mantic-oracle"})

        if not _KEYS:
            return JSONResponse(
                {"error": "oracle locked: no API key configured"}, status_code=503
            )
        auth = request.headers.get("authorization", "")
        token = auth[7:].strip() if auth.lower().startswith("bearer ") else ""
        if token not in _KEYS:
            # The Guardian's pass: short-lived, read-only, HMAC-signed.
            from api.guardian import verify_pass

            if verify_pass(token) is None:
                return JSONResponse({"error": "the guardian has not admitted you"}, status_code=401)

        # Vercel mounts this handler at /api/mcp; FastMCP serves /mcp.
        if path.startswith("/api/mcp"):
            request.scope["path"] = "/mcp"
            request.scope["raw_path"] = b"/mcp"
        return await call_next(request)


def _build_app():
    app = mcp.streamable_http_app()
    return BearerGate(app)


app = _build_app()
