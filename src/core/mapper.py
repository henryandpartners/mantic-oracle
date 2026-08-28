"""Cross-system bitwise alignment and resonance matching.

The three systems sample different bit-widths (4 / 6 / 8) but the same
binary phase-space.  This module aligns vectors across widths:

  * exact leg matching - a geomantic figure resonates *exactly* with the
    principal Ifa odu sharing its 4-bit pattern (and with its Meji form);
  * sliding-window resonance - a 4-bit figure scores against a 6-bit
    hexagram by its best-aligned window (position matters: the hexagram's
    lower positions are its root);
  * transition resonance - hexagram pairs whose King Wen distance is one
    flipped line form the dynamic state machine edges.
"""

from __future__ import annotations

from typing import Dict, List

from .tables import (
    GEOMANTIC_BY_BITS,
    KING_WEN,
    KING_WEN_BY_BITS,
    ODU_PRINCIPALS_BY_BITS,
    compound_odu_name,
    odu_index,
)


def normalize(bits: str) -> str:
    """Validate and canonicalize a binary vector."""
    bits = bits.strip()
    if not bits or any(c not in "01" for c in bits):
        raise ValueError(f"not a binary vector: {bits!r}")
    return bits


def hamming(a: str, b: str) -> int:
    """Number of differing positions between equal-length vectors."""
    if len(a) != len(b):
        raise ValueError(f"hamming requires equal lengths: {a!r} vs {b!r}")
    return sum(x != y for x, y in zip(a, b))


def window_resonance(figure_bits: str, hexagram_bits: str) -> float:
    """Best sliding-window similarity in [0, 1].

    The shorter vector slides across the longer one; the score is the
    maximum fraction of matching bits over any window alignment.
    """
    short, long = sorted([figure_bits, hexagram_bits], key=len)
    span = len(long) - len(short)
    best = 0.0
    for offset in range(span + 1):
        window = long[offset : offset + len(short)]
        score = 1.0 - hamming(short, window) / len(short)
        best = max(best, score)
    return best


def geomantic_matches(bits4: str) -> Dict[str, object]:
    """Everything that shares the exact 4-bit pattern across systems."""
    figure = GEOMANTIC_BY_BITS.get(bits4)
    odu = ODU_PRINCIPALS_BY_BITS.get(bits4)
    meji_bits = bits4 + bits4
    return {
        "geomantic_figure": None if figure is None else {
            "rank": figure.rank,
            "name": figure.name,
            "planet": figure.planet,
            "element": figure.element,
            "keyword": figure.keyword,
            "parable": figure.parable,
        },
        "ifa_principal": None if odu is None else {
            "rank": odu.rank,
            "name": odu.name,
            "bits": odu.bits,
            "parable": odu.parable,
        },
        "ifa_meji_vector": meji_bits,
        "ifa_meji_name": None if odu is None else compound_odu_name(bits4, bits4),
        "ifa_meji_index": None if odu is None else odu_index(bits4, bits4),
    }


def hexagram_resonances(bits4: str, top: int = 3) -> List[Dict[str, object]]:
    """Rank hexagrams by sliding-window resonance with a 4-bit figure."""
    scored = sorted(
        (
            {
                "number": h.number,
                "name": h.label,
                "bits": h.bits,
                "element": h.element,
                "score": round(window_resonance(bits4, h.bits), 4),
            }
            for h in KING_WEN
        ),
        key=lambda item: (-item["score"], item["number"]),  # type: ignore[index]
    )
    return scored[:top]


def transition_neighbors(hex_bits: str) -> List[Dict[str, object]]:
    """The six one-flip neighbors of a hexagram (state-machine edges)."""
    neighbors: List[Dict[str, object]] = []
    for pos in range(len(hex_bits)):
        flipped = (
            hex_bits[:pos]
            + ("1" if hex_bits[pos] == "0" else "0")
            + hex_bits[pos + 1 :]
        )
        target = KING_WEN_BY_BITS[flipped]
        neighbors.append(
            {
                "flip_line": pos + 1,
                "target_number": target.number,
                "target_name": target.label,
                "target_bits": target.bits,
            }
        )
    return neighbors


def cross_report(bits: str) -> Dict[str, object]:
    """Full cross-system resonance report for any binary vector."""
    bits = normalize(bits)
    report: Dict[str, object] = {
        "vector": bits,
        "width": len(bits),
    }
    if len(bits) == 4:
        report["exact_matches"] = geomantic_matches(bits)
        report["hexagram_resonances"] = hexagram_resonances(bits)
    elif len(bits) == 6:
        hexagram = KING_WEN_BY_BITS.get(bits)
        if hexagram is not None:
            report["hexagram"] = {
                "number": hexagram.number,
                "name": hexagram.label,
                "element": hexagram.element,
                "judgment": hexagram.judgment,
            }
        report["transition_neighbors"] = transition_neighbors(bits)
        report["leg_decomposition"] = {
            "lower_trigram": bits[:3],
            "upper_trigram": bits[3:],
            "lower_4bit_window": bits[:4],
            "upper_4bit_window": bits[2:],
        }
    elif len(bits) == 8:
        left, right = bits[:4], bits[4:]
        legs = geomantic_matches(left)
        report["odu"] = {
            "name": compound_odu_name(left, right),
            "index": odu_index(left, right),
            "left_leg": legs["ifa_principal"],
            "right_leg": geomantic_matches(right)["ifa_principal"],
        }
    return report


__all__ = [
    "cross_report",
    "geomantic_matches",
    "hamming",
    "hexagram_resonances",
    "normalize",
    "transition_neighbors",
    "window_resonance",
]
