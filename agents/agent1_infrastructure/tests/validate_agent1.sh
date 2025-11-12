#!/bin/bash
# Agent 1 Infrastructure Validation Suite
# Tests all requirements from agent1_checklist.yaml

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
TESTS_SKIPPED=0
TESTS_TOTAL=0

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_fail() { echo -e "${RED}[FAIL]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[SKIP]${NC} $1"; }

run_test() {
    local name="$1"
    local command="$2"
    local optional="${3:-false}"

    ((TESTS_TOTAL++))

    echo ""
    log_info "Testing: $name"

    if eval "$command" &>/dev/null; then
        log_success "$name"
        ((TESTS_PASSED++))
        return 0
    else
        if [ "$optional" = "true" ]; then
            log_warn "$name (optional)"
            ((TESTS_SKIPPED++))
        else
            log_fail "$name"
            ((TESTS_FAILED++))
        fi
        return 1
    fi
}

check_file() {
    local file="$1"
    local optional="${2:-false}"

    ((TESTS_TOTAL++))

    if [ -f "$file" ]; then
        log_success "File exists: $file"
        ((TESTS_PASSED++))
        return 0
    else
        if [ "$optional" = "true" ]; then
            log_warn "File missing (optional): $file"
            ((TESTS_SKIPPED++))
        else
            log_fail "File missing: $file"
            ((TESTS_FAILED++))
        fi
        return 1
    fi
}

check_executable() {
    local file="$1"

    ((TESTS_TOTAL++))

    if [ -x "$file" ]; then
        log_success "Executable: $file"
        ((TESTS_PASSED++))
        return 0
    else
        log_fail "Not executable: $file"
        ((TESTS_FAILED++))
        return 1
    fi
}

check_content() {
    local file="$1"
    local pattern="$2"

    ((TESTS_TOTAL++))

    if [ ! -f "$file" ]; then
        log_fail "File not found: $file"
        ((TESTS_FAILED++))
        return 1
    fi

    if grep -q "$pattern" "$file" 2>/dev/null; then
        log_success "Pattern found in $file: $pattern"
        ((TESTS_PASSED++))
        return 0
    else
        log_fail "Pattern not found in $file: $pattern"
        ((TESTS_FAILED++))
        return 1
    fi
}

echo "======================================"
echo "Agent 1 Infrastructure Validation"
echo "======================================"
echo ""

# DELIVERABLES
echo "=== DELIVERABLES ==="

check_file "$BASE_DIR/scripts/setup_ssh.sh"
check_executable "$BASE_DIR/scripts/setup_ssh.sh"

check_file "$BASE_DIR/scripts/setup_tailscale.sh"
check_executable "$BASE_DIR/scripts/setup_tailscale.sh"

check_file "$BASE_DIR/playbooks/connect-two-sparks.yaml"
check_file "$BASE_DIR/playbooks/nccl.yaml"

check_file "$BASE_DIR/scripts/create_student_users.sh"
check_executable "$BASE_DIR/scripts/create_student_users.sh"

check_file "$BASE_DIR/scripts/manage_student_users.sh"
check_executable "$BASE_DIR/scripts/manage_student_users.sh"

check_file "$BASE_DIR/scripts/remove_student_users.sh"
check_executable "$BASE_DIR/scripts/remove_student_users.sh"

check_file "$BASE_DIR/tools/student_manager.py"
check_executable "$BASE_DIR/tools/student_manager.py"

# TECHNICAL REQUIREMENTS - Files
echo ""
echo "=== TECHNICAL REQUIREMENTS - Scripts ==="

check_content "$BASE_DIR/scripts/create_student_users.sh" "useradd"
check_content "$BASE_DIR/scripts/create_student_users.sh" "setquota"
check_content "$BASE_DIR/scripts/create_student_users.sh" "docker"

check_content "$BASE_DIR/scripts/setup_ssh.sh" "ssh-keygen"
check_content "$BASE_DIR/scripts/setup_ssh.sh" "ssh-copy-id"

check_content "$BASE_DIR/scripts/setup_tailscale.sh" "tailscale"

# TECHNICAL REQUIREMENTS - Security
echo ""
echo "=== TECHNICAL REQUIREMENTS - Security ==="

if [ -f "/etc/ssh/sshd_config" ]; then
    check_content "/etc/ssh/sshd_config" "PubkeyAuthentication yes" || true
    run_test "Root SSH login disabled" "grep -q '^PermitRootLogin no' /etc/ssh/sshd_config || grep -q '^PermitRootLogin prohibit-password' /etc/ssh/sshd_config" true
else
    log_warn "SSH config not found (testing on non-configured system)"
    ((TESTS_SKIPPED++))
fi

run_test "Firewall status" "command -v ufw && ufw status | grep -q active" true
run_test "Fail2ban status" "systemctl is-active fail2ban" true

# FUNCTIONAL TESTS
echo ""
echo "=== FUNCTIONAL TESTS ==="

# Docker test
run_test "Docker command available" "command -v docker" false

# GPU test
run_test "nvidia-smi available" "command -v nvidia-smi" true

# Quota test
run_test "Quota command available" "command -v quota" true

# Network tools
run_test "SSH client available" "command -v ssh" false
run_test "Ping available" "command -v ping" false

# Python tools
run_test "Python 3 available" "command -v python3" false

# DOCUMENTATION
echo ""
echo "=== DOCUMENTATION ==="

check_file "$BASE_DIR/README.md"
check_file "$BASE_DIR/docs/STUDENT_MANAGEMENT.md"
check_file "$BASE_DIR/docs/NETWORK_SETUP.md" true
check_file "$BASE_DIR/docs/TROUBLESHOOTING.md" true

# CONFIGURATION
echo ""
echo "=== CONFIGURATION ==="

check_file "$BASE_DIR/config/cluster.yaml.example"
check_file "$BASE_DIR/config/inventory.ini.example"
check_file "$BASE_DIR/config/students.conf"

# PLAYBOOKS
echo ""
echo "=== ANSIBLE PLAYBOOKS ==="

check_file "$BASE_DIR/playbooks/connect-to-your-spark.yaml"
check_file "$BASE_DIR/playbooks/connect-two-sparks.yaml"
check_file "$BASE_DIR/playbooks/tailscale.yaml"
check_file "$BASE_DIR/playbooks/nccl.yaml"
check_file "$BASE_DIR/playbooks/manage-student-users.yaml"

# TOOLS
echo ""
echo "=== TOOLS ==="

check_file "$BASE_DIR/tools/network_validator.py"
check_executable "$BASE_DIR/tools/network_validator.py"

check_file "$BASE_DIR/tools/cluster_orchestrator.py"
check_executable "$BASE_DIR/tools/cluster_orchestrator.py"

check_file "$BASE_DIR/tools/student_manager.py"
check_executable "$BASE_DIR/tools/student_manager.py"

# INTERFACE
echo ""
echo "=== INTERFACE ==="

check_file "$BASE_DIR/agent1_output.py"
check_executable "$BASE_DIR/agent1_output.py"

run_test "agent1_output.py runs" "cd $BASE_DIR && python3 agent1_output.py config" false

# INTEGRATION POINTS
echo ""
echo "=== INTEGRATION POINTS ==="

run_test "Can export cluster config" "cd $BASE_DIR && python3 agent1_output.py config" false
run_test "Can export SSH config" "cd $BASE_DIR && python3 agent1_output.py ssh" false
run_test "Can export network config" "cd $BASE_DIR && python3 agent1_output.py network" false
run_test "Can export student info" "cd $BASE_DIR && python3 agent1_output.py students" false

# RESULTS
echo ""
echo "======================================"
echo "VALIDATION RESULTS"
echo "======================================"
echo "Total Tests:  $TESTS_TOTAL"
echo -e "${GREEN}Passed:       $TESTS_PASSED${NC}"
echo -e "${RED}Failed:       $TESTS_FAILED${NC}"
echo -e "${YELLOW}Skipped:      $TESTS_SKIPPED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All required tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Review errors above.${NC}"
    exit 1
fi
