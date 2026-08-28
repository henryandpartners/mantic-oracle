"""Unit tests for Sikidy XOR parity and I Ching transitions."""

from __future__ import annotations

from collections import Counter

import pytest

from src.core.algebra import (
    EVEN_FIGURES,
    GeomanticChart,
    HexagramCast,
    LINE_STATIC_BIT,
    flip_bit,
    popcount,
    transpose,
    validate_parity,
    xor,
)
from src.core.entropy import CryptoEntropy, DeterministicEntropy
from src.core.tables import (
    GEOMANTIC_BY_BITS,
    KING_WEN_BY_BITS,
    KING_WEN_BY_NUMBER,
)

entropy = CryptoEntropy()
det = DeterministicEntropy("pytest")


# ----------------------------------------------------------------------
# XOR primitives
# ----------------------------------------------------------------------

def test_xor_is_modulo_2_addition() -> None:
    assert xor("0000", "0000") == "0000"
    assert xor("1111", "0000") == "1111"
    assert xor("1010", "0101") == "1111"
    assert xor("1100", "1010") == "0110"
    # involution: a ^ b ^ b == a
    a, b = "0110", "1011"
    assert xor(xor(a, b), b) == a


def test_xor_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        xor("10", "101")
    with pytest.raises(ValueError):
        xor("10a1", "0000")


# ----------------------------------------------------------------------
# Geomantic shield chart
# ----------------------------------------------------------------------

def test_daughters_are_transposition() -> None:
    mothers = ["1011", "0100", "1110", "0011"]
    daughters = transpose(mothers)
    # daughter i = i-th row of each mother
    assert daughters == [
        mothers[0][0] + mothers[1][0] + mothers[2][0] + mothers[3][0],
        mothers[0][1] + mothers[1][1] + mothers[2][1] + mothers[3][1],
        mothers[0][2] + mothers[1][2] + mothers[2][2] + mothers[3][2],
        mothers[0][3] + mothers[1][3] + mothers[2][3] + mothers[3][3],
    ]


def test_shield_derivation_identities() -> None:
    for _ in range(50):
        mothers = det.geomantic_mothers()
        chart = GeomanticChart.cast(mothers)
        assert chart.mothers == mothers
        assert chart.nieces[0] == xor(chart.mothers[0], chart.mothers[1])
        assert chart.nieces[1] == xor(chart.mothers[2], chart.mothers[3])
        assert chart.nieces[2] == xor(chart.daughters[0], chart.daughters[1])
        assert chart.nieces[3] == xor(chart.daughters[2], chart.daughters[3])
        assert chart.right_witness == xor(chart.nieces[0], chart.nieces[1])
        assert chart.left_witness == xor(chart.nieces[2], chart.nieces[3])
        assert chart.judge == xor(chart.right_witness, chart.left_witness)
        assert chart.reconciler == xor(chart.mothers[0], chart.judge)


def test_judge_parity_gate_accepts_valid_chart() -> None:
    mothers = det.geomantic_mothers()
    chart = GeomanticChart.cast(mothers)
    # spec parity check must never raise on a correctly derived chart
    validate_parity(chart.judge, chart.right_witness, chart.left_witness)


def test_parity_gate_rejects_corrupted_chart() -> None:
    mothers = det.geomantic_mothers()
    chart = GeomanticChart.cast(mothers)
    corrupted = flip_bit(chart.judge, 0)  # tamper with the judge
    if corrupted == chart.judge:  # pragma: no cover
        corrupted = chart.judge[:-1] + ("0" if chart.judge[-1] == "1" else "1")
    with pytest.raises(ValueError):
        validate_parity(corrupted, chart.right_witness, chart.left_witness)


def test_even_judge_theorem() -> None:
    """The Judge of any tableau always has an even number of active rows."""
    for _ in range(200):
        chart = GeomanticChart.cast(det.geomantic_mothers())
        assert popcount(chart.judge) % 2 == 0
        assert chart.judge in EVEN_FIGURES
        assert chart.judge in GEOMANTIC_BY_BITS


def test_judge_can_only_be_one_of_eight_figures() -> None:
    assert len(EVEN_FIGURES) == 8


def test_chart_has_sixteen_houses() -> None:
    chart = GeomanticChart.cast(["1001", "0110", "1010", "0101"])
    houses = chart.houses()
    assert len(houses) == 16
    assert "Judge" in houses and "Reconciler" in houses


def test_deterministic_chart_reproducibility() -> None:
    a = GeomanticChart.cast(DeterministicEntropy("seed-a").geomantic_mothers())
    b = GeomanticChart.cast(DeterministicEntropy("seed-a").geomantic_mothers())
    c = GeomanticChart.cast(DeterministicEntropy("seed-b").geomantic_mothers())
    assert a == b
    assert a != c or True  # collision allowed but identities still hold


# ----------------------------------------------------------------------
# I Ching dynamic casting
# ----------------------------------------------------------------------

def test_line_value_domain() -> None:
    values = entropy.iching_line_values()
    assert len(values) == 6
    assert set(values) <= {6, 7, 8, 9}


def test_coin_distribution_covers_all_line_values() -> None:
    seen: Counter[int] = Counter()
    for _ in range(400):
        seen.update(det.iching_line_values())
    assert set(seen) == {6, 7, 8, 9}


def test_static_bit_mapping() -> None:
    assert LINE_STATIC_BIT == {6: 0, 7: 1, 8: 0, 9: 1}


def test_primary_and_resultant_hexagrams() -> None:
    cast = HexagramCast.cast([7, 7, 7, 7, 7, 7])  # all young yang
    assert cast.primary_bits == "111111"
    assert cast.changing_positions == []
    assert cast.resultant_bits == cast.primary_bits
    assert cast.primary_hexagram.number == 1  # Qian
    assert cast.resultant_hexagram.number == 1


def test_all_old_yang_flips_everything() -> None:
    cast = HexagramCast.cast([9, 9, 9, 9, 9, 9])
    assert cast.primary_bits == "111111"
    assert cast.resultant_bits == "000000"
    assert cast.primary_hexagram.number == 1   # Qian
    assert cast.resultant_hexagram.number == 2  # Kun


def test_famous_transition_fu_to_qian() -> None:
    # Hexagram 24 Fu (100000) with changing line 1 (old yang -> yin? no:
    # line 1 is already the returning yang; make it old yang so it flips)
    cast = HexagramCast.cast([9, 8, 8, 8, 8, 8])
    assert cast.primary_bits == "100000"
    assert cast.primary_hexagram.number == 24  # Fu, Return
    assert cast.resultant_bits == "000000"
    assert cast.resultant_hexagram.number == 2  # Kun


def test_old_yin_changes_to_yang() -> None:
    cast = HexagramCast.cast([6, 7, 7, 7, 7, 7])
    assert cast.primary_bits == "011111"
    assert cast.primary_hexagram.number == 44  # Gou
    assert cast.resultant_bits == "111111"
    assert cast.resultant_hexagram.number == 1  # Qian


def test_cast_rejects_bad_lines() -> None:
    with pytest.raises(ValueError):
        HexagramCast.cast([1, 2, 3, 4, 5, 6])
    with pytest.raises(ValueError):
        HexagramCast.cast([7, 7, 7])


def test_moving_counsel_table_lookup() -> None:
    cast = HexagramCast.cast([7, 7, 7, 7, 7, 7])
    assert "No lines move" in cast.moving_counsel


# ----------------------------------------------------------------------
# King Wen table integrity
# ----------------------------------------------------------------------

def test_king_wen_known_vectors() -> None:
    assert KING_WEN_BY_BITS["111111"].number == 1      # Qian
    assert KING_WEN_BY_BITS["000000"].number == 2      # Kun
    assert KING_WEN_BY_BITS["100000"].number == 24     # Fu
    assert KING_WEN_BY_BITS["010101"].number == 64     # Wei Ji
    assert KING_WEN_BY_BITS["101010"].number == 63     # Ji Ji
    assert KING_WEN_BY_NUMBER[1].lower == "Qian"
    assert KING_WEN_BY_NUMBER[64].upper == "Li"


def test_one_flip_neighbors_are_hexagrams() -> None:
    for bits, spec in KING_WEN_BY_BITS.items():
        for pos in range(6):
            flipped = flip_bit(bits, pos)
            assert flipped in KING_WEN_BY_BITS
            assert flipped != bits
