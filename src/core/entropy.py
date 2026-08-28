"""Entropy sources for mantic sampling.

Two implementations share one protocol:

  * :class:`CryptoEntropy` - `secrets`-based cryptographic randomness for
    live consultations (unpredictable, ritual-grade).
  * :class:`DeterministicEntropy` - a SHA-256 counter DRBG for reproducible
    consultations (tests, replay audits, deterministic pipelines).
"""

from __future__ import annotations

import hashlib
import secrets
from typing import List, Protocol, Sequence


class EntropySource(Protocol):
    """Anything that can yield mantic bits."""

    def bit(self) -> int:
        """Return a single uniformly distributed bit (0 or 1)."""

    def bits(self, n: int) -> str:
        """Return `n` bits as a string of '0'/'1'."""

    def geomantic_mothers(self) -> List[str]:
        """Return the four 4-bit Mothers."""

    def iching_line_values(self) -> List[int]:
        """Return six line values in {6, 7, 8, 9}, bottom line first."""

    def ifa_marks(self) -> str:
        """Return the 8-bit odu vector (left leg then right leg)."""


class CryptoEntropy:
    """Cryptographically secure entropy (`secrets`).

    The I Ching sampling reproduces the three-coin method: each coin is
    heads (3) or tails (2); three coins per line yield sums in {6,7,8,9}:

        6 = old yin  (changing to yang)
        7 = young yang (static yang)
        8 = young yin  (static yin)
        9 = old yang (changing to yin)
    """

    provider_name = "CryptoEntropy(secrets)"

    def bit(self) -> int:
        return secrets.choice((0, 1))

    def bits(self, n: int) -> str:
        return "".join(str(self.bit()) for _ in range(n))

    def geomantic_mothers(self) -> List[str]:
        return [self.bits(4) for _ in range(4)]

    def iching_line_values(self) -> List[int]:
        return [
            sum(secrets.choice((2, 3)) for _ in range(3))  # three coins
            for _ in range(6)
        ]

    def ifa_marks(self) -> str:
        return self.bits(8)


class DeterministicEntropy:
    """Reproducible SHA-256 counter-mode DRBG.

    Not for live divination - used by tests, golden-file pipelines and
    audit replays where the same seed must yield the same chart.
    """

    provider_name = "DeterministicEntropy(sha256-ctr)"

    def __init__(self, seed: str | bytes = "dvsytoe") -> None:
        self._seed: bytes = seed.encode("utf-8") if isinstance(seed, str) else seed
        self._counter = 0
        self._buffer = ""

    def _refill(self) -> None:
        digest = hashlib.sha256(self._seed + str(self._counter).encode("ascii")).digest()
        self._buffer += f"{int.from_bytes(digest, 'big'):0256b}"
        self._counter += 1

    def bit(self) -> int:
        if not self._buffer:
            self._refill()
        bit, self._buffer = self._buffer[0], self._buffer[1:]
        return int(bit)

    def bits(self, n: int) -> str:
        return "".join(str(self.bit()) for _ in range(n))

    def geomantic_mothers(self) -> List[str]:
        return [self.bits(4) for _ in range(4)]

    def iching_line_values(self) -> List[int]:
        values: List[int] = []
        for _ in range(6):
            coin_bits = self.bits(3)  # map 3 bits -> coin results
            toss = sum(2 + int(b) for b in coin_bits)  # each coin 2 or 3
            values.append(toss)
        return values

    def ifa_marks(self) -> str:
        return self.bits(8)


def default_entropy() -> CryptoEntropy:
    """Return the production entropy source."""
    return CryptoEntropy()


__all__ = [
    "CryptoEntropy",
    "DeterministicEntropy",
    "EntropySource",
    "default_entropy",
    "Sequence",
]
