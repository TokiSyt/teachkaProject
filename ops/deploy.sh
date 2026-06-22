#!/usr/bin/env bash
# Rebuild + restart the production stack.
# entrypoint.sh inside the web image runs collectstatic + migrate on boot,
# so this is the only command needed after pulling new code.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "[deploy] rebuilding prod stack (docker-compose.prod.yml)..."
docker compose -f docker-compose.prod.yml up -d --build

# Drop dangling images left by the rebuild so disk doesn't creep.
docker image prune -f >/dev/null 2>&1 || true

echo "[deploy] done. Recent web logs:"
docker compose -f docker-compose.prod.yml logs --tail 20 web
