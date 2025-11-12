#!/bin/bash
# Agent 5 Inference Engine - Deployment Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
    cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║       Agent 5 Inference Engine - Deployment Script        ║
║                  Ollama + NIM + WebUI                      ║
╚════════════════════════════════════════════════════════════╝
EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check for Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    log_success "Docker is installed"

    # Check for Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    log_success "Docker Compose is installed"

    # Check for NVIDIA GPU (optional but recommended)
    if command -v nvidia-smi &> /dev/null; then
        log_success "NVIDIA GPU detected"
        nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
    else
        log_warning "NVIDIA GPU not detected. GPU acceleration will not be available."
    fi

    # Check for Ansible (if using Ansible deployment)
    if command -v ansible &> /dev/null; then
        log_success "Ansible is installed"
    else
        log_warning "Ansible is not installed. Ansible playbooks will not be available."
    fi
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."

    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_info "Creating .env file from example..."
        cp "$PROJECT_ROOT/configs/agent5.env.example" "$PROJECT_ROOT/.env"
        log_warning "Please edit .env file with your NGC_API_KEY and other settings"
        read -p "Press Enter to continue after editing .env file..."
    fi

    # Source environment variables
    source "$PROJECT_ROOT/.env"
    log_success "Environment configured"
}

# Deploy using Docker Compose
deploy_docker_compose() {
    log_info "Deploying with Docker Compose..."

    cd "$PROJECT_ROOT"

    # Pull images
    log_info "Pulling Docker images..."
    docker-compose pull

    # Start services
    log_info "Starting services..."
    docker-compose up -d

    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10

    # Check service health
    check_services

    log_success "Docker Compose deployment complete"
}

# Deploy using Ansible
deploy_ansible() {
    log_info "Deploying with Ansible..."

    cd "$PROJECT_ROOT/playbooks"

    # Check inventory
    if [ ! -f "$PROJECT_ROOT/configs/inventory.ini" ]; then
        log_error "Inventory file not found. Please create configs/inventory.ini"
        exit 1
    fi

    # Run deployment playbook
    ansible-playbook -i "$PROJECT_ROOT/configs/inventory.ini" deploy-all.yml

    log_success "Ansible deployment complete"
}

# Check service health
check_services() {
    log_info "Checking service health..."

    # Check Ollama
    if curl -sf http://localhost:11434/api/tags > /dev/null; then
        log_success "Ollama is running"
    else
        log_warning "Ollama is not responding"
    fi

    # Check Open WebUI
    if curl -sf http://localhost:8080 > /dev/null; then
        log_success "Open WebUI is running"
    else
        log_warning "Open WebUI is not responding"
    fi

    # Check NIM Gateway
    if curl -sf http://localhost:8000/health > /dev/null; then
        log_success "NIM Gateway is running"
    else
        log_warning "NIM Gateway is not responding"
    fi

    # Check Model API
    if curl -sf http://localhost:8888/health > /dev/null; then
        log_success "Model Management API is running"
    else
        log_warning "Model Management API is not responding"
    fi
}

# Show service URLs
show_urls() {
    cat << EOF

╔════════════════════════════════════════════════════════════╗
║                    Service URLs                            ║
╠════════════════════════════════════════════════════════════╣
║  Ollama API:      http://localhost:11434                   ║
║  Open WebUI:      http://localhost:8080                    ║
║  NIM Gateway:     http://localhost:8000                    ║
║  Model API:       http://localhost:8888                    ║
║  API Docs:        http://localhost:8888/docs               ║
╚════════════════════════════════════════════════════════════╝

Next steps:
  1. Access Open WebUI at http://localhost:8080
  2. Create an account (first user is admin)
  3. Use the Model Management API for programmatic access
  4. Check logs: docker-compose logs -f

EOF
}

# Main deployment function
main() {
    show_banner
    check_prerequisites
    setup_environment

    echo ""
    echo "Select deployment method:"
    echo "  1) Docker Compose (Recommended)"
    echo "  2) Ansible Playbooks"
    echo "  3) Exit"
    echo ""
    read -p "Enter choice [1-3]: " choice

    case $choice in
        1)
            deploy_docker_compose
            show_urls
            ;;
        2)
            deploy_ansible
            ;;
        3)
            log_info "Exiting..."
            exit 0
            ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac

    log_success "Deployment completed successfully!"
}

# Run main function
main "$@"
