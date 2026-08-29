"""Local preview: serves EXACTLY what Vercel serves — public/ pages +
/api/guardian + /api/mcp — on one port, one process.

Usage:  .venv/bin/python serve_local.py  ->  http://127.0.0.1:8811
"""

from __future__ import annotations

import os
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Real signing secret so guardian passes are genuine.
_secret_file = HERE / ".secrets" / "oracle-api-key.txt"
if _secret_file.exists():
    os.environ.setdefault("ORACLE_API_KEY", _secret_file.read_text().strip())

from api.guardian import app as guardian_app  # noqa: E402
from api.mcp import app as mcp_app  # noqa: E402

FILES = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/docs": ("docs.html", "text/html; charset=utf-8"),
}


async def app(scope, receive, send):
    if scope["type"] == "lifespan":
        # fire the MCP app's lifespan (its task group must start); guardian
        # is a plain Starlette app and needs none.
        await mcp_app(scope, receive, send)
        return

    path = scope.get("path", "")
    if path.startswith("/api/mcp") or path == "/api/ping":
        await mcp_app(scope, receive, send)
    elif path.startswith("/api/guardian"):
        await guardian_app(scope, receive, send)
    elif path in FILES:
        name, ctype = FILES[path]
        body = (HERE / "public" / name).read_bytes()
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", ctype.encode()), (b"content-length", str(len(body)).encode())],
            }
        )
        await send({"type": "http.response.body", "body": body})
    else:
        body = b"not found"
        await send({"type": "http.response.start", "status": 404, "headers": [(b"content-type", b"text/plain")]})
        await send({"type": "http.response.body", "body": body})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8811, log_level="warning")
