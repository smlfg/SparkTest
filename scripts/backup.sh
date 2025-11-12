#!/bin/bash

################################################################################
# SparkTest Backup Script
# Creates complete backup of all data and configurations
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$SCRIPT_DIR/../backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="sparktest_backup_${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

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
    echo "║              SparkTest Backup System                        ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_services() {
    log_info "Checking if services are running..."

    if ! docker-compose ps | grep -q "Up"; then
        log_warning "Services are not running. Starting services..."
        docker-compose up -d
        sleep 10
    fi

    log_success "Services are running"
}

create_backup_directory() {
    log_info "Creating backup directory..."
    mkdir -p "$BACKUP_PATH"
    log_success "Backup directory created: $BACKUP_PATH"
}

backup_database() {
    log_info "Backing up PostgreSQL database..."

    docker-compose exec -T postgres pg_dump -U sparktest sparktest_db \
        > "${BACKUP_PATH}/database.sql"

    if [ $? -eq 0 ]; then
        log_success "Database backup completed"
    else
        log_error "Database backup failed"
        return 1
    fi
}

backup_redis() {
    log_info "Backing up Redis data..."

    # Trigger Redis save
    docker-compose exec -T redis redis-cli SAVE

    # Copy RDB file
    docker cp $(docker-compose ps -q redis):/data/dump.rdb "${BACKUP_PATH}/redis.rdb" 2>/dev/null || true

    log_success "Redis backup completed"
}

backup_configurations() {
    log_info "Backing up configurations..."

    # Copy configuration files
    cp docker-compose.yml "${BACKUP_PATH}/"
    cp -r monitoring "${BACKUP_PATH}/" 2>/dev/null || true
    cp .env "${BACKUP_PATH}/" 2>/dev/null || true
    cp -r database/init "${BACKUP_PATH}/database_init" 2>/dev/null || true

    log_success "Configuration backup completed"
}

backup_spark_data() {
    log_info "Backing up Spark data and logs..."

    # Backup Spark jobs
    if [ -d "spark/jobs" ]; then
        cp -r spark/jobs "${BACKUP_PATH}/"
    fi

    # Backup Spark data
    if [ -d "spark/data" ]; then
        cp -r spark/data "${BACKUP_PATH}/"
    fi

    # Backup Spark logs (last 7 days only)
    if [ -d "spark/logs" ]; then
        mkdir -p "${BACKUP_PATH}/spark_logs"
        find spark/logs -type f -mtime -7 -exec cp {} "${BACKUP_PATH}/spark_logs/" \; 2>/dev/null || true
    fi

    log_success "Spark data backup completed"
}

backup_volumes() {
    log_info "Backing up Docker volumes..."

    # List volumes
    docker volume ls | grep sparktest > "${BACKUP_PATH}/volumes.txt" || true

    # Backup volume data
    for volume in $(docker volume ls -q | grep sparktest); do
        log_info "Backing up volume: $volume"
        docker run --rm \
            -v ${volume}:/volume \
            -v ${BACKUP_PATH}:/backup \
            alpine tar czf /backup/${volume}.tar.gz -C /volume . 2>/dev/null || true
    done

    log_success "Volume backup completed"
}

backup_metrics() {
    log_info "Backing up metrics and monitoring data..."

    # Export Prometheus data (if accessible)
    mkdir -p "${BACKUP_PATH}/metrics"

    # Get current metrics
    curl -s http://localhost:8000/metrics > "${BACKUP_PATH}/metrics/api_metrics.txt" 2>/dev/null || true
    curl -s http://localhost:9090/api/v1/query?query=up > "${BACKUP_PATH}/metrics/prometheus_status.json" 2>/dev/null || true

    log_success "Metrics backup completed"
}

create_manifest() {
    log_info "Creating backup manifest..."

    cat > "${BACKUP_PATH}/MANIFEST.txt" <<EOF
SparkTest Backup Manifest
========================

Backup Name: ${BACKUP_NAME}
Backup Date: $(date)
Backup Path: ${BACKUP_PATH}

Components Backed Up:
- PostgreSQL Database
- Redis Data
- Configuration Files
- Spark Jobs and Data
- Docker Volumes
- Metrics and Logs

Files:
$(ls -lh "${BACKUP_PATH}" | tail -n +2)

Restore Command:
./scripts/restore.sh ${BACKUP_PATH}

Notes:
- Keep this backup in a secure location
- Test restore procedure regularly
- Backups older than 30 days should be archived
EOF

    log_success "Manifest created"
}

compress_backup() {
    log_info "Compressing backup..."

    cd "$BACKUP_DIR"
    tar czf "${BACKUP_NAME}.tar.gz" "${BACKUP_NAME}"

    if [ $? -eq 0 ]; then
        # Remove uncompressed directory
        rm -rf "${BACKUP_NAME}"
        log_success "Backup compressed: ${BACKUP_NAME}.tar.gz"
    else
        log_error "Compression failed"
        return 1
    fi
}

cleanup_old_backups() {
    log_info "Cleaning up old backups (keeping last 7)..."

    # Keep only last 7 backups
    cd "$BACKUP_DIR"
    ls -t sparktest_backup_*.tar.gz | tail -n +8 | xargs rm -f 2>/dev/null || true

    log_success "Old backups cleaned up"
}

create_latest_symlink() {
    log_info "Creating 'latest' symlink..."

    cd "$BACKUP_DIR"
    ln -sf "${BACKUP_NAME}.tar.gz" latest.tar.gz

    log_success "Latest symlink created"
}

calculate_backup_size() {
    local size=$(du -sh "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz" | cut -f1)
    echo "$size"
}

################################################################################
# Main Backup Flow
################################################################################

main() {
    print_banner

    log_info "Starting backup process..."
    log_info "Backup will be created at: $BACKUP_PATH"
    echo ""

    check_services
    create_backup_directory

    # Perform backups
    backup_database || log_warning "Database backup had issues"
    backup_redis || log_warning "Redis backup had issues"
    backup_configurations
    backup_spark_data
    backup_volumes
    backup_metrics

    # Create manifest and compress
    create_manifest
    compress_backup

    # Cleanup
    cleanup_old_backups
    create_latest_symlink

    # Summary
    echo ""
    log_success "╔══════════════════════════════════════════════════════════════╗"
    log_success "║           Backup Completed Successfully!                    ║"
    log_success "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Backup Details:"
    echo "  📦 Name: ${BACKUP_NAME}.tar.gz"
    echo "  📂 Location: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    echo "  💾 Size: $(calculate_backup_size)"
    echo "  🔗 Latest: ${BACKUP_DIR}/latest.tar.gz"
    echo ""
    echo "To restore this backup:"
    echo "  ./scripts/restore.sh ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz"
    echo ""
}

# Handle arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Create a complete backup of SparkTest system"
        echo ""
        echo "Options:"
        echo "  -h, --help     Show this help message"
        echo ""
        echo "Environment Variables:"
        echo "  BACKUP_DIR     Directory for backups (default: ../backups)"
        echo ""
        exit 0
        ;;
esac

main

exit 0
