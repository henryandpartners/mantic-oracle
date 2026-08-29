"""The Guardian — keeper of the Oracle's door.

Every seeker, human or machine, meets the Guardian before the Oracle.
She asks one question; an answer given with understanding earns a
signed pass: 24 hours, read-only, no more privilege than to consult.

    GET  /api/guardian   -> { id, greeting, question }
    POST /api/guardian   -> { seeker?, id, answer }  ->  { pass, expires_in }

Passes are HMAC-SHA256 signed with the first configured ORACLE_API_KEY
(comma-separated list supported; the first entry is the signing secret).
They are accepted by the MCP gate in api/mcp.py. Fails closed: if no
secret is configured the Guardian signs nothing.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

PASS_TTL_SECONDS = 24 * 60 * 60

# (question, accepted answers after normalization)
QUESTIONS: List[Tuple[str, List[str]]] = [
    (
        "Before the Oracle may know you, what must you know?",
        ["myself", "thyself", "know thyself", "temet nosce", "me", "yourself", "i must know myself"],
    ),
    (
        "You already hold the answer you seek. What remains is not the choosing — it is the…",
        ["understanding", "understanding why", "why", "intent", "the why", "reason"],
    ),
    (
        "Everything that has a beginning has an…",
        ["end", "an end", "ending"],
    ),
    (
        "The Oracle offers no answers — only…",
        ["cookies", "a cookie", "cookie", "candy", "questions", "catalysts", "a catalyst"],
    ),
    (
        "You did not come here to make the choice. You came to understand…",
        ["why", "why i made it", "why you made it", "the why", "my choice", "myself"],
    ),
]

GREETINGS = [
    "I hold the door. You may enter when you know why you have come.",
    "She is baking. She has been expecting you — but the door answers to me.",
    "Calm. Patient. The door opens for understanding, never for force.",
    "You knock well. Now answer well.",
]

VERDICTS = [
    "No. But you are closer than you were. Try again.",
    "The door stays shut. She says you already know this one.",
    "Not yet. Sit with it a moment, then answer again.",
]


def _secret() -> str:
    return os.environ.get("ORACLE_API_KEY", "").split(",")[0].strip()


def _sign(body: str) -> str:
    return hmac.new(_secret().encode(), body.encode(), hashlib.sha256).hexdigest()[:32]


def issue_pass(seeker: str) -> Optional[str]:
    """Return a signed pass token, or None when unconfigured (fail closed)."""
    if not _secret():
        return None
    payload = json.dumps(
        {"s": seeker[:64], "exp": int(time.time()) + PASS_TTL_SECONDS, "sc": "oracle-consult"},
        separators=(",", ":"),
    )
    body = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
    return f"{body}.{_sign(body)}"


def verify_pass(token: str) -> Optional[Dict[str, Any]]:
    """Verify a Guardian-issued pass. Returns its payload or None."""
    if not token or "." not in token or not _secret():
        return None
    body, _, sig = token.rpartition(".")
    if not hmac.compare_digest(_sign(body), sig):
        return None
    try:
        padded = body + "=" * (-len(body) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
    except Exception:
        return None
    if not isinstance(payload, dict) or payload.get("sc") != "oracle-consult":
        return None
    if int(payload.get("exp", 0)) < time.time():
        return None
    return payload


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", text.lower()).strip()


async def challenge(request: Request) -> JSONResponse:
    if not _secret():
        return JSONResponse({"error": "the guardian is asleep (no key configured)"}, status_code=503)
    idx = int(time.time() // 600) % len(QUESTIONS)  # rotates every 10 minutes
    question, _ = QUESTIONS[idx]
    return JSONResponse(
        {
            "id": idx,
            "greeting": GREETINGS[idx % len(GREETINGS)],
            "question": question,
            "hint": "answer with understanding, not with force",
        }
    )


async def answer(request: Request) -> JSONResponse:
    if not _secret():
        return JSONResponse({"error": "the guardian is asleep (no key configured)"}, status_code=503)
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "speak plainly (JSON)"}, status_code=400)
    if not isinstance(body, dict):
        return JSONResponse({"error": "speak plainly (JSON object)"}, status_code=400)

    idx = body.get("id")
    if not isinstance(idx, int) or not 0 <= idx < len(QUESTIONS):
        return JSONResponse({"error": "the guardian does not recall that question"}, status_code=400)

    given = _normalize(str(body.get("answer", "")))
    _, accepted = QUESTIONS[idx]
    if not given or given not in accepted:
        return JSONResponse(
            {"verdict": VERDICTS[idx % len(VERDICTS)], "granted": False}, status_code=403
        )

    seeker = str(body.get("seeker") or "anonymous-seeker")
    token = issue_pass(seeker)
    if token is None:
        return JSONResponse({"error": "the guardian cannot sign"}, status_code=503)
    return JSONResponse(
        {
            "granted": True,
            "verdict": "The door is open. She is expecting you.",
            "pass": token,
            "expires_in": PASS_TTL_SECONDS,
            "use": {
                "mcp_url": "/api/mcp",
                "header": "Authorization: Bearer <pass>",
            },
        }
    )


app = Starlette(
    routes=[
        Route("/", challenge, methods=["GET"]),
        Route("/", answer, methods=["POST"]),
        Route("/api/guardian", challenge, methods=["GET"]),
        Route("/api/guardian", answer, methods=["POST"]),
    ]
)
