#!/bin/bash
# Student User Management - List and Manage Users
# View, modify, and manage student accounts

set -e

WORKSPACE_BASE="${WORKSPACE_BASE:-/workspace}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# List all student users
list_students() {
    log_info "Student Users on $(hostname)"
    echo ""

    # Get all users with workspace directories
    local student_count=0

    printf "%-15s %-10s %-15s %-15s %-20s\n" "USERNAME" "UID" "QUOTA USED" "QUOTA LIMIT" "GROUPS"
    printf "%.s=" {1..80}
    echo ""

    for workspace in "$WORKSPACE_BASE"/*; do
        if [ -d "$workspace" ]; then
            local username=$(basename "$workspace")

            if id "$username" &>/dev/null; then
                local uid=$(id -u "$username")
                local groups=$(id -nG "$username" | tr ' ' ',' | cut -c1-18)

                # Get quota info
                local quota_used=""
                local quota_limit=""
                if command -v quota &> /dev/null; then
                    local quota_info=$(quota -s -u "$username" 2>/dev/null | grep "$WORKSPACE_BASE" || echo "")
                    if [ -n "$quota_info" ]; then
                        quota_used=$(echo "$quota_info" | awk '{print $2}')
                        quota_limit=$(echo "$quota_info" | awk '{print $3}')
                    fi
                fi

                # Fallback to du if quota not available
                if [ -z "$quota_used" ]; then
                    quota_used=$(du -sh "$workspace" 2>/dev/null | cut -f1)
                    quota_limit="N/A"
                fi

                printf "%-15s %-10s %-15s %-15s %-20s\n" \
                    "$username" "$uid" "$quota_used" "$quota_limit" "$groups"

                ((student_count++))
            fi
        fi
    done

    echo ""
    log_info "Total student users: $student_count"
}

# Show detailed info for a user
show_user_info() {
    local username="$1"

    if ! id "$username" &>/dev/null; then
        log_error "User $username does not exist"
        return 1
    fi

    echo ""
    echo "Student User: $username"
    echo "======================================"
    echo "UID: $(id -u "$username")"
    echo "GID: $(id -g "$username")"
    echo "Groups: $(id -nG "$username")"
    echo "Home: /home/$username"
    echo "Shell: $(getent passwd "$username" | cut -d: -f7)"
    echo "Workspace: $WORKSPACE_BASE/$username"
    echo ""

    # Workspace info
    if [ -d "$WORKSPACE_BASE/$username" ]; then
        echo "Workspace Contents:"
        ls -lah "$WORKSPACE_BASE/$username" 2>/dev/null | tail -n +4
        echo ""
        echo "Workspace Size:"
        du -h --max-depth=1 "$WORKSPACE_BASE/$username" 2>/dev/null
        echo ""
    fi

    # Quota info
    if command -v quota &> /dev/null; then
        echo "Quota Information:"
        quota -s -u "$username" 2>/dev/null || echo "  No quota set"
        echo ""
    fi

    # Process info
    echo "Running Processes:"
    ps -u "$username" -o pid,ppid,%cpu,%mem,cmd --no-headers 2>/dev/null | head -10 || echo "  No processes running"
    echo ""

    # Login history
    echo "Recent Logins:"
    last -n 5 "$username" 2>/dev/null || echo "  No login history"
    echo ""
}

# Reset user password
reset_password() {
    local username="$1"

    if ! id "$username" &>/dev/null; then
        log_error "User $username does not exist"
        return 1
    fi

    log_info "Resetting password for: $username"

    # Generate random password
    local new_password="spark$(date +%Y)_$(openssl rand -hex 4)"

    echo "$username:$new_password" | chpasswd
    passwd -e "$username"  # Force change on next login

    log_info "New temporary password: $new_password"
    log_warn "User must change password on next login"
}

# Update user quota
update_quota() {
    local username="$1"
    local quota_soft="$2"
    local quota_hard="$3"

    if ! id "$username" &>/dev/null; then
        log_error "User $username does not exist"
        return 1
    fi

    if ! command -v setquota &> /dev/null; then
        log_error "setquota command not available"
        return 1
    fi

    log_info "Updating quota for: $username"
    log_info "Soft limit: $quota_soft"
    log_info "Hard limit: $quota_hard"

    local soft_bytes=$(numfmt --from=iec "$quota_soft")
    local hard_bytes=$(numfmt --from=iec "$quota_hard")
    local soft_gb=$((soft_bytes / 1024 / 1024))
    local hard_gb=$((hard_bytes / 1024 / 1024))

    setquota -u "$username" "$soft_gb" "$hard_gb" 0 0 "$WORKSPACE_BASE"

    log_info "✅ Quota updated"
    quota -s -u "$username"
}

# Lock user account
lock_user() {
    local username="$1"

    if ! id "$username" &>/dev/null; then
        log_error "User $username does not exist"
        return 1
    fi

    log_info "Locking user account: $username"
    passwd -l "$username"

    log_info "✅ User account locked"
}

# Unlock user account
unlock_user() {
    local username="$1"

    if ! id "$username" &>/dev/null; then
        log_error "User $username does not exist"
        return 1
    fi

    log_info "Unlocking user account: $username"
    passwd -u "$username"

    log_info "✅ User account unlocked"
}

# Export user data
export_user_data() {
    local username="$1"
    local output_dir="${2:-.}"

    if ! id "$username" &>/dev/null; then
        log_error "User $username does not exist"
        return 1
    fi

    local workspace="$WORKSPACE_BASE/$username"
    if [ ! -d "$workspace" ]; then
        log_error "Workspace not found: $workspace"
        return 1
    fi

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local archive_file="$output_dir/${username}_export_${timestamp}.tar.gz"

    log_info "Exporting data for: $username"
    log_info "Output: $archive_file"

    tar -czf "$archive_file" -C "$WORKSPACE_BASE" "$username" 2>/dev/null

    if [ -f "$archive_file" ]; then
        log_info "✅ Export complete"
        log_info "Archive size: $(du -h "$archive_file" | cut -f1)"
    else
        log_error "Export failed"
        return 1
    fi
}

# Show usage
show_help() {
    cat <<EOF
Student User Management Tool

Usage: $0 <command> [options]

Commands:
  list                          List all student users
  info <username>              Show detailed user information
  reset-password <username>    Reset user password
  update-quota <username> <soft> <hard>
                               Update user quota limits
  lock <username>              Lock user account
  unlock <username>            Unlock user account
  export <username> [dir]      Export user data
  help                         Show this help message

Examples:
  $0 list
  $0 info student01
  $0 reset-password student01
  $0 update-quota student01 100G 110G
  $0 lock student01
  $0 unlock student01
  $0 export student01 /backup

Environment Variables:
  WORKSPACE_BASE              Workspace directory (default: /workspace)

EOF
}

# Main function
main() {
    local command="${1:-list}"

    case "$command" in
        list)
            list_students
            ;;
        info)
            if [ -z "$2" ]; then
                log_error "Username required"
                exit 1
            fi
            show_user_info "$2"
            ;;
        reset-password)
            if [ "$EUID" -ne 0 ]; then
                log_error "Must run as root"
                exit 1
            fi
            if [ -z "$2" ]; then
                log_error "Username required"
                exit 1
            fi
            reset_password "$2"
            ;;
        update-quota)
            if [ "$EUID" -ne 0 ]; then
                log_error "Must run as root"
                exit 1
            fi
            if [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]; then
                log_error "Usage: $0 update-quota <username> <soft> <hard>"
                exit 1
            fi
            update_quota "$2" "$3" "$4"
            ;;
        lock)
            if [ "$EUID" -ne 0 ]; then
                log_error "Must run as root"
                exit 1
            fi
            if [ -z "$2" ]; then
                log_error "Username required"
                exit 1
            fi
            lock_user "$2"
            ;;
        unlock)
            if [ "$EUID" -ne 0 ]; then
                log_error "Must run as root"
                exit 1
            fi
            if [ -z "$2" ]; then
                log_error "Username required"
                exit 1
            fi
            unlock_user "$2"
            ;;
        export)
            if [ "$EUID" -ne 0 ]; then
                log_error "Must run as root"
                exit 1
            fi
            if [ -z "$2" ]; then
                log_error "Username required"
                exit 1
            fi
            export_user_data "$2" "${3:-.}"
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

main "$@"
