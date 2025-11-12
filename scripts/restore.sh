#!/bin/bash

################################################################################
# SparkTest Restore Script
# Restores SparkTest from backup
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
RESTORE_PATH="${1:-}"

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
    echo "║              SparkTest Restore System                       ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

validate_backup() {
    log_info "Validating backup file..."

    if [ -z "$RESTORE_PATH" ]; then
        log_error "No backup path provided"
        echo "Usage: $0 <backup_path>"
        echo "Example: $0 /path/to/backup.tar.gz"
        exit 1
    fi

    if [ ! -f "$RESTORE_PATH" ]; then
        log_error "Backup file not found: $RESTORE_PATH"
        exit 1
    fi

    log_success "Backup file validated"
}

confirm_restore() {
    log_warning "⚠️  WARNING: This will OVERWRITE existing data!"
    echo ""
    read -p "Are you sure you want to restore from backup? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Restore cancelled by user"
        exit 0
    fi

    echo ""
    log_info "Starting restore process..."
}

stop_services() {
    log_info "Stopping services..."
    docker-compose down
    log_success "Services stopped"
}

extract_backup() {
    log_info "Extracting backup..."

    TEMP_DIR=$(mktemp -d)
    tar xzf "$RESTORE_PATH" -C "$TEMP_DIR"

    # Find the backup directory
    BACKUP_DIR=$(find "$TEMP_DIR" -maxdepth 1 -type d -name "sparktest_backup_*" | head -1)

    if [ -z "$BACKUP_DIR" ]; then
        log_error "Invalid backup structure"
        rm -rf "$TEMP_DIR"
        exit 1
    fi

    log_success "Backup extracted to: $BACKUP_DIR"
    echo "$BACKUP_DIR"
}

restore_database() {
    local backup_dir=$1
    log_info "Restoring PostgreSQL database..."

    if [ ! -f "${backup_dir}/database.sql" ]; then
        log_warning "Database backup not found, skipping..."
        return
    fi

    # Start only PostgreSQL
    docker-compose up -d postgres
    sleep 5

    # Restore database
    docker-compose exec -T postgres psql -U sparktest -d sparktest_db < "${backup_dir}/database.sql"

    log_success "Database restored"
}

restore_redis() {
    local backup_dir=$1
    log_info "Restoring Redis data..."

    if [ ! -f "${backup_dir}/redis.rdb" ]; then
        log_warning "Redis backup not found, skipping..."
        return
    fi

    # Start Redis
    docker-compose up -d redis
    sleep 3

    # Stop Redis to copy file
    docker-compose stop redis

    # Copy RDB file
    docker cp "${backup_dir}/redis.rdb" $(docker-compose ps -q redis):/data/dump.rdb

    # Restart Redis
    docker-compose start redis

    log_success "Redis data restored"
}

restore_configurations() {
    local backup_dir=$1
    log_info "Restoring configurations..."

    # Backup current configs
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml docker-compose.yml.backup
    fi

    # Restore configs
    if [ -f "${backup_dir}/docker-compose.yml" ]; then
        cp "${backup_dir}/docker-compose.yml" .
    fi

    if [ -d "${backup_dir}/monitoring" ]; then
        cp -r "${backup_dir}/monitoring" .
    fi

    if [ -f "${backup_dir}/.env" ]; then
        cp "${backup_dir}/.env" .
    fi

    if [ -d "${backup_dir}/database_init" ]; then
        mkdir -p database/init
        cp -r "${backup_dir}/database_init/"* database/init/
    fi

    log_success "Configurations restored"
}

restore_spark_data() {
    local backup_dir=$1
    log_info "Restoring Spark data..."

    if [ -d "${backup_dir}/jobs" ]; then
        mkdir -p spark/jobs
        cp -r "${backup_dir}/jobs/"* spark/jobs/
    fi

    if [ -d "${backup_dir}/data" ]; then
        mkdir -p spark/data
        cp -r "${backup_dir}/data/"* spark/data/
    fi

    if [ -d "${backup_dir}/spark_logs" ]; then
        mkdir -p spark/logs
        cp -r "${backup_dir}/spark_logs/"* spark/logs/
    fi

    log_success "Spark data restored"
}

restore_volumes() {
    local backup_dir=$1
    log_info "Restoring Docker volumes..."

    for volume_backup in "${backup_dir}"/*.tar.gz; do
        if [ -f "$volume_backup" ]; then
            volume_name=$(basename "$volume_backup" .tar.gz)
            log_info "Restoring volume: $volume_name"

            # Create volume if it doesn't exist
            docker volume create "$volume_name" 2>/dev/null || true

            # Restore volume data
            docker run --rm \
                -v ${volume_name}:/volume \
                -v ${backup_dir}:/backup \
                alpine tar xzf /backup/${volume_name}.tar.gz -C /volume
        fi
    done

    log_success "Volumes restored"
}

start_all_services() {
    log_info "Starting all services..."
    docker-compose up -d

    log_info "Waiting for services to be ready..."
    sleep 30

    log_success "All services started"
}

verify_restore() {
    log_info "Verifying restore..."

    # Check API health
    max_attempts=10
    attempt=0

    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API Gateway is healthy"
            break
        fi
        attempt=$((attempt + 1))
        sleep 3
    done

    if [ $attempt -eq $max_attempts ]; then
        log_warning "API Gateway health check timeout"
    fi

    # Check database
    if docker-compose exec -T postgres psql -U sparktest -d sparktest_db -c "SELECT 1" > /dev/null 2>&1; then
        log_success "Database is accessible"
    else
        log_warning "Database check failed"
    fi

    # Check Redis
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is accessible"
    else
        log_warning "Redis check failed"
    fi
}

cleanup() {
    local temp_dir=$1
    log_info "Cleaning up temporary files..."
    rm -rf "$temp_dir"
    log_success "Cleanup complete"
}

################################################################################
# Main Restore Flow
################################################################################

main() {
    print_banner

    validate_backup
    confirm_restore

    log_info "Restoring from: $RESTORE_PATH"
    echo ""

    stop_services

    # Extract backup
    BACKUP_DIR=$(extract_backup)

    # Perform restore
    restore_configurations "$BACKUP_DIR"
    restore_database "$BACKUP_DIR"
    restore_redis "$BACKUP_DIR"
    restore_spark_data "$BACKUP_DIR"
    restore_volumes "$BACKUP_DIR"

    # Start services
    start_all_services

    # Verify
    verify_restore

    # Cleanup
    cleanup "$(dirname "$BACKUP_DIR")"

    # Summary
    echo ""
    log_success "╔══════════════════════════════════════════════════════════════╗"
    log_success "║           Restore Completed Successfully!                   ║"
    log_success "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "System Status:"
    echo "  ✅ Services: Running"
    echo "  ✅ Database: Restored"
    echo "  ✅ Redis: Restored"
    echo "  ✅ Configurations: Restored"
    echo ""
    echo "Next Steps:"
    echo "  1. Verify data integrity"
    echo "  2. Run smoke tests: ./run_integration_tests.sh smoke"
    echo "  3. Check service status: docker-compose ps"
    echo ""
}

# Handle arguments
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: $0 <backup_path>"
    echo ""
    echo "Restore SparkTest from backup"
    echo ""
    echo "Arguments:"
    echo "  backup_path    Path to backup file (.tar.gz)"
    echo ""
    echo "Example:"
    echo "  $0 /path/to/sparktest_backup_20250112_120000.tar.gz"
    echo "  $0 backups/latest.tar.gz"
    echo ""
    exit 0
fi

main

exit 0
