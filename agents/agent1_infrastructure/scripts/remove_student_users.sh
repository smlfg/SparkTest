#!/bin/bash
# Student User Management - Remove Users
# Safely removes student accounts and optionally archives their data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_BASE="${WORKSPACE_BASE:-/workspace}"
ARCHIVE_DIR="${ARCHIVE_DIR:-/archive/students}"
ARCHIVE_DATA="${ARCHIVE_DATA:-true}"
FORCE="${FORCE:-false}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root"
    exit 1
fi

# Archive user data
archive_user_data() {
    local username="$1"
    local workspace="$WORKSPACE_BASE/$username"
    local home="/home/$username"

    if [ "$ARCHIVE_DATA" != "true" ]; then
        log_info "Skipping data archive (ARCHIVE_DATA=false)"
        return 0
    fi

    log_info "Archiving data for user: $username"

    # Create archive directory
    mkdir -p "$ARCHIVE_DIR"

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local archive_file="$ARCHIVE_DIR/${username}_${timestamp}.tar.gz"

    # Archive workspace and home
    tar -czf "$archive_file" \
        -C "$WORKSPACE_BASE" "$username" \
        -C /home "$username" \
        2>/dev/null || log_warn "Some files could not be archived"

    if [ -f "$archive_file" ]; then
        log_info "Data archived to: $archive_file"
        log_info "Archive size: $(du -h "$archive_file" | cut -f1)"
    else
        log_error "Failed to create archive"
        return 1
    fi
}

# Remove user
remove_student_user() {
    local username="$1"

    log_info "Removing user: $username"

    # Check if user exists
    if ! id "$username" &>/dev/null; then
        log_warn "User $username does not exist"
        return 1
    fi

    # Kill user processes
    log_info "Killing processes for user: $username"
    pkill -u "$username" 2>/dev/null || true
    sleep 2
    pkill -9 -u "$username" 2>/dev/null || true

    # Archive data if requested
    if [ "$ARCHIVE_DATA" = "true" ]; then
        archive_user_data "$username" || log_warn "Archive failed, continuing with removal"
    fi

    # Remove workspace
    local workspace="$WORKSPACE_BASE/$username"
    if [ -d "$workspace" ]; then
        log_info "Removing workspace: $workspace"
        rm -rf "$workspace"
    fi

    # Remove user quota
    if command -v setquota &> /dev/null; then
        setquota -u "$username" 0 0 0 0 "$WORKSPACE_BASE" 2>/dev/null || true
    fi

    # Remove resource limits
    if [ -f "/etc/security/limits.d/${username}.conf" ]; then
        rm -f "/etc/security/limits.d/${username}.conf"
    fi

    # Remove user account
    userdel -r "$username" 2>/dev/null || {
        log_warn "Could not remove user completely, trying without -r"
        userdel "$username" 2>/dev/null || log_error "Failed to remove user"
    }

    log_info "✅ Removed user: $username"
}

# Main function
main() {
    if [ $# -eq 0 ]; then
        log_error "No usernames provided"
        echo "Usage: $0 <username1> [username2] [...]"
        echo ""
        echo "Options:"
        echo "  ARCHIVE_DATA=true/false  Archive user data before deletion (default: true)"
        echo "  ARCHIVE_DIR=/path        Archive directory (default: /archive/students)"
        echo "  FORCE=true              Skip confirmation prompt"
        echo ""
        echo "Example:"
        echo "  $0 student01 student02"
        echo "  ARCHIVE_DATA=false $0 student01"
        exit 1
    fi

    log_info "Student user removal"
    log_info "Users to remove: $*"
    log_info "Archive data: $ARCHIVE_DATA"
    log_info "Archive directory: $ARCHIVE_DIR"

    # Confirmation prompt
    if [ "$FORCE" != "true" ]; then
        echo ""
        read -p "Are you sure you want to remove these users? (yes/no): " -r
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log_info "Cancelled by user"
            exit 0
        fi
    fi

    local success_count=0
    local fail_count=0

    for username in "$@"; do
        if remove_student_user "$username"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
        echo ""
    done

    log_info "Removal completed"
    log_info "Successful: $success_count"
    log_info "Failed: $fail_count"

    if [ $fail_count -eq 0 ]; then
        log_info "✅ All users removed successfully!"
    else
        log_warn "⚠️  Some users failed to remove"
        return 1
    fi
}

main "$@"
