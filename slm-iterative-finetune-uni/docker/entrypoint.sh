#!/bin/bash
# ============================================================================
# Entrypoint Script für DGX Spark Container
# ============================================================================

set -e

echo "=========================================="
echo "SLM Iterative Fine-Tuning Container"
echo "=========================================="

# GPU-Informationen anzeigen
if command -v nvidia-smi &> /dev/null; then
    echo ""
    echo "GPU Status:"
    nvidia-smi --query-gpu=index,name,memory.total,memory.free --format=csv,noheader
    echo ""
fi

# Spark-Umgebung prüfen
if [ -n "$SPARK_MASTER_HOST" ]; then
    echo "Spark Master: $SPARK_MASTER_HOST"
fi

# Verzeichnisse erstellen falls nicht vorhanden
mkdir -p /workspace/logs
mkdir -p /workspace/checkpoints
mkdir -p /workspace/data/train_batches
mkdir -p /workspace/data/eval_logs
mkdir -p /workspace/reports

echo "=========================================="
echo "Ready! Workspace: /workspace"
echo "=========================================="
echo ""

# Befehl ausführen
exec "$@"
