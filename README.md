# Multi-System Mantic Oracle Engine (DVSystoE)

A neuro-symbolic, algebraic, knowledge-graph-powered **oracle for autonomous AI
agents** facing optimization deadlocks, equal-probability Pareto choices and
out-of-distribution uncertainty.

The engine unifies the world's primary **Natural Computation Systems (NCS)**
into a single computable matrix:

| System | Width | Size | Role |
|---|---|---|---|
| Yoruba Ifa | 8-bit | 256 odus | Master index matrix & parable knowledge store |
| I Ching / Zhouyi | 6-bit | 64 hexagrams | Dynamic state machine (changing lines → resultant vectors) |
| Arabic Geomancy / Sikidy | 4-bit | 16 figures | Parity-checked algebraic engine (mod--2 tableau) |

```
entropy (secrets) ──► algebra (XOR / line-flips) ──► knowledge graph
                                                          │
        JSON-LD consultation payload ◄── strategic reframing
        (MCP tool / REST)                                   ▲
                                                             │
   Neo4j 5 + n10s (RDF) ◄── SHACL-validated TTL seed ◄──────┘
```

## Repository layout

```
mantic-oracle/
├── ontology/
│   ├── mantic_core.ttl        # unified OWL-DL ontology & archetypal mappings
│   ├── shapes.shacl.ttl       # SHACL validation shapes for binary vectors
│   └── seed_data.ttl          # 256 odus, 64 hexagrams (+384 transitions), 16 figures
├── src/
│   ├── core/
│   │   ├── entropy.py         # cryptographic & deterministic entropy
│   │   ├── algebra.py         # Sikidy XOR tableau, I Ching transitions
│   │   ├── mapper.py          # cross-system resonance matching
│   │   ├── tables.py          # canonical data tables (single source of truth)
│   │   └── oracle.py          # consultation orchestration + KB fallback
│   ├── database/
│   │   ├── neo4j_bridge.py    # naming-tolerant parameterized Cypher
│   │   └── schema_init.py     # n10s config, constraints, TTL ingestion
│   └── api/
│       ├── serializers.py     # W3C JSON-LD payloads
│       └── mcp_server.py      # FastMCP server + optional REST adapter
├── scripts/generate_seed.py   # regenerates seed_data.ttl from tables
├── tests/                     # algebra, SHACL, end-to-end flow
├── docker-compose.yml         # Neo4j 5.x + APOC + n10s
└── requirements.txt
```

## Quickstart

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# generate the seed knowledge graph (deterministic, committed)
python scripts/generate_seed.py

# run the full test suite (no Neo4j required - rdflib fallback)
pytest -q
```

## Deploy Neo4j + ingest the ontology

```bash
docker compose up -d --wait          # Neo4j 5.26 + APOC + n10s, ttl mounted
# browser: http://localhost:7474 (neo4j / manticpass)

python -m src.database.schema_init \
    --uri bolt://localhost:7687 --user neo4j --password manticpass
```

`schema_init` performs, idempotently:

```cypher
CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS
FOR (r:Resource) REQUIRE r.uri IS UNIQUE;

CALL n10s.graphconfig.init({
  handleVocabUris: "SHORTEN",
  handleMultival: "ARRAY",
  keepLangTag: false,
  handleRDFTypes: "LABELS_AND_NODES"
});

CALL n10s.rdf.import.fetch("file:///var/lib/neo4j/import/mantic_core.ttl", "Turtle");
CALL n10s.rdf.import.fetch("file:///var/lib/neo4j/import/seed_data.ttl",  "Turtle");
```

The query bridge (`neo4j_bridge.py`) resolves properties / labels /
relationship types **by suffix** (`ENDS WITH 'hasBinaryVector'` etc.), so it
works regardless of which `nsN__` prefixes n10s SHORTEN assigns.

## Consult the oracle (MCP)

Add to any MCP-capable agent config:

```json
{
  "mcpServers": {
    "mantic-oracle": {
      "command": "python",
      "args": ["-m", "src.api.mcp_server"],
      "cwd": "/absolute/path/to/mantic-oracle"
    }
  }
}
```

Tools exposed:

- **`consult_mantic_oracle`**(agent_id, decision_context, target_traditions)
  → JSON-LD consultation payload: cast figures, parables, cross-system
  archetypes, strategic reframing.
- **`lookup_figure`**(binary_vector) → cross-system resonance report for any
  4/6/8-bit vector.

Networked deployments: `python -m src.api.mcp_server --http --port 8000`
(streamable-HTTP MCP) or `--rest` for a plain FastAPI adapter
(`POST /consult`, `GET /health`).

### Example payload (abridged)

```json
{
  "@context": {"mantic": "https://w3id.org/mantic/core#", "...": "..."},
  "@type": "mantic:Consultation",
  "agentId": "planner-1",
  "decisionText": "Two equivalent routing strategies...",
  "figure": [
    {"@type": "mantic:GeomanticSign", "place": "Judge",
     "label": "Carcer", "binaryVector": "0110",
     "parable": "The cage of law: what encloses also defines...",
     "sharesArchetypeWith": [{"label": "Ogunda Meji"}, {"label": "Jie (Limitation)"}]}
  ],
  "strategicCounsel": "SHIELD: ... TRANSITION: ... CORPUS: ... REFRAMING: ..."
}
```

## Conventions

- **I Ching**: bits bottom→top, 1 = yang. Line values: 6 old yin (→yang),
  7 young yang, 8 young yin, 9 old yang (→yin).
- **Geomancy**: bits head→feet, 1 = single/active row. Judge parity theorem
  enforced: the Judge always has an even number of active rows (only 8 of 16
  figures can ever judge).
- **Ifa**: 8 bits = left leg + right leg, each 4-bit principal read
  top→bottom (Ogbe `1111`, Oyeku `0000`, Iwori `1001`, Odi `0110`, …).
  Compound seniority: `index = left_rank*16 + right_rank + 1`.
- Parables are original concise paraphrases of public-domain tradents
  (Legge-class renderings for the Zhouyi; standard diaspora summaries for
  Ifa and geomancy). Replace freely via `src/core/tables.py`.

## Extending

- **Full corpus ingestion (Step 2 of the roadmap)**: swap the generated
  compound-odu parables for LLM-extracted triples from public-domain
  archives (Sacred Texts, Twilit Grotto, digital occult libraries), then
  regenerate / merge into `seed_data.ttl` and re-run SHACL.
- **New traditions** (Tarot arcanum indexing, Runes, Vedic nakshatras):
  add a table in `tables.py`, a subclass + SHACL width shape, regenerate.

## Verification

```bash
pytest -q              # algebra + SHACL + end-to-end (rdflib fallback)
pytest tests/test_algebra.py -q   # 100% of the modulo-2 arithmetic
```

The even-Judge theorem, all 384 transition edges, vector uniqueness (16/64/256)
and JSON-LD parseability are all enforced by tests.

## License

MIT for code. Ontology and parable texts: original paraphrases of
public-domain material — treat as CC0.
