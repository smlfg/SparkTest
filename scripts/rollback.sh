#!/bin/bash

################################################################################
# SparkTest Rollback Script
# Rollback to previous version or state
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
STATE_FILE="$SCRIPT_DIR/../.deployment_state"

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
    echo -e "${YELLOW}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              SparkTest Rollback System                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

save_current_state() {
    log_info "Saving current state..."

    cat > "$STATE_FILE" <<EOF
deployment_time=$(date +%s)
deployment_date=$(date)
git_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
git_branch=$(git branch --show-current 2>/dev/null || echo "unknown")
docker_compose_checksum=$(md5sum docker-compose.yml | cut -d' ' -f1)
EOF

    log_success "Current state saved"
}

get_rollback_options() {
    log_info "Available rollback options:"
    echo ""

    # Option 1: Rollback to previous backup
    if [ -d "$BACKUP_DIR" ] && [ "$(ls -A $BACKUP_DIR/*.tar.gz 2>/dev/null)" ]; then
        echo "1. Rollback to previous backup"
        echo "   Available backups:"
        ls -1t "$BACKUP_DIR"/*.tar.gz | head -5 | nl -w2 -s'. '
        echo ""
    fi

    # Option 2: Rollback to previous git commit
    if git rev-parse --git-dir > /dev/null 2>&1; then
        echo "2. Rollback to previous git commit"
        echo "   Recent commits:"
        git log --oneline -5 | nl -w2 -s'. '
        echo ""
    fi

    # Option 3: Rollback Docker images
    echo "3. Rollback Docker images to previous tags"
    echo ""

    # Option 4: Rollback configuration files
    echo "4. Rollback configuration files only"
    echo ""
}

rollback_from_backup() {
    local backup_path=$1

    log_info "Rolling back from backup: $backup_path"

    if [ ! -f "$backup_path" ]; then
        log_error "Backup file not found: $backup_path"
        return 1
    fi

    # Create emergency backup of current state
    log_info "Creating emergency backup of current state..."
    ./scripts/backup.sh > /dev/null 2>&1 || true

    # Restore from backup
    log_info "Restoring from backup..."
    ./scripts/restore.sh "$backup_path"

    log_success "Rollback from backup completed"
}

rollback_git_commit() {
    local commit_hash=$1

    log_warning "⚠️  This will reset your git repository to commit: $commit_hash"
    read -p "Are you sure? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        log_info "Rollback cancelled"
        return 1
    fi

    log_info "Rolling back to git commit: $commit_hash"

    # Create backup before git operations
    log_info "Creating backup before rollback..."
    ./scripts/backup.sh > /dev/null 2>&1 || true

    # Stop services
    log_info "Stopping services..."
    docker-compose down

    # Git rollback
    log_info "Performing git reset..."
    git reset --hard "$commit_hash"

    # Rebuild and restart
    log_info "Rebuilding services..."
    docker-compose build

    log_info "Starting services..."
    docker-compose up -d

    log_success "Git rollback completed"
}

rollback_docker_images() {
    log_info "Rolling back Docker images..."

    # Stop services
    log_info "Stopping services..."
    docker-compose down

    # Pull previous image versions
    log_info "Pulling previous image versions..."

    # This is a placeholder - in production, you'd specify previous tags
    # docker pull sparktest-api:previous
    # docker pull sparktest-test:previous

    log_warning "Docker image rollback requires specific image tags"
    log_info "Please specify image versions in docker-compose.yml"

    log_success "Docker images rollback prepared"
}

rollback_configuration() {
    log_info "Rolling back configuration files..."

    # Look for backup configs
    if [ -f "docker-compose.yml.backup" ]; then
        log_info "Restoring docker-compose.yml from backup..."
        cp docker-compose.yml docker-compose.yml.rollback
        mv docker-compose.yml.backup docker-compose.yml
        log_success "docker-compose.yml restored"
    else
        log_warning "No backup configuration found"
    fi

    # Restart services with old config
    log_info "Restarting services with rolled back configuration..."
    docker-compose down
    docker-compose up -d

    log_success "Configuration rollback completed"
}

verify_rollback() {
    log_info "Verifying rollback..."

    # Wait for services
    sleep 10

    # Run health check
    if ./scripts/health_check.sh > /dev/null 2>&1; then
        log_success "Health check passed"
        return 0
    else
        log_error "Health check failed after rollback"
        return 1
    fi
}

automated_rollback() {
    log_warning "⚠️  AUTOMATED ROLLBACK INITIATED"

    # Try to restore from latest backup
    local latest_backup="$BACKUP_DIR/latest.tar.gz"

    if [ -f "$latest_backup" ]; then
        log_info "Restoring from latest backup..."
        rollback_from_backup "$latest_backup"

        if verify_rollback; then
            log_success "Automated rollback successful"
            return 0
        fi
    fi

    log_error "Automated rollback failed"
    return 1
}

interactive_rollback() {
    print_banner

    log_info "Interactive Rollback Mode"
    echo ""

    get_rollback_options

    read -p "Select rollback option (1-4): " option

    case $option in
        1)
            echo ""
            read -p "Enter backup number or path: " backup_choice

            if [[ "$backup_choice" =~ ^[0-9]+$ ]]; then
                # User entered a number from the list
                backup_path=$(ls -1t "$BACKUP_DIR"/*.tar.gz | sed -n "${backup_choice}p")
            else
                # User entered a full path
                backup_path="$backup_choice"
            fi

            rollback_from_backup "$backup_path"
            ;;

        2)
            echo ""
            read -p "Enter commit hash or number: " commit_choice

            if [[ "$commit_choice" =~ ^[0-9]+$ ]]; then
                # User entered a number from the list
                commit_hash=$(git log --oneline | sed -n "${commit_choice}p" | cut -d' ' -f1)
            else
                # User entered a commit hash
                commit_hash="$commit_choice"
            fi

            rollback_git_commit "$commit_hash"
            ;;

        3)
            rollback_docker_images
            ;;

        4)
            rollback_configuration
            ;;

        *)
            log_error "Invalid option"
            exit 1
            ;;
    esac

    echo ""
    log_info "Verifying rollback..."
    if verify_rollback; then
        log_success "Rollback completed successfully!"
    else
        log_error "Rollback verification failed"
        log_info "You may need to manually investigate the issue"
    fi
}

################################################################################
# Main Rollback Flow
################################################################################

main() {
    local mode="${1:-interactive}"

    case "$mode" in
        --auto|--automated)
            automated_rollback
            ;;

        --backup)
            if [ -z "$2" ]; then
                log_error "Backup path required"
                echo "Usage: $0 --backup <path_to_backup>"
                exit 1
            fi
            rollback_from_backup "$2"
            verify_rollback
            ;;

        --git)
            if [ -z "$2" ]; then
                log_error "Commit hash required"
                echo "Usage: $0 --git <commit_hash>"
                exit 1
            fi
            rollback_git_commit "$2"
            verify_rollback
            ;;

        --config)
            rollback_configuration
            verify_rollback
            ;;

        --help|-h)
            echo "Usage: $0 [MODE] [OPTIONS]"
            echo ""
            echo "Rollback SparkTest to a previous state"
            echo ""
            echo "Modes:"
            echo "  (no args)         Interactive mode (default)"
            echo "  --auto            Automated rollback to latest backup"
            echo "  --backup <path>   Rollback to specific backup"
            echo "  --git <commit>    Rollback to specific git commit"
            echo "  --config          Rollback configuration files only"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Interactive mode"
            echo "  $0 --auto                            # Auto rollback"
            echo "  $0 --backup backups/latest.tar.gz   # Specific backup"
            echo "  $0 --git abc123                      # Specific commit"
            echo ""
            exit 0
            ;;

        *)
            interactive_rollback
            ;;
    esac
}

main "$@"

exit $?
