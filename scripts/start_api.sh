#!/bin/bash
#
# Start Agent 8 Model API Server
#

set -e

PORT="${PORT:-8888}"
HOST="${HOST:-0.0.0.0}"
WORKERS="${WORKERS:-4}"

echo "Starting Agent 8 Model API..."
echo "Host: $HOST"
echo "Port: $PORT"
echo "Workers: $WORKERS"
echo ""

cd "$(dirname "$0")/.."

python3 -m uvicorn agent8.api.model_api:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WORKERS" \
    --log-level info
