#!/bin/bash
# Deploy All Inference Engines
# Unified deployment script for Agent 4

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Agent 4: Inference Engine Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Check NVIDIA Docker runtime
if ! docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi >/dev/null 2>&1; then
    echo -e "${RED}Error: NVIDIA Docker runtime is not properly configured${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prerequisites met${NC}"

# Parse arguments
SERVICES="vllm trt-llm speculative"
ENABLE_MONITORING=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --monitoring)
            ENABLE_MONITORING=true
            shift
            ;;
        --service)
            SERVICES="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --monitoring        Enable Prometheus and Grafana monitoring"
            echo "  --service <name>    Deploy specific service (vllm, trt-llm, speculative, or 'all')"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Navigate to deployment directory
cd "$PROJECT_ROOT/deployment/docker"

# Build and deploy
echo -e "\n${YELLOW}Building Docker images...${NC}"
if [ "$ENABLE_MONITORING" = true ]; then
    docker-compose --profile monitoring build
else
    docker-compose build
fi

echo -e "\n${YELLOW}Starting services...${NC}"
if [ "$SERVICES" = "all" ]; then
    if [ "$ENABLE_MONITORING" = true ]; then
        docker-compose --profile monitoring up -d
    else
        docker-compose up -d
    fi
else
    docker-compose up -d $SERVICES
fi

# Wait for services to be ready
echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Health check
echo -e "\n${YELLOW}Performing health checks...${NC}"

check_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "http://localhost:$port/health" >/dev/null 2>&1 || \
           curl -s -f "http://localhost:$port/v1/models" >/dev/null 2>&1; then
            echo -e "${GREEN}✓ $service is healthy${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo -e "\n${RED}✗ $service failed to start${NC}"
    return 1
}

# Check each service
if [[ $SERVICES == *"vllm"* ]] || [ "$SERVICES" = "all" ]; then
    echo -n "Checking vLLM service... "
    check_service "vLLM" 8000
fi

if [[ $SERVICES == *"trt-llm"* ]] || [ "$SERVICES" = "all" ]; then
    echo -n "Checking TRT-LLM service... "
    check_service "TRT-LLM" 8001
fi

if [[ $SERVICES == *"speculative"* ]] || [ "$SERVICES" = "all" ]; then
    echo -n "Checking Speculative Decoding service... "
    check_service "Speculative" 8002
fi

# Display endpoints
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Successful!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Inference Endpoints:"
echo "  vLLM:              http://localhost:8000"
echo "  TRT-LLM:           http://localhost:8001"
echo "  Speculative:       http://localhost:8002"

if [ "$ENABLE_MONITORING" = true ]; then
    echo ""
    echo "Monitoring:"
    echo "  Prometheus:        http://localhost:9090"
    echo "  Grafana:           http://localhost:3000 (admin/admin)"
fi

echo ""
echo "Useful commands:"
echo "  View logs:         docker-compose logs -f [service]"
echo "  Stop services:     docker-compose down"
echo "  Restart service:   docker-compose restart [service]"
echo "  View status:       docker-compose ps"
echo ""
