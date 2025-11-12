#!/bin/bash
# Agent 5 Inference Engine - API Testing Script

set -e

API_URL="${API_URL:-http://localhost:8888}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Testing Agent 5 Model Management API${NC}"
echo "API URL: $API_URL"
echo ""

# Test 1: Health Check
echo -e "${GREEN}[1/6] Testing health endpoint...${NC}"
curl -s "$API_URL/health" | jq '.'
echo ""

# Test 2: Root endpoint
echo -e "${GREEN}[2/6] Testing root endpoint...${NC}"
curl -s "$API_URL/" | jq '.'
echo ""

# Test 3: List models
echo -e "${GREEN}[3/6] Listing available models...${NC}"
curl -s "$API_URL/api/models" | jq '.'
echo ""

# Test 4: Get model registry
echo -e "${GREEN}[4/6] Getting model registry...${NC}"
curl -s "$API_URL/api/models/registry" | jq '.'
echo ""

# Test 5: List providers
echo -e "${GREEN}[5/6] Listing providers...${NC}"
curl -s "$API_URL/api/providers" | jq '.'
echo ""

# Test 6: Test completion (if Ollama is running)
echo -e "${GREEN}[6/6] Testing completion endpoint...${NC}"
curl -s -X POST "$API_URL/api/completion" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:70b",
    "prompt": "Hello, how are you?",
    "max_tokens": 100,
    "provider": "ollama"
  }' | jq '.'

echo ""
echo -e "${GREEN}API testing complete!${NC}"
