#!/bin/bash
#
# Agent 5 Quick Validation Script
# Quick smoke test to verify basic functionality
#
# Usage: ./quick_validate.sh
#

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Agent 5: Quick Validation Check                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Ollama
echo -n "Testing Ollama API... "
if curl -sf http://localhost:11434/api/tags > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "  Error: Ollama not responding on port 11434"
fi

# Test 2: Open WebUI
echo -n "Testing Open WebUI... "
if curl -sf http://localhost:8080 > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "  Error: Open WebUI not responding on port 8080"
fi

# Test 3: Model API Health
echo -n "Testing Model API... "
if curl -sf http://localhost:8888/health > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "  Error: Model API not responding on port 8888"
fi

# Test 4: Model List
echo -n "Testing Model Registry... "
if curl -sf http://localhost:8888/api/models | grep -q "ollama"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "  Error: Model registry not returning data"
fi

# Test 5: Compare Endpoint
echo -n "Testing Compare Endpoint... "
if curl -sf http://localhost:8888/api/compare \
    -H "Content-Type: application/json" \
    -d '{"prompt":"test","models":["llama3.1:8b"]}' | grep -q "results"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} (May need models loaded)"
fi

# Docker Status
echo ""
echo "Docker Container Status:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "NAME|ollama|webui|agent5"

echo ""
echo "Quick validation complete!"
echo ""
echo "For full test suite, run:"
echo "  ./scripts/run_tests.sh"
