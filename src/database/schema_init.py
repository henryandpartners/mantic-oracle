"""Automated Neo4j schema & neosemantics (n10s) configuration.

Idempotent initializer equivalent to running by hand in the Cypher browser:

    CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS
    FOR (r:Resource) REQUIRE r.uri IS UNIQUE;

    CALL n10s.graphconfig.init({
      handleVocabUris: "SHORTEN",
      handleMultival: "ARRAY",
      keepLangTag: false,
      handleRDFTypes: "LABELS_AND_NODES"
    });

    CALL n10s.rdf.import.fetch(
      "file:///var/lib/neo4j/import/mantic_core.ttl", "Turtle");

Usage:
    python -m src.database.schema_init \\
        --uri bolt://localhost:7687 --user neo4j --password manticpass

The ``docker-compose.yml`` mounts ``./ontology`` at the container's import
directory, so the file:// URIs resolve out of the box.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from neo4j import GraphDatabase

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ONTOLOGY_DIR = REPO_ROOT / "ontology"

GRAPH_CONFIG = {
    "handleVocabUris": "SHORTEN",
    "handleMultival": "ARRAY",
    "keepLangTag": False,
    "handleRDFTypes": "LABELS_AND_NODES",
}

TTL_FILES = ("mantic_core.ttl", "shapes.shacl.ttl", "seed_data.ttl")


def log(message: str) -> None:
    print(f"[schema_init] {message}", flush=True)


def init_schema(
    uri: str,
    user: str,
    password: str,
    ontology_dir: Optional[Path] = None,
    import_root: str = "/var/lib/neo4j/import",
) -> bool:
    """Configure constraints, n10s graph config and import the ontology.

    Returns True when the graph is fully initialized.
    """
    ontology_dir = Path(ontology_dir or DEFAULT_ONTOLOGY_DIR)
    driver = GraphDatabase.driver(uri, auth=(user, password))
    try:
        with driver.session() as session:

            # 0. n10s presence ------------------------------------------------
            row = session.run(
                "SHOW PROCEDURES YIELD name WHERE name STARTS WITH 'n10s' "
                "RETURN count(*) AS n"
            ).single()
            if not row or row["n"] == 0:
                log("ERROR: neosemantics (n10s) is not installed on this server.")
                log("       Use the provided docker image (mantic/neo4j-n10s) or")
                log("       drop n10s.jar into the plugins/ directory and restart.")
                return False
            log(f"n10s detected ({row['n']} procedures).")

            # 1. unique URI constraint ---------------------------------------
            session.run(
                "CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS "
                "FOR (r:Resource) REQUIRE r.uri IS UNIQUE"
            )
            log("constraint n10s_unique_uri ensured.")

            # 2. graph configuration -----------------------------------------
            try:
                session.run("CALL n10s.graphconfig.init($config)", config=GRAPH_CONFIG)
                log("n10s graphconfig initialized (SHORTEN / ARRAY).")
            except Exception as exc:  # already configured is fine
                if "already" in str(exc).lower():
                    log("graphconfig already initialized - keeping existing config.")
                else:
                    raise

            # 3. ontology + seed import --------------------------------------
            for name in TTL_FILES:
                local = ontology_dir / name
                if not local.exists():
                    log(f"skip {name} (not found under {ontology_dir})")
                    continue
                remote = f"{import_root.rstrip('/')}/{name}"
                result = session.run(
                    "CALL n10s.rdf.import.fetch($url, 'Turtle') "
                    "YIELD terminationStatus, triplesLoaded, triplesParsed",
                    url=remote,
                ).single()
                if result is None:
                    log(f"{name}: no summary returned (unexpected).")
                else:
                    log(
                        f"{name}: {result['triplesLoaded']} triples loaded "
                        f"(status {result['terminationStatus']})."
                    )

            # 4. summary -------------------------------------------------------
            for suffix in ("GeomanticSign", "IChingHexagram", "IfaOdu"):
                row = session.run(
                    "MATCH (f) WHERE any(l IN labels(f) WHERE l ENDS WITH $suffix) "
                    "RETURN count(f) AS n",
                    suffix=suffix,
                ).single()
                log(f"{suffix} nodes: {row['n'] if row else 0}")
        return True
    finally:
        driver.close()


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--uri", default="bolt://localhost:7687")
    parser.add_argument("--user", default="neo4j")
    parser.add_argument("--password", default="manticpass")
    parser.add_argument("--ontology-dir", default=str(DEFAULT_ONTOLOGY_DIR))
    parser.add_argument(
        "--import-root",
        default="/var/lib/neo4j/import",
        help="in-container directory the ontology files are mounted at",
    )
    args = parser.parse_args(argv)
    ok = init_schema(
        uri=args.uri,
        user=args.user,
        password=args.password,
        ontology_dir=Path(args.ontology_dir),
        import_root=args.import_root,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
