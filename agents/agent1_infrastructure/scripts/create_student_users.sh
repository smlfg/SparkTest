#!/bin/bash
# Student User Management - Create Users
# Creates student accounts with workspaces, quotas, and proper permissions

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${CONFIG_FILE:-${SCRIPT_DIR}/../config/students.conf}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Default configuration
DEFAULT_STUDENTS=(
    "student01"
    "student02"
    "student03"
    "student04"
    "student05"
)

WORKSPACE_BASE="${WORKSPACE_BASE:-/workspace}"
QUOTA_SOFT="${QUOTA_SOFT:-50G}"
QUOTA_HARD="${QUOTA_HARD:-55G}"
DEFAULT_GROUPS="${DEFAULT_GROUPS:-docker,sudo}"
DEFAULT_SHELL="${DEFAULT_SHELL:-/bin/bash}"
SSH_KEY_TYPE="${SSH_KEY_TYPE:-ed25519}"
CREATE_SSH_KEYS="${CREATE_SSH_KEYS:-true}"

# Load configuration if exists
if [ -f "$CONFIG_FILE" ]; then
    log_info "Loading configuration from $CONFIG_FILE"
    source "$CONFIG_FILE"
else
    log_warn "Config file not found, using defaults"
    STUDENTS=("${DEFAULT_STUDENTS[@]}")
fi

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    log_error "This script must be run as root"
    exit 1
fi

# Check for required commands
check_dependencies() {
    local missing_deps=()

    for cmd in useradd usermod mkdir chown setquota ssh-keygen; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        log_error "Missing required commands: ${missing_deps[*]}"
        log_info "Install with: apt-get install quota openssh-server"
        exit 1
    fi
}

# Setup quota support
setup_quota() {
    log_info "Setting up quota support..."

    # Check if quota is already enabled
    if ! grep -q "usrquota" /etc/fstab; then
        log_warn "Quota not enabled in /etc/fstab for $WORKSPACE_BASE"
        log_info "You may need to add 'usrquota,grpquota' to mount options"
        log_info "Example: UUID=xxx $WORKSPACE_BASE ext4 defaults,usrquota,grpquota 0 2"
    fi

    # Create workspace base directory
    if [ ! -d "$WORKSPACE_BASE" ]; then
        mkdir -p "$WORKSPACE_BASE"
        log_info "Created workspace directory: $WORKSPACE_BASE"
    fi

    # Initialize quota database
    if [ -f "$WORKSPACE_BASE/aquota.user" ]; then
        log_debug "Quota database already exists"
    else
        log_info "Initializing quota database..."
        quotaoff -v "$WORKSPACE_BASE" 2>/dev/null || true
        quotacheck -cugm "$WORKSPACE_BASE" 2>/dev/null || true
        quotaon -v "$WORKSPACE_BASE" 2>/dev/null || log_warn "Could not enable quotas (may need reboot)"
    fi
}

# Create individual student user
create_student_user() {
    local username="$1"

    log_info "Creating user: $username"

    # Check if user already exists
    if id "$username" &>/dev/null; then
        log_warn "User $username already exists, skipping creation"
        return 0
    fi

    # Create user with home directory
    useradd -m -s "$DEFAULT_SHELL" "$username"

    # Set default password (user must change on first login)
    echo "$username:spark$(date +%Y)" | chpasswd
    passwd -e "$username"  # Force password change on first login

    # Add to groups
    IFS=',' read -ra GROUPS <<< "$DEFAULT_GROUPS"
    for group in "${GROUPS[@]}"; do
        if getent group "$group" > /dev/null; then
            usermod -aG "$group" "$username"
            log_debug "Added $username to group: $group"
        else
            log_warn "Group $group does not exist"
        fi
    done

    # Create workspace structure
    local workspace="$WORKSPACE_BASE/$username"
    mkdir -p "$workspace"/{datasets,models,checkpoints,notebooks,scripts,logs}

    # Set ownership
    chown -R "$username":"$username" "$workspace"

    # Set permissions
    chmod 750 "$workspace"
    chmod 755 "$workspace"/{datasets,models,checkpoints,notebooks,scripts}
    chmod 700 "$workspace"/logs

    log_info "Created workspace: $workspace"

    # Set quota
    if command -v setquota &> /dev/null; then
        local soft_bytes=$(numfmt --from=iec "$QUOTA_SOFT")
        local hard_bytes=$(numfmt --from=iec "$QUOTA_HARD")
        local soft_gb=$((soft_bytes / 1024 / 1024))
        local hard_gb=$((hard_bytes / 1024 / 1024))

        setquota -u "$username" "$soft_gb" "$hard_gb" 0 0 "$WORKSPACE_BASE" 2>/dev/null || \
            log_warn "Could not set quota for $username (quotas may not be enabled)"

        log_debug "Set quota: soft=$QUOTA_SOFT hard=$QUOTA_HARD"
    fi

    # Generate SSH key for the user
    if [ "$CREATE_SSH_KEYS" = "true" ]; then
        local ssh_dir="/home/$username/.ssh"
        local ssh_key="$ssh_dir/id_$SSH_KEY_TYPE"

        sudo -u "$username" mkdir -p "$ssh_dir"
        sudo -u "$username" chmod 700 "$ssh_dir"

        if [ ! -f "$ssh_key" ]; then
            sudo -u "$username" ssh-keygen -t "$SSH_KEY_TYPE" -f "$ssh_key" -N "" -C "$username@spark-cluster"
            log_info "Generated SSH key: $ssh_key"
        fi

        # Create authorized_keys file
        touch "$ssh_dir/authorized_keys"
        chown "$username":"$username" "$ssh_dir/authorized_keys"
        chmod 600 "$ssh_dir/authorized_keys"
    fi

    # Create welcome message
    cat > "/home/$username/.spark_welcome" <<EOF
Welcome to Spark Cluster, $username!

Your workspace: $workspace
Quota: $QUOTA_SOFT (soft) / $QUOTA_HARD (hard)

Directory structure:
  - datasets/     : Store your datasets here
  - models/       : Save trained models
  - checkpoints/  : Training checkpoints
  - notebooks/    : Jupyter notebooks
  - scripts/      : Python/bash scripts
  - logs/         : Application logs

Useful commands:
  - quota -s      : Check your disk usage
  - nvidia-smi    : Check GPU status
  - docker ps     : List your containers

Documentation: https://docs.spark-cluster.local

For support, contact your cluster administrator.
EOF

    chown "$username":"$username" "/home/$username/.spark_welcome"

    # Add welcome message to bashrc
    if ! grep -q ".spark_welcome" "/home/$username/.bashrc"; then
        echo "" >> "/home/$username/.bashrc"
        echo "# Spark Cluster Welcome" >> "/home/$username/.bashrc"
        echo "[ -f ~/.spark_welcome ] && cat ~/.spark_welcome" >> "/home/$username/.bashrc"
    fi

    # Create resource limits
    cat >> /etc/security/limits.d/"$username".conf <<EOF
# Resource limits for $username
$username soft nproc 1024
$username hard nproc 2048
$username soft nofile 4096
$username hard nofile 8192
$username soft memlock unlimited
$username hard memlock unlimited
EOF

    log_info "✅ Successfully created user: $username"
}

# Generate student list report
generate_report() {
    local report_file="${1:-/tmp/student_users_$(date +%Y%m%d_%H%M%S).txt}"

    {
        echo "Spark Cluster - Student Users Report"
        echo "Generated: $(date)"
        echo "======================================"
        echo ""

        for username in "${STUDENTS[@]}"; do
            if id "$username" &>/dev/null; then
                echo "User: $username"
                echo "  Home: /home/$username"
                echo "  Workspace: $WORKSPACE_BASE/$username"
                echo "  Groups: $(id -nG "$username")"

                # Check quota
                if command -v quota &> /dev/null; then
                    echo "  Quota:"
                    quota -s -u "$username" 2>/dev/null | grep -v "^$" | sed 's/^/    /'
                fi

                # Check workspace size
                if [ -d "$WORKSPACE_BASE/$username" ]; then
                    local size=$(du -sh "$WORKSPACE_BASE/$username" 2>/dev/null | cut -f1)
                    echo "  Workspace size: $size"
                fi

                echo ""
            fi
        done

        echo "======================================"
        echo "Total users: ${#STUDENTS[@]}"
    } | tee "$report_file"

    log_info "Report saved to: $report_file"
}

# Main function
main() {
    log_info "Starting student user creation..."
    log_info "Workspace base: $WORKSPACE_BASE"
    log_info "Quota: $QUOTA_SOFT (soft) / $QUOTA_HARD (hard)"
    log_info "Users to create: ${#STUDENTS[@]}"

    check_dependencies
    setup_quota

    # Create each student user
    local success_count=0
    local fail_count=0

    for student in "${STUDENTS[@]}"; do
        if create_student_user "$student"; then
            ((success_count++))
        else
            ((fail_count++))
            log_error "Failed to create user: $student"
        fi
    done

    log_info "User creation completed"
    log_info "Successful: $success_count"
    log_info "Failed: $fail_count"

    # Generate report
    generate_report

    if [ $fail_count -eq 0 ]; then
        log_info "✅ All student users created successfully!"
    else
        log_warn "⚠️  Some users failed to create. Check logs above."
        return 1
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        --workspace)
            WORKSPACE_BASE="$2"
            shift 2
            ;;
        --quota-soft)
            QUOTA_SOFT="$2"
            shift 2
            ;;
        --quota-hard)
            QUOTA_HARD="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --config FILE       Configuration file path"
            echo "  --workspace DIR     Workspace base directory (default: /workspace)"
            echo "  --quota-soft SIZE   Soft quota limit (default: 50G)"
            echo "  --quota-hard SIZE   Hard quota limit (default: 55G)"
            echo "  --help              Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  WORKSPACE_BASE      Workspace base directory"
            echo "  QUOTA_SOFT          Soft quota limit"
            echo "  QUOTA_HARD          Hard quota limit"
            echo "  DEFAULT_GROUPS      Comma-separated groups (default: docker,sudo)"
            echo "  CREATE_SSH_KEYS     Generate SSH keys (default: true)"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run main function
main "$@"
