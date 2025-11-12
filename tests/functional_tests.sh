#!/bin/bash
# Functional Tests for Agent 9 (from agent9_checklist.yaml)

set -e

echo "=================================="
echo "Agent 9 Functional Tests"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0

# Function to test an endpoint
test_endpoint() {
    local name="$1"
    local url="$2"
    local data="$3"
    local expected_field="$4"

    echo -n "Testing: $name ... "

    response=$(curl -s -w "\n%{http_code}" -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$data")

    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)

    if [ "$http_code" -eq 200 ]; then
        if [ -n "$expected_field" ]; then
            if echo "$body" | jq -e "$expected_field" > /dev/null 2>&1; then
                echo -e "${GREEN}✓ PASSED${NC}"
                ((PASSED++))
                return 0
            else
                echo -e "${RED}✗ FAILED${NC} (missing field: $expected_field)"
                echo "  Response: $body"
                ((FAILED++))
                return 1
            fi
        else
            echo -e "${GREEN}✓ PASSED${NC}"
            ((PASSED++))
            return 0
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        echo "  Response: $body"
        ((FAILED++))
        return 1
    fi
}

echo "1. RAG Application Tests"
echo "------------------------"

# Wait for service to be ready
echo -n "Waiting for RAG service... "
for i in {1..30}; do
    if curl -s http://localhost:3000/health > /dev/null 2>&1; then
        echo "ready"
        break
    fi
    sleep 2
    if [ $i -eq 30 ]; then
        echo "timeout"
        exit 1
    fi
done

# RAG Query Test (from checklist)
test_endpoint \
    "RAG query endpoint" \
    "http://localhost:3000/api/rag/query" \
    '{"question":"test"}' \
    '.answer'

# Check for sources array
test_endpoint \
    "RAG sources validation" \
    "http://localhost:3000/api/rag/query" \
    '{"question":"What is Apache Spark?"}' \
    '.sources | type == "array"'

echo ""
echo "2. Multi-Agent Chatbot Tests"
echo "----------------------------"

# Wait for service to be ready
echo -n "Waiting for Chatbot service... "
for i in {1..30}; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "ready"
        break
    fi
    sleep 2
    if [ $i -eq 30 ]; then
        echo "timeout"
        exit 1
    fi
done

# Chatbot Test (from checklist)
test_endpoint \
    "Chatbot endpoint" \
    "http://localhost:8080/chat" \
    '{"message":"hello"}' \
    '.response'

# Check conversation_id
test_endpoint \
    "Chatbot conversation tracking" \
    "http://localhost:8080/chat" \
    '{"message":"test"}' \
    '.conversation_id'

echo ""
echo "3. Additional Service Tests"
echo "--------------------------"

# ComfyUI (if available)
if curl -s http://localhost:8188/system_stats > /dev/null 2>&1; then
    echo -n "Testing: ComfyUI health ... "
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -n "Testing: ComfyUI health ... "
    echo -e "${RED}✗ FAILED${NC} (service not available)"
    ((FAILED++))
fi

# txt2kg (if available)
if curl -s http://localhost:3001/health > /dev/null 2>&1; then
    echo -n "Testing: txt2kg health ... "
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -n "Testing: txt2kg health ... "
    echo -e "${RED}✗ FAILED${NC} (service not available)"
    ((FAILED++))
fi

# VSS (if available)
if curl -s http://localhost:8081/health > /dev/null 2>&1; then
    echo -n "Testing: VSS health ... "
    echo -e "${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -n "Testing: VSS health ... "
    echo -e "${RED}✗ FAILED${NC} (service not available)"
    ((FAILED++))
fi

echo ""
echo "=================================="
echo "Test Results"
echo "=================================="
echo "Passed: $PASSED"
echo "Failed: $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC}"
    exit 1
fi
