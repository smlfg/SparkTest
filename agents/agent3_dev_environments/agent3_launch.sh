#!/bin/bash
# Agent 3: Development Environments
# Main launch script for IDEs and coding tools

set -e

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT3_DIR="$SCRIPT_DIR/agent3"
PLAYBOOKS_DIR="$AGENT3_DIR/playbooks"
CONTAINERS_DIR="$AGENT3_DIR/containers"
TEMPLATES_DIR="$AGENT3_DIR/templates"

# Default settings
VSCODE_PORT="${VSCODE_PORT:-8443}"
JAX_GPU="${JAX_GPU:-all}"
USE_ANSIBLE="${USE_ANSIBLE:-false}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
show_banner() {
    echo ""
    echo "========================================="
    echo "  Agent 3: Development Environments"
    echo "  IDEs + Coding Tools"
    echo "========================================="
    echo ""
}

# Function to start VS Code Server
start_vscode_server() {
    local port="${1:-$VSCODE_PORT}"

    log_info "Starting VS Code Server on port $port..."

    if [ "$USE_ANSIBLE" = "true" ] && command -v ansible-playbook &> /dev/null; then
        log_info "Using Ansible playbook..."
        ansible-playbook "$PLAYBOOKS_DIR/vscode.yml" \
            -e "vscode_port=$port" \
            --connection=local
    else
        log_info "Using shell script..."
        source "$PLAYBOOKS_DIR/vscode.sh"
        start_vscode_server "$port"
    fi

    log_success "VS Code Server started on port $port"
}

# Function to launch JAX container
launch_jax_container() {
    local gpus="${1:-$JAX_GPU}"

    log_info "Launching JAX Container with GPU config: $gpus..."

    if [ "$USE_ANSIBLE" = "true" ] && command -v ansible-playbook &> /dev/null; then
        log_info "Using Ansible playbook..."
        ansible-playbook "$PLAYBOOKS_DIR/jax.yml" --connection=local
    else
        log_info "Using shell script..."
        source "$PLAYBOOKS_DIR/jax.sh"
        launch_jax_container "$gpus"
    fi

    log_success "JAX Container launched"
}

# Function to stop JAX container
stop_jax_container() {
    log_info "Stopping JAX Container..."
    source "$PLAYBOOKS_DIR/jax.sh"
    stop_jax_container
    log_success "JAX Container stopped"
}

# Function to show status
show_status() {
    log_info "Checking environment status..."
    echo ""

    # Check VS Code Server
    if command -v code-server &> /dev/null; then
        if pgrep -f "code-server" > /dev/null; then
            log_success "VS Code Server: Running"
        else
            log_warning "VS Code Server: Installed but not running"
        fi
    else
        log_warning "VS Code Server: Not installed"
    fi

    # Check Docker
    if command -v docker &> /dev/null; then
        log_success "Docker: Installed"

        # Check JAX container
        if docker ps --format '{{.Names}}' | grep -q "jax-dev-environment"; then
            log_success "JAX Container: Running"
        elif docker ps -a --format '{{.Names}}' | grep -q "jax-dev-environment"; then
            log_warning "JAX Container: Exists but not running"
        else
            log_warning "JAX Container: Not created"
        fi
    else
        log_warning "Docker: Not installed"
    fi

    echo ""
}

# Function to list available templates
list_templates() {
    log_info "Available development environment templates:"
    echo ""

    for template in "$TEMPLATES_DIR"/*.env; do
        if [ -f "$template" ]; then
            basename "$template"
        fi
    done

    echo ""
    log_info "Usage: source agent3/templates/<template-name>.env"
}

# Function to show URLs and access info
show_access_info() {
    echo ""
    echo "========================================="
    echo "  Access Information"
    echo "========================================="
    echo ""
    echo "VS Code Server:"
    echo "  URL: http://localhost:$VSCODE_PORT"
    echo "  Default Password: changeme123"
    echo "  (Set VSCODE_PASSWORD to change)"
    echo ""
    echo "JAX Container:"
    echo "  Jupyter: http://localhost:8888"
    echo "  Token: jaxdev123"
    echo "  TensorBoard: http://localhost:6006"
    echo ""
    echo "Useful Commands:"
    echo "  $0 status              - Show status"
    echo "  $0 stop-jax            - Stop JAX container"
    echo "  $0 templates           - List templates"
    echo "  docker logs jax-dev-environment"
    echo "========================================="
    echo ""
}

# Function to setup complete environment
setup_complete_environment() {
    log_info "Setting up complete development environment..."

    start_vscode_server "$VSCODE_PORT"
    sleep 2
    launch_jax_container "$JAX_GPU"

    log_success "Complete environment setup finished!"
    show_access_info
}

# Function to show help
show_help() {
    cat << EOF
Usage: $0 [COMMAND] [OPTIONS]

Commands:
    all, setup              Setup complete environment (VS Code + JAX)
    vscode, code            Start VS Code Server only
    jax                     Launch JAX container only
    stop-jax                Stop JAX container
    status                  Show environment status
    templates               List available templates
    help                    Show this help message

Options:
    --port PORT             VS Code Server port (default: 8443)
    --gpus GPU_CONFIG       GPU configuration for JAX (default: all)
                           Options: all, none, 0,1,2
    --ansible               Use Ansible playbooks instead of shell scripts

Environment Variables:
    VSCODE_PORT            VS Code Server port (default: 8443)
    VSCODE_PASSWORD        VS Code Server password (default: changeme123)
    JAX_GPU                JAX GPU configuration (default: all)
    USE_ANSIBLE            Use Ansible playbooks (default: false)

Examples:
    # Start complete environment
    $0 all

    # Start VS Code Server on custom port
    $0 vscode --port 9000

    # Launch JAX container with specific GPUs
    $0 jax --gpus 0,1

    # Use Ansible playbooks
    $0 all --ansible

    # Check status
    $0 status

Dependencies:
    - Docker (required for JAX container)
    - code-server (installed automatically for VS Code)
    - Ansible (optional, for playbook-based setup)

Interface Output:
    # agent3_launch.sh
    start_vscode_server --port 8443
    launch_jax_container --gpus all

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --port)
                VSCODE_PORT="$2"
                shift 2
                ;;
            --gpus)
                JAX_GPU="$2"
                shift 2
                ;;
            --ansible)
                USE_ANSIBLE="true"
                shift
                ;;
            *)
                break
                ;;
        esac
    done
}

# Main execution
main() {
    show_banner

    # Check if Agent3 directory exists
    if [ ! -d "$AGENT3_DIR" ]; then
        log_error "Agent3 directory not found at: $AGENT3_DIR"
        exit 1
    fi

    # Parse arguments
    local command="${1:-help}"
    shift || true
    parse_args "$@"

    # Execute command
    case "$command" in
        all|setup)
            setup_complete_environment
            ;;
        vscode|code|vs)
            start_vscode_server "$VSCODE_PORT"
            ;;
        jax)
            launch_jax_container "$JAX_GPU"
            ;;
        stop-jax)
            stop_jax_container
            ;;
        status)
            show_status
            ;;
        templates|template|env)
            list_templates
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $command"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Export functions for testing and sourcing
export -f start_vscode_server
export -f launch_jax_container
export -f stop_jax_container
export -f show_status
export -f list_templates

# Run main if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
