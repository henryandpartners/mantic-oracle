"""Neo4j knowledge-graph bridge (n10s-aware, naming-tolerant Cypher).

neosemantics (n10s) with ``handleVocabUris: "SHORTEN"`` renames predicates
to ``<prefix>__<local>`` and class labels to ``<prefix>_<Local>`` (the
exact prefix depends on how namespaces got registered).  Rather than
hard-coding one spelling, every query below resolves properties, labels
and relationship types by SUFFIX so the bridge survives prefix churn:

    MATCH (f) WHERE any(k IN keys(f) WHERE k ENDS WITH 'hasBinaryVector'
                        AND f[k] = $vector)
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase


def _short_key(key: str) -> str:
    """Strip an n10s prefix ('ns0__', 'mantic__', 'mantic_') from a key."""
    return re.sub(r"^[A-Za-z0-9]+__", "", re.sub(r"^[A-Za-z0-9]+_", "", key))


class Neo4jManticBridge:
    """Parameterized-Cypher access layer for the mantic knowledge graph."""

    FIGURE_BY_VECTOR = """
    MATCH (f)
    WHERE any(k IN keys(f) WHERE k ENDS WITH 'hasBinaryVector' AND f[k] = $vector)
    OPTIONAL MATCH (f)-[r]-(c)
    WHERE type(r) ENDS WITH 'sharesArchetypeWith'
    RETURN properties(f) AS props, labels(f) AS labels,
           collect(DISTINCT properties(c)) AS counterparts,
           collect(DISTINCT labels(c)) AS counterpart_labels
    LIMIT 1
    """

    ALL_FIGURES = """
    MATCH (f)
    WHERE any(l IN labels(f) WHERE l ENDS WITH $suffix)
    RETURN properties(f) AS props, labels(f) AS labels
    ORDER BY f.figureIndex
    """

    def __init__(self, uri: str, auth: tuple[str, str] | None = None) -> None:
        self.uri = uri
        self.auth = auth
        self._driver = None

    # ------------------------------------------------------------------
    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(self.uri, auth=self.auth)
        return self._driver

    def healthy(self) -> bool:
        """True when the server answers and n10s procedures are present."""
        try:
            with self.driver.session() as session:
                record = session.run(
                    "SHOW PROCEDURES YIELD name WHERE name STARTS WITH 'n10s' "
                    "RETURN count(*) AS n"
                ).single()
                return bool(record and record["n"] > 0)
        except Exception:
            return False

    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_record(
        props: Dict[str, Any],
        labels: List[str],
        counterparts: List[Dict[str, Any]],
        counterpart_labels: List[List[str]],
    ) -> Dict[str, Any]:
        short = {_short_key(k): v for k, v in props.items()}
        kind = next(
            (
                label
                for label in labels
                if label.endswith(("GeomanticSign", "IChingHexagram", "IfaOdu"))
            ),
            labels[0] if labels else "Unknown",
        )
        archetypes: List[Dict[str, Any]] = []
        for cprops, clabels in zip(counterparts, counterpart_labels):
            cshort = {_short_key(k): v for k, v in cprops.items()}
            archetypes.append(
                {
                    "iri": cshort.get("uri"),
                    "label": cshort.get("label"),
                    "bits": cshort.get("hasBinaryVector"),
                    "kinds": [l for l in clabels if not l.startswith("Resource")],
                }
            )
        return {
            "iri": short.get("uri"),
            "kind": kind,
            "label": short.get("label"),
            "bits": short.get("hasBinaryVector"),
            "index": short.get("figureIndex"),
            "element": short.get("element"),
            "parable": short.get("parable"),
            "archetypes": archetypes,
        }

    def figure_by_vector(self, binary_vector: str) -> Optional[Dict[str, Any]]:
        """Retrieve a figure (label, element, parable, archetypes) by vector."""
        with self.driver.session() as session:
            result = session.run(self.FIGURE_BY_VECTOR, vector=binary_vector)
            record = result.single()
            if record is None:
                return None
            return self._normalize_record(
                record["props"], record["labels"] or [],
                record["counterparts"] or [], record["counterpart_labels"] or [],
            )

    def figures_of_kind(self, kind_suffix: str) -> List[Dict[str, Any]]:
        """List all figures whose label ends with `kind_suffix`."""
        with self.driver.session() as session:
            result = session.run(self.ALL_FIGURES, suffix=kind_suffix)
            return [
                self._normalize_record(r["props"], r["labels"] or [], [], [])
                for r in result
            ]

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def __enter__(self) -> "Neo4jManticBridge":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


__all__ = ["Neo4jManticBridge"]
