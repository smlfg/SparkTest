#!/bin/bash

################################################################################
# Agent 10 Deployment Script
# Deploys the complete SparkTest multi-agent system
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

################################################################################
# Helper Functions
################################################################################

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

print_banner() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║         SparkTest Agent 10 - Deployment System              ║"
    echo "║         Integration + Testing Infrastructure                ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_dependencies() {
    log_info "Checking dependencies..."

    local missing_deps=0

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        missing_deps=1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        missing_deps=1
    fi

    if [ $missing_deps -eq 1 ]; then
        log_error "Missing required dependencies"
        exit 1
    fi

    log_success "All dependencies are installed"
}

create_directories() {
    log_info "Creating required directories..."

    mkdir -p spark/jobs
    mkdir -p spark/data
    mkdir -p spark/logs
    mkdir -p database/init
    mkdir -p reports
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/provisioning/datasources
    mkdir -p monitoring/grafana/provisioning/dashboards

    log_success "Directories created"
}

setup_monitoring() {
    log_info "Setting up monitoring configuration..."

    # Create Prometheus configuration
    cat > monitoring/prometheus.yml <<EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'sparktest-api'
    static_configs:
      - targets: ['api-gateway:8000']

  - job_name: 'spark-master'
    static_configs:
      - targets: ['spark-master:8080']

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF

    # Create Grafana datasource configuration
    cat > monitoring/grafana/provisioning/datasources/prometheus.yml <<EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    # Create Grafana dashboard provisioning
    cat > monitoring/grafana/provisioning/dashboards/dashboard.yml <<EOF
apiVersion: 1

providers:
  - name: 'SparkTest Dashboards'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    log_success "Monitoring configuration created"
}

setup_database() {
    log_info "Setting up database initialization scripts..."

    cat > database/init/01_init.sql <<EOF
-- SparkTest Database Initialization

-- Create jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    job_name VARCHAR(255) NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    parameters JSONB,
    result JSONB,
    error_message TEXT
);

-- Create index on job_id
CREATE INDEX IF NOT EXISTS idx_jobs_job_id ON jobs(job_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);

-- Create metrics table
CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value NUMERIC NOT NULL,
    tags JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_metrics_name ON metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp);

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id VARCHAR(255),
    user_id VARCHAR(255),
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);

-- Insert initial data
INSERT INTO jobs (job_id, job_name, job_type, status, priority)
VALUES ('init_job', 'Initialization Job', 'system', 'completed', 10)
ON CONFLICT (job_id) DO NOTHING;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO sparktest;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO sparktest;
EOF

    log_success "Database initialization scripts created"
}

start_services() {
    log_info "Starting services with Docker Compose..."

    # Pull images
    log_info "Pulling Docker images..."
    docker-compose pull

    # Build custom images
    log_info "Building custom images..."
    docker-compose build

    # Start services
    log_info "Starting all services..."
    docker-compose up -d

    log_success "Services started"
}

wait_for_services() {
    log_info "Waiting for services to be ready..."

    local max_attempts=30
    local attempt=0

    # Wait for API Gateway
    log_info "Checking API Gateway..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API Gateway is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    if [ $attempt -eq $max_attempts ]; then
        log_warning "API Gateway may not be fully ready"
    fi

    # Wait for Spark Master
    log_info "Checking Spark Master..."
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8080 > /dev/null 2>&1; then
            log_success "Spark Master is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    # Wait for Grafana
    log_info "Checking Grafana..."
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
            log_success "Grafana is ready"
            break
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    log_success "All services are ready"
}

show_status() {
    log_info "Service Status:"
    echo ""
    docker-compose ps
    echo ""
}

show_urls() {
    log_success "Deployment Complete! 🎉"
    echo ""
    echo "Access the services:"
    echo "  📊 Spark Master UI:    http://localhost:8080"
    echo "  🔌 API Gateway:        http://localhost:8000"
    echo "  📚 API Documentation:  http://localhost:8000/docs"
    echo "  📈 Grafana:           http://localhost:3000 (admin/admin123)"
    echo "  📉 Prometheus:        http://localhost:9090"
    echo ""
    echo "Database Connection:"
    echo "  Host: localhost"
    echo "  Port: 5432"
    echo "  Database: sparktest_db"
    echo "  User: sparktest"
    echo "  Password: sparktest123"
    echo ""
    echo "Redis Connection:"
    echo "  Host: localhost"
    echo "  Port: 6379"
    echo ""
}

################################################################################
# Main Deployment Flow
################################################################################

main() {
    print_banner

    log_info "Starting SparkTest deployment..."
    echo ""

    check_dependencies
    create_directories
    setup_monitoring
    setup_database
    start_services
    wait_for_services
    show_status
    show_urls

    log_success "Deployment completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Run integration tests: ./run_integration_tests.sh"
    echo "  2. Run benchmarks: ./benchmark_suite.sh"
    echo "  3. View logs: docker-compose logs -f"
    echo "  4. Stop services: docker-compose down"
    echo ""
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Deploy the SparkTest multi-agent system"
        echo ""
        echo "Options:"
        echo "  -h, --help     Show this help message"
        echo "  --clean        Remove all containers and volumes before deploying"
        echo ""
        exit 0
        ;;
    --clean)
        log_warning "Cleaning up existing deployment..."
        docker-compose down -v
        log_success "Cleanup complete"
        ;;
esac

main
