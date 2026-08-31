#!/usr/bin/env bash
# Mantic Oracle — local Neo4j graph backup (offline dump).
#
# The public deployment is immutable (TTL files in git), so the only mutable
# copy of the knowledge graph is this local Neo4j. Back it up nightly:
#
#   bash scripts/backup_graph.sh            (one-off)
#   cron:  17 3 * * *  bash ~/workspace/mantic-oracle/scripts/backup_graph.sh
#
# Keeps the 14 most recent dumps in ./backups.
set -euo pipefail
cd "$(dirname "$0")/.."

STAMP=$(date +%Y%m%d-%H%M%S)
mkdir -p backups

VOL=$(docker volume ls -q | grep -m1 'neo4j_data' || true)
if [ -z "$VOL" ]; then
  echo "no neo4j_data volume found — is the stack up? (docker compose up -d)" >&2
  exit 1
fi

echo "stopping neo4j for a consistent dump..."
docker compose stop neo4j >/dev/null

echo "dumping graph $VOL -> backups/graph-$STAMP.dump"
docker run --rm \
  -v "$VOL:/data" \
  -v "$PWD/backups:/backups" \
  neo4j:5.26 \
  neo4j-admin database dump neo4j --to="/backups/graph-$STAMP.dump" >/dev/null

docker compose start neo4j >/dev/null
echo "neo4j restarted."

# keep last 14
ls -1t backups/graph-*.dump 2>/dev/null | tail -n +15 | xargs -r rm -f
echo "done -> backups/graph-$STAMP.dump"
