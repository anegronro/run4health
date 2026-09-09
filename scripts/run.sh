#!/usr/bin/env bash
# Runs the app. Local only by default; pass an address to expose it on your
# own private network.
#   ./scripts/run.sh                 -> http://127.0.0.1:8770
#   ./scripts/run.sh 100.64.0.1      -> reachable from your phone over Tailscale
set -euo pipefail
cd "$(dirname "$0")/.."
HOST="${1:-127.0.0.1}"
PORT="${PORT:-8770}"
exec uv run uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
