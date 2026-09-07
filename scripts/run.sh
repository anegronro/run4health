#!/usr/bin/env bash
# Levanta la app. Por defecto solo en local; pasa una IP para exponerla al tailnet.
#   ./scripts/run.sh                 -> http://127.0.0.1:8770
#   ./scripts/run.sh 100.64.0.1   -> accesible desde el teléfono por Tailscale
set -euo pipefail
cd "$(dirname "$0")/.."
HOST="${1:-127.0.0.1}"
PORT="${PORT:-8770}"
exec uv run uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
