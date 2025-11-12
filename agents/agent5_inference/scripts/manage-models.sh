#!/bin/bash
# Agent 5 Inference Engine - Model Management Script

set -e

API_URL="${API_URL:-http://localhost:8888}"
OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# List all models
list_models() {
    log_info "Fetching available models..."

    echo ""
    echo "═══════════════════════════════════════"
    echo "       Available Models"
    echo "═══════════════════════════════════════"

    curl -s "$API_URL/api/models" | jq -r '
        .ollama as $ollama | .nim as $nim |

        "Ollama Models (" + ($ollama | length | tostring) + "):",
        ($ollama[] | "  • " + .name + " [" + .status + "]"),
        "",
        "NIM Models (" + ($nim | length | tostring) + "):",
        ($nim[] | "  • " + .name + " [" + .status + "]")
    '
    echo ""
}

# Pull a model
pull_model() {
    local model_name="$1"

    if [ -z "$model_name" ]; then
        log_error "Model name is required"
        echo "Usage: $0 pull <model-name>"
        echo "Example: $0 pull llama3.1:70b"
        exit 1
    fi

    log_info "Pulling model: $model_name"

    curl -s -X POST "$API_URL/api/models/pull?model_name=$model_name" | jq '.'

    if [ $? -eq 0 ]; then
        log_success "Model pulled successfully"
    else
        log_error "Failed to pull model"
    fi
}

# Get model info
model_info() {
    local model_name="$1"

    if [ -z "$model_name" ]; then
        log_error "Model name is required"
        echo "Usage: $0 info <model-name>"
        exit 1
    fi

    log_info "Getting info for model: $model_name"

    curl -s "$API_URL/api/models" | jq --arg name "$model_name" '
        (.ollama[] | select(.name == $name)),
        (.nim[] | select(.name == $name))
    '
}

# Test model
test_model() {
    local model_name="$1"
    local provider="${2:-ollama}"

    if [ -z "$model_name" ]; then
        log_error "Model name is required"
        echo "Usage: $0 test <model-name> [provider]"
        echo "Example: $0 test llama3.1:70b ollama"
        exit 1
    fi

    log_info "Testing model: $model_name (provider: $provider)"

    curl -s -X POST "$API_URL/api/completion" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$model_name\",
            \"prompt\": \"Say hello in one sentence.\",
            \"max_tokens\": 50,
            \"provider\": \"$provider\"
        }" | jq '.'
}

# Show registry
show_registry() {
    log_info "Fetching model registry..."

    echo ""
    echo "═══════════════════════════════════════"
    echo "       Model Registry"
    echo "═══════════════════════════════════════"

    curl -s "$API_URL/api/models/registry" | jq -r '
        "Ollama Models:",
        (.ollama_models[] | "  • " + .),
        "",
        "NIM Endpoints:",
        (.nim_endpoints[] | "  • " + .)
    '
    echo ""
}

# Show usage
show_usage() {
    cat << EOF
Agent 5 Model Management Tool

Usage: $0 <command> [arguments]

Commands:
    list                    List all available models
    pull <model-name>       Pull/download a model (Ollama)
    info <model-name>       Get information about a model
    test <model> [provider] Test a model with a simple prompt
    registry                Show the model registry
    help                    Show this help message

Examples:
    $0 list
    $0 pull llama3.1:70b
    $0 info mistral:7b
    $0 test llama3.1:70b ollama
    $0 registry

Environment Variables:
    API_URL                 Model API URL (default: http://localhost:8888)
    OLLAMA_URL             Ollama API URL (default: http://localhost:11434)

EOF
}

# Main
main() {
    local command="${1:-help}"

    case "$command" in
        list)
            list_models
            ;;
        pull)
            pull_model "$2"
            ;;
        info)
            model_info "$2"
            ;;
        test)
            test_model "$2" "$3"
            ;;
        registry)
            show_registry
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
