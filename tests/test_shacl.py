"""SHACL validation of the ontology and seed data."""

from __future__ import annotations

from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import RDF, Graph, Literal, Namespace

REPO_ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY = REPO_ROOT / "ontology"
SEED = ONTOLOGY / "seed_data.ttl"
SHAPES = ONTOLOGY / "shapes.shacl.ttl"

MANTIC = Namespace("https://w3id.org/mantic/core#")

CORE = ONTOLOGY / "mantic_core.ttl"

pytestmark = pytest.mark.skipif(
    not SEED.exists(), reason="seed_data.ttl not generated - run scripts/generate_seed.py"
)


def _shapes_graph() -> Graph:
    return Graph().parse(SHAPES, format="turtle")


def _full_store() -> Graph:
    """The production RDF store: ontology (class axioms) + seed data."""
    data = Graph().parse(SEED, format="turtle")
    data.parse(CORE, format="turtle")
    return data


def _run(data: Graph):
    """Validate with pyshacl (kwarg: shacl_graph), with RDFS inference so
    subclass typing (GeomanticSign rdfs:subClassOf ManticFigure) is honored."""
    return validate(data_graph=data, shacl_graph=_shapes_graph(), inference="rdfs")


def test_shapes_file_loads() -> None:
    shapes = _shapes_graph()
    shacl = Namespace("http://www.w3.org/ns/shacl#")
    assert len(shapes) > 20
    assert len(list(shapes.subjects(RDF.type, shacl.NodeShape))) >= 5


def test_seed_data_conforms() -> None:
    data = _full_store()
    conforms, _, text = _run(data)
    assert conforms, f"SHACL violations:\n{text}"


def _corrupted_seed(**mutations) -> Graph:
    """Load the full store and apply programmatic corruption."""
    data = _full_store()
    for cls, action in mutations.items():
        node = next(data.subjects(RDF.type, MANTIC[cls]))
        if action == "widen":
            vec = data.value(node, MANTIC.hasBinaryVector)
            data.remove((node, MANTIC.hasBinaryVector, vec))
            data.add((node, MANTIC.hasBinaryVector, Literal(str(vec) + "1")))
        elif action == "nonbinary":
            vec = data.value(node, MANTIC.hasBinaryVector)
            data.remove((node, MANTIC.hasBinaryVector, vec))
            data.add((node, MANTIC.hasBinaryVector, Literal("x" + str(vec)[1:])))
        elif action == "strip":
            data.remove(
                (node, MANTIC.hasBinaryVector, None)
            )
    return data


def test_width_violation_detected() -> None:
    data = _corrupted_seed(GeomanticSign="widen")
    conforms, _, text = _run(data)
    assert not conforms
    assert "4-digit" in text or "Pattern" in text


def test_nonbinary_vector_detected() -> None:
    data = _corrupted_seed(IChingHexagram="nonbinary")
    conforms, _, _ = _run(data)
    assert not conforms


def test_missing_vector_detected() -> None:
    data = _corrupted_seed(IfaOdu="strip")
    conforms, _, _ = _run(data)
    assert not conforms  # minCount 1 violated
