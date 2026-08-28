"""Consultation oracle: entropy -> algebra -> knowledge graph -> reframing.

The :class:`Oracle` orchestrates a full consultation:

  1. sample entropy for each requested tradition,
  2. derive the algebraic states (shield chart, hexagram cast, odu vector),
  3. enrich every figure through the knowledge graph - Neo4j when the
     bridge is healthy, otherwise a local rdflib fallback over the shipped
     ontology and seed data,
  4. compute cross-system resonances and assemble actionable strategic
     counsel for the consulting agent.

The payload returned by :meth:`Oracle.consult` is a plain dict ready for
JSON-LD serialization by ``src.api.serializers``.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .algebra import EVEN_FIGURES, GeomanticChart, HexagramCast, validate_parity
from .entropy import CryptoEntropy, DeterministicEntropy
from .mapper import cross_report, geomantic_matches, hexagram_resonances
from .tables import (
    GEOMANTIC_BY_BITS,
    KING_WEN_BY_BITS,
    ODU_PRINCIPALS_BY_BITS,
    compound_odu_name,
    odu_index,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ONTOLOGY_DIR = REPO_ROOT / "ontology"

TRADITIONS = ("geomancy", "iching", "ifa")

#################################################################
# Knowledge base (Neo4j bridge with rdflib fallback)
#################################################################


class FigureRecord(BaseModel):
    """A normalized figure record, whichever backend produced it."""

    iri: str
    kind: str                      # GeomanticSign | IChingHexagram | IfaOdu
    label: str
    bits: str
    index: Optional[int] = None
    element: Optional[str] = None
    parable: Optional[str] = None
    archetypes: List[Dict[str, Any]] = Field(default_factory=list)


class KnowledgeBase:
    """Figure lookup over Neo4j (preferred) or local rdflib graph."""

    def __init__(self, bridge: Any = None, ontology_dir: Path | None = None) -> None:
        self.bridge = bridge
        self.ontology_dir = Path(
            ontology_dir or os.environ.get("MANTIC_ONTOLOGY_DIR", DEFAULT_ONTOLOGY_DIR)
        )
        self._graph = None
        self.backend = "rdflib-fallback"
        if bridge is not None:
            try:
                if bridge.healthy():
                    self.backend = "neo4j"
            except Exception:  # pragma: no cover - transport failures fall back
                self.backend = "rdflib-fallback"

    # ------------------------------------------------------------------
    @property
    def graph(self):
        if self._graph is None:
            from rdflib import Graph

            graph = Graph()
            for name in ("mantic_core.ttl", "seed_data.ttl"):
                path = self.ontology_dir / name
                if path.exists():
                    graph.parse(path, format="turtle")
            self._graph = graph
        return self._graph

    # ------------------------------------------------------------------
    def lookup(self, kind: str, bits: str) -> Optional[FigureRecord]:
        """Fetch a figure by class and binary vector."""
        if self.backend == "neo4j":
            record = self.bridge.figure_by_vector(bits)
            if record is None:
                return None
            return FigureRecord(
                iri=record["iri"],
                kind=record.get("kind", kind),
                label=record.get("label", ""),
                bits=bits,
                index=record.get("index"),
                element=record.get("element"),
                parable=record.get("parable"),
                archetypes=record.get("archetypes", []),
            )
        return self._lookup_rdflib(kind, bits)

    def _lookup_rdflib(self, kind: str, bits: str) -> Optional[FigureRecord]:
        from rdflib import RDF, Literal, URIRef

        MANTIC = "https://w3id.org/mantic/core#"
        cls = URIRef(MANTIC + kind)
        query = f"""
        PREFIX mantic: <{MANTIC}>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        SELECT ?f ?label ?index ?element ?parable WHERE {{
          ?f a mantic:{kind} ;
             mantic:hasBinaryVector "{bits}" ;
             rdfs:label ?label .
          OPTIONAL {{ ?f mantic:figureIndex ?index }}
          OPTIONAL {{ ?f mantic:element ?element }}
          OPTIONAL {{ ?f mantic:parable ?parable }}
        }} LIMIT 1
        """
        for row in self.graph.query(query):
            iri = str(row[0])
            record = FigureRecord(
                iri=iri,
                kind=kind,
                label=str(row[1]),
                bits=bits,
                index=int(row[2]) if row[2] is not None else None,
                element=str(row[3]) if row[3] is not None else None,
                parable=str(row[4]) if row[4] is not None else None,
            )
            record.archetypes = self._archetypes_rdflib(iri)
            return record
        return None

    def _archetypes_rdflib(self, iri: str) -> List[Dict[str, Any]]:
        from rdflib import URIRef

        MANTIC = "https://w3id.org/mantic/core#"
        pred = URIRef(MANTIC + "sharesArchetypeWith")
        out: List[Dict[str, Any]] = []
        for s, o in ((s, o) for s, _, o in self.graph.triples((None, pred, None))):
            if str(s) == iri:
                partner = o
            elif str(o) == iri:
                partner = s
            else:
                continue
            label = self.graph.value(partner, URIRef("http://www.w3.org/2000/01/rdf-schema#label"))
            vec = self.graph.value(partner, URIRef(MANTIC + "hasBinaryVector"))
            kinds = [
                str(t).split("#")[-1]
                for t in self.graph.triples((partner, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), None))
            ]
            out.append(
                {
                    "iri": str(partner),
                    "label": str(label) if label else None,
                    "bits": str(vec) if vec else None,
                    "kinds": [k for k in kinds if k != "ManticFigure"],
                }
            )
        return out


#################################################################
# Oracle
#################################################################


class Oracle:
    """The consultation engine exposed to MCP / REST clients."""

    def __init__(
        self,
        entropy: Any = None,
        knowledge_base: KnowledgeBase | None = None,
    ) -> None:
        self.entropy = entropy or CryptoEntropy()
        self.kb = knowledge_base or KnowledgeBase()

    # ------------------------------------------------------------------
    def consult(
        self,
        agent_id: str,
        decision_context: str,
        target_traditions: List[str] | None = None,
    ) -> Dict[str, Any]:
        """Run a full consultation and return the serializable payload."""
        traditions = self._normalize_traditions(target_traditions)
        payload: Dict[str, Any] = {
            "consultation_id": f"urn:uuid:{uuid.uuid4()}",
            "agent_id": agent_id,
            "decision_context": decision_context,
            "cast_at": datetime.now(timezone.utc).isoformat(),
            "entropy_provider": getattr(self.entropy, "provider_name", type(self.entropy).__name__),
            "knowledge_backend": self.kb.backend,
            "traditions": traditions,
        }

        sections: Dict[str, Any] = {}
        if "geomancy" in traditions:
            sections["geomancy"] = self._consult_geomancy()
        if "iching" in traditions:
            sections["iching"] = self._consult_iching()
        if "ifa" in traditions:
            sections["ifa"] = self._consult_ifa()
        payload["tradition_results"] = sections

        payload["resonances"] = self._resonance_report(sections)
        payload["strategic_counsel"] = self._compose_counsel(agent_id, sections)
        return payload

    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_traditions(target: List[str] | None) -> List[str]:
        if not target or "all" in [t.lower() for t in target]:
            return list(TRADITIONS)
        normalized = [t.lower() for t in target]
        unknown = [t for t in normalized if t not in TRADITIONS]
        if unknown:
            raise ValueError(
                f"unknown traditions {unknown}; valid: {list(TRADITIONS)} or ['all']"
            )
        ordered = [t for t in TRADITIONS if t in normalized]
        return ordered

    # ------------------------------------------------------------------
    def _figure_payload(self, bits: str, kind: str, local: Dict[str, Any]) -> Dict[str, Any]:
        """Merge knowledge-graph enrichment with the local algebraic spec."""
        record = self.kb.lookup(kind, bits)
        merged: Dict[str, Any] = {
            "bits": bits,
            "label": local.get("label"),
            "element": local.get("element"),
            "parable": local.get("parable"),
            "index": local.get("index"),
        }
        if record is not None:
            merged.update(
                {
                    "iri": record.iri,
                    "label": record.label or merged["label"],
                    "element": record.element or merged["element"],
                    "parable": record.parable or merged["parable"],
                    "index": record.index if record.index is not None else merged["index"],
                    "archetypes": record.archetypes,
                }
            )
        else:
            merged["iri"] = None
            merged["archetypes"] = []
        return merged

    def _consult_geomancy(self) -> Dict[str, Any]:
        mothers = self.entropy.geomantic_mothers()
        chart = GeomanticChart.cast(mothers)
        validate_parity(chart.judge, chart.right_witness, chart.left_witness)  # spec gate

        houses: Dict[str, Dict[str, Any]] = {}
        for place, bits in chart.houses().items():
            spec = GEOMANTIC_BY_BITS[bits]
            houses[place] = self._figure_payload(
                bits,
                "GeomanticSign",
                {
                    "label": spec.name,
                    "element": spec.element,
                    "parable": spec.parable,
                    "index": spec.rank,
                    "kind": "GeomanticSign",
                },
            )

        judge_spec = GEOMANTIC_BY_BITS[chart.judge]
        return {
            "mothers": chart.mothers,
            "houses": houses,
            "judge": houses["Judge"],
            "reconciler": houses["Reconciler"],
            "judge_is_even_figure": chart.judge in EVEN_FIGURES,
            "judge_keyword": judge_spec.keyword,
        }

    def _consult_iching(self) -> Dict[str, Any]:
        line_values = self.entropy.iching_line_values()
        cast = HexagramCast.cast(line_values)
        primary = cast.primary_hexagram
        resultant = cast.resultant_hexagram
        return {
            "line_values": cast.line_values,
            "changing_positions": [p + 1 for p in cast.changing_positions],  # 1-based lines
            "primary": self._figure_payload(
                cast.primary_bits,
                "IChingHexagram",
                {
                    "label": primary.label,
                    "element": primary.element,
                    "parable": primary.judgment,
                    "index": primary.number,
                },
            ),
            "resultant": self._figure_payload(
                cast.resultant_bits,
                "IChingHexagram",
                {
                    "label": resultant.label,
                    "element": resultant.element,
                    "parable": resultant.judgment,
                    "index": resultant.number,
                },
            ),
            "moving_counsel": cast.moving_counsel,
        }

    def _consult_ifa(self) -> Dict[str, Any]:
        bits = self.entropy.ifa_marks()
        left, right = bits[:4], bits[4:]
        left_spec = ODU_PRINCIPALS_BY_BITS[left]
        right_spec = ODU_PRINCIPALS_BY_BITS[right]
        parable = (
            f"Left leg {left_spec.name}: {left_spec.parable} "
            f"Right leg {right_spec.name}: {right_spec.parable} "
            "The left leg leads; the right leg modifies."
        )
        record = self._figure_payload(
            bits,
            "IfaOdu",
            {
                "label": compound_odu_name(left, right),
                "element": None,
                "parable": parable,
                "index": odu_index(left, right),
            },
        )
        return {"bits": bits, "odu": record}

    # ------------------------------------------------------------------
    def _resonance_report(self, sections: Dict[str, Any]) -> Dict[str, Any]:
        report: Dict[str, Any] = {}
        geo = sections.get("geomancy")
        if geo:
            judge_bits = geo["judge"]["bits"]
            report["judge_exact_matches"] = geomantic_matches(judge_bits)
            report["judge_hexagram_resonances"] = hexagram_resonances(judge_bits)
        ich = sections.get("iching")
        if ich:
            report["primary_hexagram_neighbors"] = cross_report(
                ich["primary"]["bits"]
            ).get("transition_neighbors")
        ifa = sections.get("ifa")
        if ifa:
            report["odu_leg_resonances"] = {
                "left": geomantic_matches(ifa["bits"][:4])["geomantic_figure"],
                "right": geomantic_matches(ifa["bits"][4:])["geomantic_figure"],
            }
        return report

    # ------------------------------------------------------------------
    def _compose_counsel(self, agent_id: str, sections: Dict[str, Any]) -> str:
        lines: List[str] = []
        geo = sections.get("geomancy")
        if geo:
            judge = geo["judge"]
            lines.append(
                "SHIELD: The chart judges through "
                f"{judge['label']} - {judge.get('parable') or geo['judge_keyword']}"
            )
            lines.append(
                f"The Reconciler ({geo['reconciler']['label']}) shows how to seat the verdict into the opening situation."
            )
        ich = sections.get("iching")
        if ich:
            primary = ich["primary"]
            lines.append(
                f"TRANSITION: Primary {primary['label']} - {primary.get('parable')}"
            )
            lines.append(f"Line dynamics: {ich['moving_counsel']}")
            if ich["changing_positions"]:
                lines.append(
                    f"Changing line(s) {ich['changing_positions']} resolve toward "
                    f"{ich['resultant']['label']} - {ich['resultant'].get('parable')}"
                )
        ifa = sections.get("ifa")
        if ifa:
            odu = ifa["odu"]
            lines.append(f"CORPUS: Odu {odu['label']} - {odu.get('parable')}")
        lines.append(
            "REFRAMING: The deadlock is not a missing datum but an unchosen frame. "
            "Treat the figures above as three independent samplings of the same "
            "phase space; act where their counsel converges, and where they "
            "diverge, delay that branch - divergence marks the out-of-distribution edge."
        )
        return "\n".join(lines)


__all__ = ["FigureRecord", "KnowledgeBase", "Oracle", "TRADITIONS"]
