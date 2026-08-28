# Neo4j 5.x with APOC + neosemantics (n10s) pre-installed.
#
# n10s version pinning: neosemantics publishes one release per Neo4j
# minor. Leave N10S_VERSION empty to auto-resolve the latest release at
# build time, or pin it to match the base image, e.g. --build-arg
# N10S_VERSION=5.20.0 for neo4j:5.20.
FROM neo4j:5.26

# Pinned to the release line matching the base image (Neo4j 5.26).
# Asset names are neosemantics-<version>.jar (NOT n10s-...jar).
ARG N10S_VERSION="5.26.0"
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && if [ -n "$N10S_VERSION" ]; then \
        URL="https://github.com/neo4j-labs/neosemantics/releases/download/${N10S_VERSION}/neosemantics-${N10S_VERSION}.jar"; \
    else \
        URL="https://github.com/neo4j-labs/neosemantics/releases/download/${N10S_VERSION}/neosemantics-${N10S_VERSION}.jar"; \
    fi \
 && echo "installing n10s from $URL" \
 && curl -fsSL "$URL" -o /tmp/n10s.jar \
 && ls -la /tmp/n10s.jar \
 && mkdir -p /var/lib/neo4j/plugins \
 && install -m 0644 /tmp/n10s.jar /var/lib/neo4j/plugins/n10s.jar \
 && rm -f /tmp/n10s.jar \
 && ls -la /var/lib/neo4j/plugins/
