"""Generate ontology/seed_data.ttl from the canonical tables.

Emits:
  * all 64 King Wen hexagrams (typed, labeled, vector, index, element, judgment)
  * the full 384-edge I Ching dynamic transition graph (one flip per line)
  * all 16 geomantic figures (+ elemental dominance edges)
  * all 256 Ifa odus: 16 Meji (doubled) principals with full parables and
    240 compounds with leg-composed counsel
  * curated cross-system `sharesArchetypeWith` links
  * `resolvesAmbiguity` seeds for the canonical decision-context classes

Run from the repository root:

    python scripts/generate_seed.py

The output is deterministic and committed; regenerate only when the
tables change.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef  # noqa: E402
from rdflib.namespace import XSD  # noqa: E402

from src.core.tables import (  # noqa: E402
    GEOMANTIC_BY_BITS,
    GEOMANTIC_FIGURES,
    GEOMANTY_HEXAGRAM_LINKS,
    HEXAGRAM_ODU_LINKS,
    KING_WEN,
    KING_WEN_BY_BITS,
    ODU_PRINCIPALS,
    ODU_PRINCIPALS_BY_BITS,
    ODU_PRINCIPALS_BY_NAME,
    RESOLVES_AMBIGUITY_SEEDS,
    TRIGRAM_ELEMENT,
    odu_index,
)

MANTIC = Namespace("https://w3id.org/mantic/core#")

ELEMENT_INDIVIDUAL = {
    "Air": MANTIC.ElemAir,
    "Fire": MANTIC.ElemFire,
    "Water": MANTIC.ElemWater,
    "Earth": MANTIC.ElemEarth,
    "Heaven": MANTIC.ElemHeaven,
    "Lake": MANTIC.ElemLake,
    "Thunder": MANTIC.ElemThunder,
    "Wind": MANTIC.ElemWind,
    "Mountain": MANTIC.ElemMountain,
}


def figure_uri(name: str) -> URIRef:
    camel = "".join(part.capitalize() for part in name.split())
    return MANTIC[f"Fig{camel}"]


def hexagram_uri(number: int) -> URIRef:
    return MANTIC[f"Hex{number:02d}"]


def odu_uri(index: int) -> URIRef:
    return MANTIC[f"Odu{index:03d}"]


def build_graph() -> Graph:
    graph = Graph()
    graph.bind("mantic", MANTIC)

    # ------------------------------------------------------------------
    # I Ching: 64 hexagrams
    # ------------------------------------------------------------------
    from src.core.corpus import HEXAGRAM_IMAGES, compound_parable

    for spec in KING_WEN:
        node = hexagram_uri(spec.number)
        graph.add((node, RDF.type, MANTIC.IChingHexagram))
        graph.add((node, RDFS.label, Literal(spec.label)))
        graph.add((node, MANTIC.hasBinaryVector, Literal(spec.bits)))
        graph.add((node, MANTIC.figureIndex, Literal(spec.number)))
        graph.add((node, MANTIC.element, Literal(spec.element)))
        graph.add((node, MANTIC.parable, Literal(spec.judgment)))
        image = HEXAGRAM_IMAGES.get(spec.number)
        if image:
            graph.add((node, MANTIC.imageText, Literal(image)))
        graph.add((node, MANTIC.lowerTrigram, Literal(spec.lower)))
        graph.add((node, MANTIC.upperTrigram, Literal(spec.upper)))
        if spec.element in ELEMENT_INDIVIDUAL:
            graph.add((node, MANTIC.dominatesElement, ELEMENT_INDIVIDUAL[spec.element]))

    # I Ching: 384 transition edges (flip each line of each hexagram)
    for spec in KING_WEN:
        source = hexagram_uri(spec.number)
        for pos in range(6):
            flipped = (
                spec.bits[:pos]
                + ("1" if spec.bits[pos] == "0" else "0")
                + spec.bits[pos + 1 :]
            )
            target = hexagram_uri(KING_WEN_BY_BITS[flipped].number)
            graph.add((source, MANTIC.generatesTransitionTo, target))

    # ------------------------------------------------------------------
    # Geomancy: 16 figures
    # ------------------------------------------------------------------
    for spec in GEOMANTIC_FIGURES:
        node = figure_uri(spec.name)
        graph.add((node, RDF.type, MANTIC.GeomanticSign))
        graph.add((node, RDFS.label, Literal(spec.name)))
        graph.add((node, MANTIC.hasBinaryVector, Literal(spec.bits)))
        graph.add((node, MANTIC.figureIndex, Literal(spec.rank)))
        graph.add((node, MANTIC.element, Literal(spec.element)))
        graph.add((node, MANTIC.parable, Literal(spec.parable)))
        graph.add((node, MANTIC.planet, Literal(spec.planet)))
        graph.add((node, MANTIC.keyword, Literal(spec.keyword)))
        if spec.element in ELEMENT_INDIVIDUAL:
            graph.add((node, MANTIC.dominatesElement, ELEMENT_INDIVIDUAL[spec.element]))

    # ------------------------------------------------------------------
    # Ifa: 256 odus (16 Meji + 240 compounds)
    # ------------------------------------------------------------------
    for left in ODU_PRINCIPALS:
        for right in ODU_PRINCIPALS:
            bits = left.bits + right.bits
            index = odu_index(left.bits, right.bits)
            node = odu_uri(index)
            graph.add((node, RDF.type, MANTIC.IfaOdu))
            graph.add((node, MANTIC.hasBinaryVector, Literal(bits)))
            graph.add((node, MANTIC.figureIndex, Literal(index)))
            if left.name == right.name:
                label = f"{left.name} Meji"
                parable = left.parable
            else:
                label = f"{left.name}-{right.name}"
                parable = compound_parable(left.name, right.name)
            graph.add((node, RDFS.label, Literal(label)))
            graph.add((node, MANTIC.parable, Literal(parable)))
            graph.add((node, MANTIC.leftLeg, Literal(left.name)))
            graph.add((node, MANTIC.rightLeg, Literal(right.name)))

    # ------------------------------------------------------------------
    # Cross-system archetype links
    # ------------------------------------------------------------------
    def meji_uri(principal_name: str) -> URIRef:
        bits = ODU_PRINCIPALS_BY_NAME[principal_name].bits
        return odu_uri(odu_index(bits, bits))

    # 1. every geomantic figure <-> the Meji odu with the same 4-bit pattern
    for spec in GEOMANTIC_FIGURES:
        graph.add((figure_uri(spec.name), MANTIC.sharesArchetypeWith, odu_uri(odu_index(spec.bits, spec.bits))))

    # 2. curated figure <-> hexagram pairings
    for fig_name, hex_number in GEOMANTY_HEXAGRAM_LINKS:
        graph.add((figure_uri(fig_name), MANTIC.sharesArchetypeWith, hexagram_uri(hex_number)))

    # 3. curated hexagram <-> odu pairings
    for hex_number, odu_name in HEXAGRAM_ODU_LINKS:
        graph.add((hexagram_uri(hex_number), MANTIC.sharesArchetypeWith, meji_uri(odu_name)))

    # ------------------------------------------------------------------
    # Decision-context seeds
    # ------------------------------------------------------------------
    context_locals = {
        "Deadlock": MANTIC.Deadlock,
        "ParetoFlat": MANTIC.ParetoFlat,
        "OODSurprise": MANTIC.OODSurprise,
    }
    for source_name, context_name in RESOLVES_AMBIGUITY_SEEDS:
        if source_name.startswith("Odu"):
            node = meji_uri(source_name.removeprefix("Odu"))
        else:
            node = figure_uri(source_name)
        graph.add((node, MANTIC.resolvesAmbiguity, context_locals[context_name]))

    return graph


def verify(graph: Graph) -> None:
    """Structural sanity gates before writing."""
    hexes = list(graph.subjects(RDF.type, MANTIC.IChingHexagram))
    figs = list(graph.subjects(RDF.type, MANTIC.GeomanticSign))
    odus = list(graph.subjects(RDF.type, MANTIC.IfaOdu))
    assert len(hexes) == 64, f"expected 64 hexagrams, got {len(hexes)}"
    assert len(figs) == 16, f"expected 16 figures, got {len(figs)}"
    assert len(odus) == 256, f"expected 256 odus, got {len(odus)}"

    vecs = {kind: set() for kind in (MANTIC.IChingHexagram, MANTIC.GeomanticSign, MANTIC.IfaOdu)}
    for cls in vecs:
        for node in graph.subjects(RDF.type, cls):
            vecs[cls].add(str(graph.value(node, MANTIC.hasBinaryVector)))
    assert len(vecs[MANTIC.IChingHexagram]) == 64
    assert len(vecs[MANTIC.GeomanticSign]) == 16
    assert len(vecs[MANTIC.IfaOdu]) == 256

    transitions = list(graph.triples((None, MANTIC.generatesTransitionTo, None)))
    assert len(transitions) == 384, f"expected 384 transition edges, got {len(transitions)}"


def main() -> int:
    graph = build_graph()
    verify(graph)
    out = REPO_ROOT / "ontology" / "seed_data.ttl"
    graph.serialize(destination=str(out), format="turtle")
    print(f"wrote {out} ({len(graph)} triples)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
