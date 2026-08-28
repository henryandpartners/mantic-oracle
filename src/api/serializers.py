"""W3C-compliant JSON-LD serialization of oracle consultations.

Every emitted key is bound in the @context so standard JSON-LD 1.1
processors expand the document into proper triples (verified by
`parse_jsonld` in the test suite). Nested analytical reports are carried
as `@json` literals to preserve their structure losslessly.
"""

from __future__ import annotations

from typing import Any, Dict

MANTIC_IRI = "https://w3id.org/mantic/core#"

MANTIC_CONTEXT: Dict[str, Any] = {
    "mantic": MANTIC_IRI,
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "label": {"@id": "rdfs:label"},
    "binaryVector": "mantic:hasBinaryVector",
    "figureIndex": "mantic:figureIndex",
    "element": "mantic:element",
    "parable": "mantic:parable",
    "keyword": "mantic:keyword",
    "planet": "mantic:planet",
    "agentId": "mantic:agentId",
    "decisionText": "mantic:decisionText",
    "castAt": {"@id": "mantic:castAt", "@type": "xsd:dateTime"},
    "sharesArchetypeWith": "mantic:sharesArchetypeWith",
    "generatesTransitionTo": "mantic:generatesTransitionTo",
    "figure": "mantic:hasFigure",
    "place": "mantic:place",
    "role": "mantic:role",
    "entropyProvider": "mantic:entropyProvider",
    "knowledgeBackend": "mantic:knowledgeBackend",
    "consultedTraditions": "mantic:consultedTraditions",
    "strategicCounsel": "mantic:strategicCounsel",
    "resonances": {"@id": "mantic:resonanceReport", "@type": "@json"},
    "hexagramCast": "mantic:hexagramCast",
    "geomanticChart": "mantic:geomanticChart",
    "lineValues": {"@id": "mantic:lineValues", "@type": "@json"},
    "changingLines": {"@id": "mantic:changingLines", "@type": "@json"},
    "movingCounsel": "mantic:movingCounsel",
    "judge": "mantic:judgeFigure",
    "reconciler": "mantic:reconcilerFigure",
}


def _node(figure: Dict[str, Any], kind: str | None = None) -> Dict[str, Any]:
    """One figure as a JSON-LD node object."""
    effective_kind = figure.get("kind") or figure.get("_kind") or kind
    node: Dict[str, Any] = {}
    if figure.get("iri"):
        node["@id"] = figure["iri"]
    if effective_kind:
        node["@type"] = f"{MANTIC_IRI}{effective_kind}"
    for src, dst in (
        ("label", "label"),
        ("bits", "binaryVector"),
        ("index", "figureIndex"),
        ("element", "element"),
        ("parable", "parable"),
        ("keyword", "keyword"),
        ("planet", "planet"),
    ):
        if figure.get(src) is not None:
            node[dst] = figure[src]
    archetypes = figure.get("archetypes") or []
    if archetypes:
        links = []
        for a in archetypes:
            if a.get("iri"):
                link: Dict[str, Any] = {"@id": a["iri"]}
                if a.get("label"):
                    link["label"] = a["label"]
            else:
                link = {"label": a.get("label")}
            links.append(link)
        node["sharesArchetypeWith"] = links
    return node


def consultation_to_jsonld(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Lift an `Oracle.consult` payload into a JSON-LD document."""
    sections = payload.get("tradition_results", {})

    figures: list[Dict[str, Any]] = []
    geomancy = sections.get("geomancy")
    if geomancy:
        for place, figure in geomancy["houses"].items():
            node = _node(figure, kind="GeomanticSign")
            node["place"] = place
            figures.append(node)
    iching = sections.get("iching")
    if iching:
        primary = _node(iching["primary"], kind="IChingHexagram")
        primary["role"] = "primary"
        resultant = _node(iching["resultant"], kind="IChingHexagram")
        resultant["role"] = "resultant"
        if resultant.get("@id"):
            primary["generatesTransitionTo"] = {"@id": resultant["@id"]}
        figures.extend([primary, resultant])
    ifa = sections.get("ifa")
    if ifa:
        figures.append(_node(ifa["odu"], kind="IfaOdu"))

    doc: Dict[str, Any] = {
        "@context": MANTIC_CONTEXT,
        "@type": f"{MANTIC_IRI}Consultation",
        "@id": payload["consultation_id"],
        "agentId": payload["agent_id"],
        "decisionText": payload["decision_context"],
        "castAt": payload["cast_at"],
        "entropyProvider": payload["entropy_provider"],
        "knowledgeBackend": payload["knowledge_backend"],
        "consultedTraditions": payload["traditions"],
        "figure": figures,
    }
    if iching:
        doc["hexagramCast"] = {
            "@type": f"{MANTIC_IRI}HexagramCast",
            "lineValues": iching["line_values"],
            "changingLines": iching["changing_positions"],
            "movingCounsel": iching["moving_counsel"],
        }
    if geomancy:
        doc["geomanticChart"] = {
            "@type": f"{MANTIC_IRI}GeomanticChart",
            "judge": _node(geomancy["judge"], kind="GeomanticSign"),
            "reconciler": _node(geomancy["reconciler"], kind="GeomanticSign"),
        }
    doc["resonances"] = payload.get("resonances", {})
    doc["strategicCounsel"] = payload.get("strategic_counsel", "")
    return doc


def parse_jsonld(doc: Dict[str, Any]):
    """Parse a JSON-LD document into an rdflib Graph (verification helper)."""
    import json

    from rdflib import Graph

    graph = Graph()
    graph.parse(data=json.dumps(doc), format="json-ld")
    return graph


__all__ = ["MANTIC_CONTEXT", "consultation_to_jsonld", "parse_jsonld"]
