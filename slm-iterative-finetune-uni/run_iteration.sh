#!/bin/bash
# ============================================================================
# Run-Script für eine komplette Iteration
# ============================================================================
#
# Verwendung:
#   ./run_iteration.sh <iteration_number>
#
# Beispiel:
#   ./run_iteration.sh 1
#
# Das Script führt aus:
# 1. Training
# 2. Evaluation
# 3. Report-Generierung
# 4. Visualisierung (optional)
#
# ============================================================================

set -e  # Stop bei Fehler

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ============================================================================
# Parameter prüfen
# ============================================================================

if [ $# -eq 0 ]; then
    echo -e "${RED}❌ Fehler: Iterations-Nummer fehlt${NC}"
    echo "Verwendung: $0 <iteration_number>"
    echo "Beispiel: $0 1"
    exit 1
fi

ITERATION=$1
CONFIG_FILE="${CONFIG_FILE:-config.yaml}"
TRAIN_DATA="data/train_batches/iteration_${ITERATION}_train.json"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  Iteration ${ITERATION} - Vollständiger Durchlauf${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# ============================================================================
# Schritt 1: Training
# ============================================================================

echo -e "${YELLOW}[1/4] Training wird gestartet...${NC}"
echo ""

if [ $ITERATION -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Iteration 0 ist Baseline - kein Training nötig${NC}"
else
    # Checkpoint der vorherigen Iteration finden
    if [ $ITERATION -eq 1 ]; then
        # Erste Iteration: Verwende Base Model
        CHECKPOINT_ARG=""
    else
        PREV_ITERATION=$((ITERATION - 1))
        PREV_CHECKPOINT="checkpoints/iteration_${PREV_ITERATION}_model"

        if [ -d "$PREV_CHECKPOINT" ]; then
            CHECKPOINT_ARG="--previous-checkpoint $PREV_CHECKPOINT"
        else
            echo -e "${YELLOW}⚠️  Vorheriger Checkpoint nicht gefunden: $PREV_CHECKPOINT${NC}"
            CHECKPOINT_ARG=""
        fi
    fi

    # Training durchführen
    python src/train.py \
        --config "$CONFIG_FILE" \
        --iteration $ITERATION \
        --train-data "$TRAIN_DATA" \
        $CHECKPOINT_ARG

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Training erfolgreich abgeschlossen${NC}"
    else
        echo -e "${RED}❌ Training fehlgeschlagen${NC}"
        exit 1
    fi
fi

echo ""

# ============================================================================
# Schritt 2: Evaluation
# ============================================================================

echo -e "${YELLOW}[2/4] Evaluation wird gestartet...${NC}"
echo ""

if [ $ITERATION -eq 0 ]; then
    # Baseline: Verwende Base Model
    MODEL_ARG="--model $(grep 'base_model:' $CONFIG_FILE | awk '{print $2}' | tr -d '\"')"
else
    MODEL_ARG=""
fi

python src/eval.py \
    --config "$CONFIG_FILE" \
    --iteration $ITERATION \
    $MODEL_ARG

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Evaluation erfolgreich abgeschlossen${NC}"
else
    echo -e "${RED}❌ Evaluation fehlgeschlagen${NC}"
    exit 1
fi

echo ""

# ============================================================================
# Schritt 3: Report-Generierung
# ============================================================================

echo -e "${YELLOW}[3/4] Report wird generiert...${NC}"
echo ""

if [ $ITERATION -eq 0 ]; then
    COMPARE_ARG=""
else
    PREV_ITERATION=$((ITERATION - 1))
    COMPARE_ARG="--compare-with $PREV_ITERATION"
fi

python src/explain.py \
    --config "$CONFIG_FILE" \
    --iteration $ITERATION \
    $COMPARE_ARG

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Report erfolgreich generiert${NC}"
else
    echo -e "${RED}❌ Report-Generierung fehlgeschlagen${NC}"
    exit 1
fi

echo ""

# ============================================================================
# Schritt 4: Visualisierung (optional)
# ============================================================================

if [ "$SKIP_VISUALIZATION" != "1" ]; then
    echo -e "${YELLOW}[4/4] Visualisierung wird erstellt...${NC}"
    echo ""

    # Alle bisherigen Iterationen visualisieren
    ITERATIONS_LIST=$(seq -s',' 0 $ITERATION)

    python src/visualize.py \
        --config "$CONFIG_FILE" \
        --iterations "$ITERATIONS_LIST"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Visualisierung erfolgreich erstellt${NC}"
    else
        echo -e "${YELLOW}⚠️  Visualisierung fehlgeschlagen (nicht kritisch)${NC}"
    fi
else
    echo -e "${YELLOW}[4/4] Visualisierung übersprungen (SKIP_VISUALIZATION=1)${NC}"
fi

echo ""

# ============================================================================
# Zusammenfassung
# ============================================================================

echo -e "${BLUE}======================================${NC}"
echo -e "${GREEN}✅ Iteration ${ITERATION} abgeschlossen!${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""
echo "📊 Ergebnisse:"
echo "   - Checkpoint: checkpoints/iteration_${ITERATION}_model"
echo "   - Evaluation: data/eval_logs/iteration_${ITERATION}_eval.json"
echo "   - Report: reports/iteration_${ITERATION}_report.md"
echo ""
echo "📖 Nächste Schritte:"
echo "   1. Report ansehen: cat reports/iteration_${ITERATION}_report.md"
echo "   2. Dashboard öffnen: open reports/interactive_dashboard.html"

NEXT_ITERATION=$((ITERATION + 1))
echo "   3. Nächste Iteration: ./run_iteration.sh $NEXT_ITERATION"
echo ""
