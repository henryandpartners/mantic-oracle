"""Structural inference engine — the graph that grows.

The curated `sharesArchetypeWith` triples were placed by hand. This
module *derives* new resonance from the structure of the phase space
itself. Every rule is transparent: a link is proposed together with
its basis and a confidence.

Rules
-----
mirror      (confidence 0.90) - vectors related by full complement
            (every bit flipped). The two figures are one archetype
            seen from opposite conditions: Via/Populus (1111/0000),
            Laetitia/Tristitia (1000/0110)... the classic
            activation/inversion axis of geomancy.

drift       (confidence 0.55) - Hamming distance 1 within a system.
            One changed row/line: the same figure one decision away.

rotation    (confidence 0.75) - geomantic inversion (the figure read
            upside-down, row order reversed). Classical geomancy
            treats these as cousin figures.

same-element
            (confidence 0.40, geomancy only) - figures sharing
            elemental dominance resonate in domain though not in
            structure.

Inferred links never overwrite curated ones; they are additive, and
always carry `inferred: true` + `basis` so consumers can weigh them.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .tables import GEOMANTIC_FIGURES, KING_WEN, ODU_PRINCIPALS


def _invert(bits: str) -> str:
    return "".join("1" if b == "0" else "0" for b in bits)


def _reverse(bits: str) -> str:
    return bits[::-1]


def _geomantic_by_bits() -> Dict[str, Any]:
    return {f.bits: f for f in GEOMANTIC_FIGURES}


def _hex_by_bits() -> Dict[str, Any]:
    return {h.bits: h for h in KING_WEN}


def _odu_by_bits() -> Dict[str, Any]:
    return {o.bits: o for o in ODU_PRINCIPALS}


def infer_for_bits(bits: str) -> List[Dict[str, Any]]:
    """Infer resonances for one vector, whatever its width.

    Returns a list of {figure, system, bits, basis, confidence} dicts,
    strongest first. Curated links are not repeated here - callers
    merge both.
    """
    out: List[Dict[str, Any]] = []

    if len(bits) == 4:
        geo = _geomantic_by_bits()
        # mirror: full complement
        m = geo.get(_invert(bits))
        if m is not None:
            out.append({
                "figure": m.name, "system": "geomancy", "bits": m.bits,
                "basis": "mirror (full complement)", "confidence": 0.90,
            })
        # rotation: figure read upside-down
        r = geo.get(_reverse(bits))
        if r is not None and r.bits != bits:
            out.append({
                "figure": r.name, "system": "geomancy", "bits": r.bits,
                "basis": "rotation (read upside-down)", "confidence": 0.75,
            })
        # drift: hamming-1 neighbours
        for i in range(4):
            d = geo.get(bits[:i] + ("1" if bits[i] == "0" else "0") + bits[i + 1:])
            if d is not None:
                out.append({
                    "figure": d.name, "system": "geomancy", "bits": d.bits,
                    "basis": f"drift (row {i + 1} changed)", "confidence": 0.55,
                })
        # same element
        me = geo.get(bits)
        if me is not None:
            for f in GEOMANTIC_FIGURES:
                if f.bits != bits and f.element == me.element:
                    out.append({
                        "figure": f.name, "system": "geomancy", "bits": f.bits,
                        "basis": f"same element ({me.element})", "confidence": 0.40,
                    })
        # cross-system: the mirrored Meji odu
        odu = _odu_by_bits().get(_invert(bits) + _invert(bits))
        if odu is not None:
            out.append({
                "figure": f"{odu.name} Meji", "system": "ifa",
                "bits": odu.bits + odu.bits,
                "basis": "mirror odu (doubled complement)", "confidence": 0.80,
            })

    elif len(bits) == 6:
        hx = _hex_by_bits()
        for i in range(6):
            d = hx.get(bits[:i] + ("1" if bits[i] == "0" else "0") + bits[i + 1:])
            if d is not None:
                out.append({
                    "figure": d.label, "system": "iching", "bits": d.bits,
                    "basis": f"drift (line {i + 1} changed)", "confidence": 0.55,
                })
        r = hx.get(_reverse(bits))
        if r is not None and r.bits != bits:
            out.append({
                "figure": r.label, "system": "iching", "bits": r.bits,
                "basis": "rotation (hexagram inverted)", "confidence": 0.70,
            })

    elif len(bits) == 8:
        left, right = bits[:4], bits[4:]
        odus = _odu_by_bits()
        # the swapped-leg odu: X-Y read as Y-X is its traditional twin
        swapped = right + left
        l, r = odus.get(left), odus.get(right)
        if l is not None and r is not None and left != right:
            out.append({
                "figure": f"{r.name}-{l.name}", "system": "ifa",
                "bits": swapped,
                "basis": "leg-twin (legs exchanged)", "confidence": 0.85,
            })

    # dedupe by (figure, basis), sort strongest first
    seen = set()
    unique = []
    for link in out:
        key = (link["figure"], link["basis"])
        if key not in seen:
            seen.add(key)
            unique.append(link)
    return sorted(unique, key=lambda x: -x["confidence"])


def inferred_report(bits: str) -> Dict[str, Any]:
    """Consumer-facing shape for lookup_figure / resonances."""
    return {"vector": bits, "inferredEchoes": infer_for_bits(bits)}


__all__ = ["infer_for_bits", "inferred_report"]
