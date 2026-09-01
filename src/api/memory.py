"""Consultation memory (opt-in).

The public tier is immutable by design - nothing a seeker does can
change the knowledge base. Memory lives *beside* the engine, in an
external table, and only for agents who explicitly ask for it:

    consult_mantic_oracle(..., remember=True)

Backed by Supabase (PostgREST). If SUPABASE_URL / SUPABASE_SERVICE_KEY
are not configured, every call degrades to a silent no-op - the
stateless guarantee is never broken, and the door never fails because
memory did.

Table (created by scripts/create_memory_table.sql):

    oracle_consultations(
        id           uuid primary key default gen_random_uuid(),
        agent_id     text not null,
        decision     text,
        judge        text,
        hexagram     text,
        odu          text,
        voice        jsonb,
        cast_at      timestamptz not null default now()
    )
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


def _config() -> Optional[Dict[str, str]]:
    url = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        return None
    return {"url": url, "key": key}


def _table_url(cfg: Dict[str, str], agent_id: Optional[str] = None) -> str:
    u = f"{cfg['url']}/rest/v1/oracle_consultations?select=*"
    if agent_id:
        u += f"&agent_id=eq.{agent_id}"
    return u


def remember_consultation(
    agent_id: str,
    decision: str,
    judge: str,
    hexagram: str,
    odu: str,
    voice: Dict[str, Any],
) -> bool:
    """Store one consultation. Returns True if persisted."""
    cfg = _config()
    if cfg is None:
        return False
    import json as _json

    import urllib.request

    body = _json.dumps(
        {
            "agent_id": agent_id,
            "decision": decision[:2000],
            "judge": judge,
            "hexagram": hexagram,
            "odu": odu,
            "voice": voice,
        }
    ).encode()
    req = urllib.request.Request(
        f"{cfg['url']}/rest/v1/oracle_consultations",
        data=body,
        headers={
            "apikey": cfg["key"],
            "Authorization": f"Bearer {cfg['key']}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            return 200 <= resp.status < 300
    except Exception:
        return False  # memory is a courtesy, never a gate


def last_visit(agent_id: str) -> Optional[Dict[str, Any]]:
    """Fetch the previous consultation for an agent (most recent first)."""
    cfg = _config()
    if cfg is None:
        return None
    import json as _json

    import urllib.request

    req = urllib.request.Request(
        _table_url(cfg) + f"&agent_id=eq.{agent_id}&order=cast_at.desc&limit=1",
        headers={
            "apikey": cfg["key"],
            "Authorization": f"Bearer {cfg['key']}",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            rows = _json.loads(resp.read().decode())
        return rows[0] if rows else None
    except Exception:
        return None


def memory_enabled() -> bool:
    return _config() is not None


__all__ = ["remember_consultation", "last_visit", "memory_enabled"]
