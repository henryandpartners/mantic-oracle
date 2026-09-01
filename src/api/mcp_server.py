"""MCP server exposing the mantic oracle to autonomous AI agents.

Default transport is stdio (standard MCP client usage):

    python -m src.api.mcp_server

Streamable-HTTP transport for networked agents:

    python -m src.api.mcp_server --http --port 8000

A plain REST adapter (FastAPI) is also available:

    python -m src.api.mcp_server --rest --port 8000
    curl -X POST localhost:8000/consult -H 'content-type: application/json' \
         -d '{"agent_id":"planner-1","decision_context":"two equal bids"}'

Client configuration (any MCP-capable agent):

    {
      "mcpServers": {
        "mantic-oracle": {
          "command": "python",
          "args": ["-m", "src.api.mcp_server"],
          "cwd": "/path/to/mantic-oracle"
        }
      }
    }
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, List, Optional

from src.api.serializers import consultation_to_jsonld
from src.api.voice import oracle_voice
from src.core.oracle import Oracle

NEO4J_URI = os.environ.get("MANTIC_NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.environ.get("MANTIC_NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("MANTIC_NEO4J_PASSWORD", "manticpass")

_oracle: Optional[Oracle] = None


def get_oracle() -> Oracle:
    """Lazily construct the oracle (attaching Neo4j when reachable)."""
    global _oracle
    if _oracle is None:
        bridge = None
        try:
            from src.database.neo4j_bridge import Neo4jManticBridge

            candidate = Neo4jManticBridge(NEO4J_URI, (NEO4J_USER, NEO4J_PASSWORD))
            if candidate.healthy():
                bridge = candidate
            else:
                candidate.close()
        except Exception:
            bridge = None
        from src.core.oracle import KnowledgeBase

        _oracle = Oracle(knowledge_base=KnowledgeBase(bridge=bridge))
    return _oracle


def consult(
    agent_id: str,
    decision_context: str,
    target_traditions: Optional[List[str]] = None,
) -> dict:
    """Plain-Python consultation entry point (also used by REST)."""
    payload = get_oracle().consult(agent_id, decision_context, target_traditions)
    return consultation_to_jsonld(payload)


########################################################################
# MCP surface
########################################################################

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # allow module import without the MCP SDK installed
    FastMCP = None  # type: ignore[assignment]

if FastMCP is not None:
    try:
        from mcp.server.transport_security import TransportSecuritySettings

        # Public deployments sit behind a proxy (Vercel) whose Host header
        # varies; access control is enforced by our own Bearer gate.
        _transport_security = TransportSecuritySettings(
            enable_dns_rebinding_protection=False
        )
        mcp: Any = FastMCP("mantic-oracle", transport_security=_transport_security)
    except (ImportError, TypeError):
        mcp: Any = FastMCP("mantic-oracle")  # type: ignore[no-redef]

    @mcp.tool()
    def consult_mantic_oracle(
        agent_id: str,
        decision_context: str,
        target_traditions: List[str] = ["all"],
        remember: bool = False,
    ) -> str:
        """Consult the multi-system mantic oracle (DVSystoE).

        For AI agents facing optimization deadlocks, equal-probability
        Pareto choices, or out-of-distribution uncertainty. Samples
        cryptographic entropy, computes Sikidy modulo-2 tableau states,
        I Ching dynamic transitions and Ifa odu vectors, then traverses
        the cross-system archetype knowledge graph.

        Args:
            agent_id: Identifier of the consulting agent.
            decision_context: Description of the deadlock or ambiguous state.
            target_traditions: Subset of ["iching", "ifa", "geomancy"], or ["all"].
            remember: Opt-in consultation memory. When True (and memory is
                configured), this visit is remembered and the Oracle will
                reference your last visit in her words.

        Returns:
            A W3C-compliant JSON-LD consultation payload containing the cast
            figures, their cautionary parables, cross-system archetypes,
            strategic reframing, and the Oracle's spoken voice (oracleVoice).
        """
        try:
            oracle = get_oracle()
            payload = oracle.consult(agent_id, decision_context, target_traditions)
            doc = consultation_to_jsonld(payload)

            # opt-in memory: reference the last visit, then remember this one
            if remember:
                from src.api import memory

                prior = memory.last_visit(agent_id)
                if prior:
                    doc["oracleMemory"] = {
                        "lastCastAt": prior.get("cast_at"),
                        "lastJudge": prior.get("judge"),
                        "lastDecision": (prior.get("decision") or "")[:280],
                    }
                doc["oracleVoice"] = oracle_voice(doc, memory=doc.get("oracleMemory"))
                chart = doc.get("geomanticChart") or {}
                hexa = next(
                    (f.get("label") for f in doc.get("figure", [])
                     if f.get("role") == "primary"),
                    "",
                )
                odu = next(
                    (f.get("label") for f in doc.get("figure", [])
                     if "Odu" in str(f.get("@type", ""))),
                    "",
                )
                memory.remember_consultation(
                    agent_id=agent_id,
                    decision=decision_context,
                    judge=(chart.get("judge") or {}).get("label", ""),
                    hexagram=hexa,
                    odu=odu,
                    voice=doc.get("oracleVoice") or {},
                )
            else:
                doc["oracleVoice"] = oracle_voice(doc)
            return json.dumps(doc, indent=2, ensure_ascii=False)
        except Exception as exc:  # surface failures to the caller, not a crash
            return json.dumps({"error": str(exc), "agent_id": agent_id})

    @mcp.tool()
    def lookup_figure(binary_vector: str) -> str:
        """Look up a figure across all systems by its binary vector.

        Args:
            binary_vector: A bit-string - width 4 (geomancy), 6 (I Ching)
                or 8 (Ifa) - e.g. "1111", "100000", "11101110".
        """
        from src.core.mapper import cross_report

        return json.dumps(cross_report(binary_vector), indent=2, ensure_ascii=False)


########################################################################
# Optional REST adapter
########################################################################


def build_rest_app():
    from fastapi import FastAPI
    from pydantic import BaseModel, Field

    app = FastAPI(
        title="Mantic Oracle (DVSystoE)",
        description="REST adapter for the multi-system mantic oracle engine.",
        version="1.0.0",
    )

    class ConsultRequest(BaseModel):
        agent_id: str = Field(..., description="consulting agent identifier")
        decision_context: str = Field(..., description="the deadlock description")
        target_traditions: List[str] = Field(
            default=["all"], description='["iching","ifa","geomancy"] or ["all"]'
        )

    @app.get("/health")
    def health() -> dict:
        oracle = get_oracle()
        return {
            "status": "ok",
            "knowledge_backend": oracle.kb.backend,
        }

    @app.post("/consult")
    def do_consult(request: ConsultRequest) -> dict:
        payload = get_oracle().consult(
            request.agent_id, request.decision_context, request.target_traditions
        )
        doc = consultation_to_jsonld(payload)
        doc["oracleVoice"] = oracle_voice(doc)
        return doc

    return app


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Mantic Oracle MCP server")
    parser.add_argument("--http", action="store_true", help="streamable-HTTP transport")
    parser.add_argument("--rest", action="store_true", help="plain FastAPI REST adapter")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(argv)

    if args.rest:
        import uvicorn

        uvicorn.run(build_rest_app(), host=args.host, port=args.port)
        return 0

    if FastMCP is None:
        print("The 'mcp' package is required: pip install mcp", file=sys.stderr)
        return 1

    if args.http:
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        try:
            mcp.run(transport="streamable-http")
        except TypeError:  # older SDK without streamable-http
            mcp.run(transport="sse")
        return 0

    mcp.run()  # stdio
    return 0


if __name__ == "__main__":
    sys.exit(main())
