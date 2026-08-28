"""End-to-end consultation & JSON-LD payload verification (no Neo4j needed)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.api.serializers import consultation_to_jsonld, parse_jsonld
from src.core.algebra import GeomanticChart, HexagramCast
from src.core.entropy import DeterministicEntropy
from src.core.oracle import KnowledgeBase, Oracle
from src.core.tables import KING_WEN_BY_BITS

REPO_ROOT = Path(__file__).resolve().parents[1]
SEED = REPO_ROOT / "ontology" / "seed_data.ttl"

pytestmark = pytest.mark.skipif(
    not SEED.exists(), reason="seed_data.ttl not generated - run scripts/generate_seed.py"
)


@pytest.fixture(scope="module")
def oracle() -> Oracle:
    return Oracle(entropy=DeterministicEntropy("oracle-flow"))


@pytest.fixture(scope="module")
def payload(oracle: Oracle) -> dict:
    return oracle.consult(
        agent_id="planner-1",
        decision_context="Two equivalent routing strategies with equal expected utility; cannot break the tie.",
        target_traditions=["all"],
    )


def test_consultation_metadata(payload: dict) -> None:
    assert payload["consultation_id"].startswith("urn:uuid:")
    assert payload["agent_id"] == "planner-1"
    assert "routing strategies" in payload["decision_context"]
    assert payload["knowledge_backend"] == "rdflib-fallback"
    assert payload["traditions"] == ["geomancy", "iching", "ifa"]


def test_geomantic_section(payload: dict) -> None:
    geo = payload["tradition_results"]["geomancy"]
    houses = geo["houses"]
    assert len(houses) == 16
    assert geo["judge"]["bits"] in {f["bits"] for f in houses.values()}
    # every house is a real figure with knowledge-graph enrichment
    for figure in houses.values():
        assert figure["label"]
        assert figure["parable"]
        assert set(figure["bits"]) <= {"0", "1"}
    assert geo["judge_is_even_figure"] is True


def test_iching_section(payload: dict) -> None:
    ich = payload["tradition_results"]["iching"]
    assert set(ich["line_values"]) <= {6, 7, 8, 9}
    primary = HexagramCast.cast(ich["line_values"])
    assert primary.primary_bits == ich["primary"]["bits"]
    assert primary.resultant_bits == ich["resultant"]["bits"]
    assert primary.primary_hexagram.label == ich["primary"]["label"]
    assert KING_WEN_BY_BITS[ich["primary"]["bits"]].number == ich["primary"]["index"]
    assert isinstance(ich["moving_counsel"], str) and ich["moving_counsel"]


def test_ifa_section(payload: dict) -> None:
    ifa = payload["tradition_results"]["ifa"]
    bits = ifa["bits"]
    assert len(bits) == 8
    assert set(bits) <= {"0", "1"}
    odu = ifa["odu"]
    assert 1 <= odu["index"] <= 256
    assert odu["label"]
    assert "Meji" in odu["label"] or "-" in odu["label"]


def test_resonances_present(payload: dict) -> None:
    res = payload["resonances"]
    assert "judge_exact_matches" in res
    assert res["judge_exact_matches"]["geomantic_figure"] is not None
    assert len(res["judge_hexagram_resonances"]) == 3
    assert "odu_leg_resonances" in res


def test_strategic_counsel_composition(payload: dict) -> None:
    counsel = payload["strategic_counsel"]
    assert "SHIELD:" in counsel
    assert "TRANSITION:" in counsel
    assert "CORPUS:" in counsel
    assert "REFRAMING:" in counsel


def test_jsonld_roundtrip(payload: dict) -> None:
    doc = consultation_to_jsonld(payload)
    assert doc["@context"]["mantic"] == "https://w3id.org/mantic/core#"
    assert doc["@type"] == "https://w3id.org/mantic/core#Consultation"
    assert doc["@id"].startswith("urn:uuid:")
    graph = parse_jsonld(doc)
    triples = len(graph)
    assert triples > 20
    # serialization is stable JSON
    text = json.dumps(doc)
    assert json.loads(text) == doc


def test_knowledge_base_fallback_lookup() -> None:
    kb = KnowledgeBase()  # no bridge -> rdflib fallback
    figure = kb.lookup("GeomanticSign", "1111")
    assert figure is not None
    assert figure.label == "Via"
    hexagram = kb.lookup("IChingHexagram", "100000")
    assert hexagram is not None
    assert hexagram.index == 24
    odu = kb.lookup("IfaOdu", "11111111")
    assert odu is not None
    assert "Ogbe" in odu.label


def test_knowledge_base_archetype_traversal() -> None:
    kb = KnowledgeBase()
    via = kb.lookup("GeomanticSign", "1111")
    assert via is not None
    labels = {a.get("label") for a in via.archetypes}
    # Via links to Qian and to Ogbe Meji by seed
    assert any("Qian" in (l or "") for l in labels)
    assert any("Ogbe" in (l or "") for l in labels)


def test_subset_traditions() -> None:
    oracle = Oracle(entropy=DeterministicEntropy("subset"))
    payload = oracle.consult("a", "ctx", ["iching"])
    assert payload["traditions"] == ["iching"]
    assert set(payload["tradition_results"]) == {"iching"}


def test_unknown_tradition_rejected() -> None:
    oracle = Oracle(entropy=DeterministicEntropy("subset"))
    with pytest.raises(ValueError):
        oracle.consult("a", "ctx", ["tarot"])


def test_reproducibility() -> None:
    a = Oracle(entropy=DeterministicEntropy("same")).consult("a", "ctx")
    b = Oracle(entropy=DeterministicEntropy("same")).consult("a", "ctx")
    assert a["tradition_results"]["geomancy"]["mothers"] == b["tradition_results"]["geomancy"]["mothers"]
    assert a["tradition_results"]["ifa"]["bits"] == b["tradition_results"]["ifa"]["bits"]


def test_geomantic_chart_reconstructs_from_payload(payload: dict) -> None:
    geo = payload["tradition_results"]["geomancy"]
    chart = GeomanticChart.cast(geo["mothers"])
    assert chart.judge == geo["judge"]["bits"]
    assert chart.reconciler == geo["reconciler"]["bits"]


def test_mcp_tool_function() -> None:
    """The MCP tool wraps the same code path (no MCP SDK required)."""
    from src.api.mcp_server import consult

    doc = consult(
        agent_id="mcp-test",
        decision_context="deadlock between two equal deployments",
        target_traditions=["geomancy"],
    )
    assert doc["@type"] == "https://w3id.org/mantic/core#Consultation"
    assert any(f.get("place") == "Judge" for f in doc["figure"])
