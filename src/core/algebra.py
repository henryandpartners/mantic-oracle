"""Modulo-2 algebraic engine: Sikidy tableau arithmetic and Zhouyi transitions.

Geomancy (Sikidy / Arabic Geomancy)
-----------------------------------
The 16-place shield chart is closed under XOR:

    Mothers  M1..M4  <- entropy (4 bits each)
    Daughters D1..D4 <- column-wise transposition of the Mothers
    Nieces   N1 = M1 ^ M2      N2 = M3 ^ M4
             N3 = D1 ^ D2      N4 = D3 ^ D4
    Witnesses WR = N1 ^ N2     WL = N3 ^ N4
    Judge     J  = WR ^ WL
    Reconciler R = M1 ^ J

Two structural theorems are enforced as validators:

  T1 (parity):  J == WR ^ WL (definitionally true; guarded against drift),
  T2 (even judge): the Judge always carries an even number of active rows,
      hence only 8 of the 16 figures can ever judge a chart.

I Ching
-------
Line values in {6,7,8,9}:

    6 old yin   -> static bit 0, changing
    7 young yang -> static bit 1, static
    8 young yin  -> static bit 0, static
    9 old yang  -> static bit 1, changing

The primary hexagram uses the static bits; flipping every changing line
yields the resultant hexagram.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from pydantic import BaseModel, Field, model_validator

from .tables import (
    CHANGING_LINE_COUNSEL,
    GEOMANTIC_BY_BITS,
    KING_WEN_BY_BITS,
    HexagramSpec,
)

#################################################################
# Bitwise primitives
#################################################################


def xor(left: str, right: str) -> str:
    """Per-bit modulo-2 addition (XOR) of two equal-length bit strings."""
    if len(left) != len(right):
        raise ValueError(f"XOR operands must be equal length: {left!r} vs {right!r}")
    if any(c not in "01" for c in left + right):
        raise ValueError("XOR operands must be binary strings")
    return "".join(str(int(a) ^ int(b)) for a, b in zip(left, right))


def popcount(bits: str) -> int:
    """Number of active (1) rows."""
    return sum(int(c) for c in bits)


def flip_bit(bits: str, position: int) -> str:
    """Flip the bit at `position` (0 = first character / bottom line)."""
    if not 0 <= position < len(bits):
        raise IndexError(f"position {position} out of range for {bits!r}")
    return bits[:position] + ("1" if bits[position] == "0" else "0") + bits[position + 1 :]


#################################################################
# Geomantic shield chart
#################################################################


def transpose(mothers: List[str]) -> List[str]:
    """Derive the four Daughters by column-wise transposition.

    Daughter i takes row i of each Mother (Mothers are rows of the matrix,
    Daughters are its columns).
    """
    if len(mothers) != 4 or any(len(m) != 4 for m in mothers):
        raise ValueError("transpose expects exactly four 4-bit Mothers")
    return ["".join(m[i] for m in mothers) for i in range(4)]


class GeomanticChart(BaseModel):
    """The complete 16-place geomantic tableau, XOR-derived and validated."""

    mothers: List[str] = Field(..., min_length=4, max_length=4)
    daughters: List[str] = Field(..., min_length=4, max_length=4)
    nieces: List[str] = Field(..., min_length=4, max_length=4)
    right_witness: str
    left_witness: str
    judge: str
    reconciler: str

    @model_validator(mode="after")
    def _check_modulo2_identities(self) -> "GeomanticChart":
        m, d, n = self.mothers, self.daughters, self.nieces
        checks: List[Tuple[str, str, str]] = [
            ("N1 = M1 ^ M2", n[0], xor(m[0], m[1])),
            ("N2 = M3 ^ M4", n[1], xor(m[2], m[3])),
            ("N3 = D1 ^ D2", n[2], xor(d[0], d[1])),
            ("N4 = D3 ^ D4", n[3], xor(d[2], d[3])),
            ("WR = N1 ^ N2", self.right_witness, xor(n[0], n[1])),
            ("WL = N3 ^ N4", self.left_witness, xor(n[2], n[3])),
            ("J  = WR ^ WL", self.judge, xor(self.right_witness, self.left_witness)),
            ("R  = M1 ^ J", self.reconciler, xor(m[0], self.judge)),
        ]
        for label, got, expected in checks:
            if got != expected:
                raise ValueError(
                    f"Modulo-2 parity violation: {label}: got {got}, expected {expected}"
                )
        if popcount(self.judge) % 2 != 0:
            # Structurally impossible for a correct tableau.
            raise ValueError(
                "Even-judge theorem violated: judge popcount must be even "
                f"(judge={self.judge})"
            )
        return self

    @classmethod
    def cast(cls, mothers: List[str]) -> "GeomanticChart":
        """Derive the full chart from the four Mothers."""
        daughters = transpose(mothers)
        nieces = [
            xor(mothers[0], mothers[1]),
            xor(mothers[2], mothers[3]),
            xor(daughters[0], daughters[1]),
            xor(daughters[2], daughters[3]),
        ]
        right_witness = xor(nieces[0], nieces[1])
        left_witness = xor(nieces[2], nieces[3])
        judge = xor(right_witness, left_witness)
        reconciler = xor(mothers[0], judge)
        return cls(
            mothers=list(mothers),
            daughters=daughters,
            nieces=nieces,
            right_witness=right_witness,
            left_witness=left_witness,
            judge=judge,
            reconciler=reconciler,
        )

    def houses(self) -> Dict[str, str]:
        """All 16 named places of the shield, in derivation order."""
        places: Dict[str, str] = {}
        for i in range(4):
            places[f"Mother {i + 1}"] = self.mothers[i]
            places[f"Daughter {i + 1}"] = self.daughters[i]
            places[f"Niece {i + 1}"] = self.nieces[i]
        places["Right Witness"] = self.right_witness
        places["Left Witness"] = self.left_witness
        places["Judge"] = self.judge
        places["Reconciler"] = self.reconciler
        return places


#: The eight figures that can legally appear as Judge (even popcount).
EVEN_FIGURES = frozenset(b for b in GEOMANTIC_BY_BITS if popcount(b) % 2 == 0)


#################################################################
# I Ching dynamic casting
#################################################################

#: static bit contributed by each line value
LINE_STATIC_BIT = {6: 0, 7: 1, 8: 0, 9: 1}
#: whether the line transforms
LINE_CHANGING = {6: True, 7: False, 8: False, 9: True}


class HexagramCast(BaseModel):
    """A dynamic Zhouyi state sample (six lines, bottom first)."""

    line_values: List[int] = Field(..., min_length=6, max_length=6)
    primary_bits: str
    resultant_bits: str
    changing_positions: List[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_line_semantics(self) -> "HexagramCast":
        if any(v not in LINE_STATIC_BIT for v in self.line_values):
            raise ValueError(f"line values must be in {{6,7,8,9}}: {self.line_values}")
        primary = "".join(str(LINE_STATIC_BIT[v]) for v in self.line_values)
        changing = [i for i, v in enumerate(self.line_values) if LINE_CHANGING[v]]
        if self.primary_bits != primary:
            raise ValueError(
                f"primary mismatch: {self.primary_bits} != derived {primary}"
            )
        if sorted(self.changing_positions) != sorted(changing):
            raise ValueError(
                f"changing positions mismatch: {self.changing_positions} != {changing}"
            )
        resultant = self.primary_bits
        for pos in changing:
            resultant = flip_bit(resultant, pos)
        if self.resultant_bits != resultant:
            raise ValueError(
                f"resultant mismatch: {self.resultant_bits} != derived {resultant}"
            )
        return self

    @classmethod
    def cast(cls, line_values: List[int]) -> "HexagramCast":
        """Build a cast from six coin-derived line values (bottom first)."""
        if len(line_values) != 6:
            raise ValueError("a hexagram needs exactly six line values")
        if any(v not in LINE_STATIC_BIT for v in line_values):
            raise ValueError(f"line values must be in {{6,7,8,9}}: {line_values}")
        primary = "".join(str(LINE_STATIC_BIT[v]) for v in line_values)
        changing = [i for i, v in enumerate(line_values) if LINE_CHANGING[v]]
        resultant = primary
        for pos in changing:
            resultant = flip_bit(resultant, pos)
        return cls(
            line_values=list(line_values),
            primary_bits=primary,
            resultant_bits=resultant,
            changing_positions=changing,
        )

    @property
    def primary_hexagram(self) -> HexagramSpec:
        return KING_WEN_BY_BITS[self.primary_bits]

    @property
    def resultant_hexagram(self) -> HexagramSpec:
        return KING_WEN_BY_BITS[self.resultant_bits]

    @property
    def moving_counsel(self) -> str:
        return CHANGING_LINE_COUNSEL[len(self.changing_positions)]


def validate_parity(judge: str, right_witness: str, left_witness: str) -> None:
    """Explicit mathematical parity gate (spec requirement).

    Rejects any chart whose Judge is not congruent to WR xor WL.
    """
    if judge != xor(right_witness, left_witness):
        raise ValueError(
            "Rejected chart: Judge parity failed "
            f"(J={judge} != WR^{left_witness.rstrip() and right_witness} -> "
            f"{xor(right_witness, left_witness)})"
        )


__all__ = [
    "EVEN_FIGURES",
    "GeomanticChart",
    "HexagramCast",
    "LINE_CHANGING",
    "LINE_STATIC_BIT",
    "flip_bit",
    "popcount",
    "transpose",
    "validate_parity",
    "xor",
]
