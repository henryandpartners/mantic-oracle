# Neo4j 5.x with APOC + neosemantics (n10s) pre-installed.
#
# n10s version pinning: neosemantics publishes one release per Neo4j
# minor. Leave N10S_VERSION empty to auto-resolve the latest release at
# build time, or pin it to match the base image, e.g. --build-arg
# N10S_VERSION=5.20.0 for neo4j:5.20.
FROM neo4j:5.26

ARG N10S_VERSION=""
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && if [ -n "$N10S_VERSION" ]; then \
        URL="https://github.com/neo4j-labs/neosemantics/releases/download/${N10S_VERSION}/n10s-${N10S_VERSION}.jar"; \
    else \
        URL="$(curl -fsSL https://api.github.com/repos/neo4j-labs/neosemantics/releases/latest \
              | grep -oE 'https://[^"]+\.jar' | head -n 1)"; \
    fi \
 && echo "installing n10s from $URL" \
 && curl -fsSL "$URL" -o /plugins/n10s.jar \
 && ls -la /plugins/
