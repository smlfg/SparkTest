#!/bin/bash
# LLaMA Factory Fine-tuning Launch Script
# Simplified interface for students

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FINETUNING_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATES_DIR="$FINETUNING_DIR/templates"
DATASETS_DIR="$FINETUNING_DIR/datasets"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_banner() {
    echo ""
    echo "========================================="
    echo "  LLaMA Factory Fine-tuning Launcher"
    echo "  Agent 3: Development Environments"
    echo "========================================="
    echo ""
}

# Validate dataset
validate_dataset() {
    local dataset_file="$1"
    local dataset_type="$2"

    log_info "Validating dataset: $dataset_file"

    if [ ! -f "$dataset_file" ]; then
        log_error "Dataset file not found: $dataset_file"
        return 1
    fi

    python "$SCRIPT_DIR/validate_dataset.py" "$dataset_file" --type "$dataset_type"
    return $?
}

# List available templates
list_templates() {
    log_info "Available templates:"
    echo ""

    for template in "$TEMPLATES_DIR"/*.yaml; do
        if [ -f "$template" ]; then
            filename=$(basename "$template")
            echo "  - $filename"
        fi
    done

    echo ""
}

# List example datasets
list_examples() {
    log_info "Example datasets:"
    echo ""

    for example in "$DATASETS_DIR/examples"/*.json; do
        if [ -f "$example" ]; then
            filename=$(basename "$example")
            echo "  - $filename"
        fi
    done

    echo ""
}

# Start fine-tuning with template
start_training() {
    local template="$1"
    local dataset="$2"

    log_info "Starting fine-tuning..."
    log_info "Template: $template"
    log_info "Dataset: $dataset"

    # Validate inputs
    if [ ! -f "$TEMPLATES_DIR/$template" ]; then
        log_error "Template not found: $template"
        log_info "Use --list-templates to see available templates"
        exit 1
    fi

    if [ ! -f "$DATASETS_DIR/$dataset" ]; then
        log_error "Dataset not found: $dataset"
        log_info "Place your dataset in: $DATASETS_DIR/"
        exit 1
    fi

    # Validate dataset
    log_info "Validating dataset..."
    if ! validate_dataset "$DATASETS_DIR/$dataset" "chat"; then
        log_error "Dataset validation failed!"
        exit 1
    fi

    log_info "Dataset validation passed!"
    echo ""

    # Launch via Docker
    log_info "Launching LLaMA Factory container..."

    docker exec agent3-llama-factory llamafactory-cli train \
        "/app/templates/$template" \
        --dataset_dir /app/data \
        --output_dir /app/output

    log_info "Training started!"
    log_info "Monitor at: http://localhost:7860"
    log_info "API Monitor: http://localhost:8001"
}

# Monitor training
monitor_training() {
    local job_id="$1"

    log_info "Opening training monitor..."
    echo ""
    echo "WebUI: http://localhost:7860"
    echo "API: http://localhost:8001/api/jobs/$job_id"
    echo "WebSocket: ws://localhost:8001/ws/training/$job_id"
    echo ""
    echo "Press Ctrl+C to stop monitoring (training continues in background)"

    # Stream logs
    docker logs -f agent3-llama-factory
}

# Quick start with examples
quick_start() {
    local example_type="$1"

    case "$example_type" in
        chat)
            log_info "Quick start: Chat fine-tuning"
            start_training "chat-finetune.yaml" "examples/student-chat.json"
            ;;
        classification)
            log_info "Quick start: Classification"
            start_training "classification.yaml" "examples/student-classification.json"
            ;;
        code)
            log_info "Quick start: Code assistant"
            start_training "code-assistant.yaml" "examples/student-code.json"
            ;;
        *)
            log_error "Unknown example type: $example_type"
            log_info "Available: chat, classification, code"
            exit 1
            ;;
    esac
}

# Show help
show_help() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
    quick-start TYPE        Quick start with example dataset
                           Types: chat, classification, code

    train                   Start fine-tuning
        --template FILE     Template YAML file (required)
        --dataset FILE      Dataset JSON file (required)

    validate               Validate dataset
        --dataset FILE      Dataset JSON file (required)
        --type TYPE         Dataset type (chat, classification, code)

    monitor [JOB_ID]       Monitor training job

    list-templates         List available templates
    list-examples          List example datasets
    help                   Show this help message

Examples:
    # Quick start with chat example
    $0 quick-start chat

    # Custom training
    $0 train --template chat-finetune.yaml --dataset my-dataset.json

    # Validate dataset
    $0 validate --dataset my-dataset.json --type chat

    # Monitor training
    $0 monitor

Environment Variables:
    LLAMA_FACTORY_CONTAINER   Container name (default: agent3-llama-factory)

EOF
}

# Main
main() {
    show_banner

    local command="${1:-help}"
    shift || true

    case "$command" in
        quick-start)
            quick_start "$1"
            ;;
        train)
            local template=""
            local dataset=""

            while [[ $# -gt 0 ]]; do
                case $1 in
                    --template)
                        template="$2"
                        shift 2
                        ;;
                    --dataset)
                        dataset="$2"
                        shift 2
                        ;;
                    *)
                        log_error "Unknown option: $1"
                        exit 1
                        ;;
                esac
            done

            if [ -z "$template" ] || [ -z "$dataset" ]; then
                log_error "Both --template and --dataset are required"
                show_help
                exit 1
            fi

            start_training "$template" "$dataset"
            ;;
        validate)
            local dataset=""
            local dtype="chat"

            while [[ $# -gt 0 ]]; do
                case $1 in
                    --dataset)
                        dataset="$2"
                        shift 2
                        ;;
                    --type)
                        dtype="$2"
                        shift 2
                        ;;
                    *)
                        log_error "Unknown option: $1"
                        exit 1
                        ;;
                esac
            done

            if [ -z "$dataset" ]; then
                log_error "--dataset is required"
                exit 1
            fi

            validate_dataset "$DATASETS_DIR/$dataset" "$dtype"
            ;;
        monitor)
            monitor_training "$1"
            ;;
        list-templates)
            list_templates
            ;;
        list-examples)
            list_examples
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            show_help
            exit 1
            ;;
    esac
}

# Run
main "$@"
