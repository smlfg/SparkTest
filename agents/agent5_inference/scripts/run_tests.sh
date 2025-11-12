#!/bin/bash
#
# Agent 5 Inference Engine - Automated Test Runner
# Executes functional tests from TESTING_CHECKLIST.yaml
#
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh --critical   # Run only critical tests
#   ./run_tests.sh --report     # Generate detailed report
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
REPORT_FILE="/tmp/agent5_test_report_$(date +%Y%m%d_%H%M%S).txt"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
}

# Test execution function
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_status="${3:-0}"

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log_info "Running: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    # Execute test command
    if eval "$test_command" > /tmp/test_output.txt 2>&1; then
        if [ "$expected_status" -eq 0 ]; then
            log_success "$test_name"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        else
            log_error "$test_name (Expected failure but succeeded)"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            cat /tmp/test_output.txt
            return 1
        fi
    else
        if [ "$expected_status" -ne 0 ]; then
            log_success "$test_name (Expected failure)"
            PASSED_TESTS=$((PASSED_TESTS + 1))
            return 0
        else
            log_error "$test_name"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            echo "Output:"
            cat /tmp/test_output.txt
            return 1
        fi
    fi
}

# Banner
show_banner() {
    cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║     Agent 5 Inference Engine - Test Suite Runner          ║
║                 Functional Validation                      ║
╚════════════════════════════════════════════════════════════╝
EOF
}

# Prerequisite checks
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found. Please install Docker."
        exit 1
    fi
    log_success "Docker installed"

    # Check curl
    if ! command -v curl &> /dev/null; then
        log_error "curl not found. Please install curl."
        exit 1
    fi
    log_success "curl installed"

    # Check jq (optional but recommended)
    if ! command -v jq &> /dev/null; then
        log_warning "jq not found. JSON validation will be limited."
    else
        log_success "jq installed"
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found"
        exit 1
    fi
    log_success "Python 3 installed"

    echo ""
}

# Test 1: Ollama Health Check
test_ollama_health() {
    run_test "Ollama Service Health" \
        "curl -f -s http://localhost:11434/api/tags" \
        0
}

# Test 2: Open WebUI Access
test_webui_access() {
    run_test "Open WebUI Accessibility" \
        "curl -f -s -I http://localhost:8080 | head -n 1 | grep '200'" \
        0
}

# Test 3: Model API Health
test_api_health() {
    run_test "Model API Health Check" \
        "curl -f -s http://localhost:8888/health | jq -e '.status == \"healthy\"'" \
        0
}

# Test 4: Model Registry
test_model_registry() {
    run_test "Model Registry API" \
        "curl -f -s http://localhost:8888/api/models | jq -e '.ollama'" \
        0
}

# Test 5: Model Registry Endpoint
test_registry_endpoint() {
    run_test "Static Model Registry" \
        "curl -f -s http://localhost:8888/api/models/registry | jq -e '.ollama_models'" \
        0
}

# Test 6: Providers List
test_providers() {
    run_test "Provider Configuration" \
        "curl -f -s http://localhost:8888/api/providers | jq -e '.providers'" \
        0
}

# Test 7: Completion API
test_completion_api() {
    log_info "Testing completion API (may take 10-30s)..."

    run_test "Text Completion API" \
        "timeout 30 curl -f -s -X POST http://localhost:8888/api/completion \
            -H 'Content-Type: application/json' \
            -d '{\"model\":\"llama3.1:8b\",\"prompt\":\"Say hello\",\"max_tokens\":10}' \
            | jq -e '.response'" \
        0
}

# Test 8: Model Comparison API
test_comparison_api() {
    log_info "Testing comparison API (may take 30-60s)..."

    run_test "Model Comparison API" \
        "timeout 60 curl -f -s -X POST http://localhost:8888/api/compare \
            -H 'Content-Type: application/json' \
            -d '{\"prompt\":\"Test\",\"models\":[\"llama3.1:8b\"]}' \
            | jq -e '.results'" \
        0
}

# Test 9: Benchmark Script Validation
test_benchmark_script() {
    run_test "Benchmark Script Help" \
        "python3 ${SCRIPT_DIR}/student_benchmark.py --help" \
        0
}

# Test 10: Import Script Validation
test_import_script() {
    run_test "Import Script Help" \
        "python3 ${SCRIPT_DIR}/import_finetuned.py --help" \
        0
}

# Test 11: Shared Health Check
test_shared_health() {
    run_test "Shared Health Check Module" \
        "python3 ${PROJECT_ROOT}/shared/health_check.py --port 8888" \
        0
}

# Test 12: Docker Health Status
test_docker_health() {
    run_test "Container Health Status" \
        "docker ps --format '{{.Names}}\t{{.Status}}' | grep -E 'ollama|open-webui|agent5-api' | grep -v 'unhealthy'" \
        0
}

# Test 13: API Documentation
test_api_docs() {
    run_test "API Documentation Available" \
        "curl -f -s http://localhost:8888/docs | grep -i 'swagger'" \
        0
}

# Test 14: OpenAPI Schema
test_openapi_schema() {
    run_test "OpenAPI Schema Available" \
        "curl -f -s http://localhost:8888/openapi.json | jq -e '.info.title'" \
        0
}

# Generate test report
generate_report() {
    local report_file="$1"

    cat > "$report_file" << EOF
================================================================================
AGENT 5 INFERENCE ENGINE - TEST REPORT
================================================================================

Date: $(date)
Host: $(hostname)
User: $(whoami)

--------------------------------------------------------------------------------
TEST SUMMARY
--------------------------------------------------------------------------------

Total Tests:    $TOTAL_TESTS
Passed:         $PASSED_TESTS
Failed:         $FAILED_TESTS
Skipped:        $SKIPPED_TESTS

Pass Rate:      $(( PASSED_TESTS * 100 / TOTAL_TESTS ))%

--------------------------------------------------------------------------------
SERVICE STATUS
--------------------------------------------------------------------------------

$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "NAME|ollama|webui|agent5")

--------------------------------------------------------------------------------
SYSTEM INFORMATION
--------------------------------------------------------------------------------

Docker Version: $(docker --version)
Python Version: $(python3 --version)
GPU Status:
$(nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>/dev/null || echo "No GPU found")

--------------------------------------------------------------------------------
ENDPOINT VERIFICATION
--------------------------------------------------------------------------------

Ollama API:      $(curl -s -o /dev/null -w "%{http_code}" http://localhost:11434/api/tags)
Open WebUI:      $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080)
Model API:       $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8888/health)

--------------------------------------------------------------------------------
RECOMMENDATIONS
--------------------------------------------------------------------------------

EOF

    if [ $FAILED_TESTS -gt 0 ]; then
        echo "⚠️  Some tests failed. Please review the output above." >> "$report_file"
        echo "   Check docker logs for services that failed." >> "$report_file"
        echo "   Ensure all prerequisites are met." >> "$report_file"
    else
        echo "✅ All tests passed! Agent 5 is fully functional." >> "$report_file"
    fi

    cat "$report_file"
    echo ""
    log_info "Report saved to: $report_file"
}

# Main test execution
main() {
    local run_critical_only=false
    local generate_report_flag=false

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --critical)
                run_critical_only=true
                shift
                ;;
            --report)
                generate_report_flag=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --critical    Run only critical tests"
                echo "  --report      Generate detailed report"
                echo "  --help        Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    show_banner
    check_prerequisites

    echo ""
    log_info "Starting test execution..."
    echo ""

    # Critical tests
    test_ollama_health
    test_webui_access
    test_api_health
    test_model_registry

    # High priority tests
    if [ "$run_critical_only" = false ]; then
        test_registry_endpoint
        test_providers
        test_completion_api
        test_comparison_api
        test_benchmark_script
        test_import_script
        test_shared_health
        test_docker_health
        test_api_docs
        test_openapi_schema
    fi

    # Summary
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "                    TEST SUMMARY"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    echo "Total Tests:   $TOTAL_TESTS"
    echo -e "Passed:        ${GREEN}$PASSED_TESTS${NC}"
    echo -e "Failed:        ${RED}$FAILED_TESTS${NC}"
    echo -e "Skipped:       ${YELLOW}$SKIPPED_TESTS${NC}"
    echo ""

    if [ $FAILED_TESTS -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        echo ""
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        echo ""
    fi

    # Generate report if requested
    if [ "$generate_report_flag" = true ]; then
        generate_report "$REPORT_FILE"
    fi

    # Exit with appropriate code
    if [ $FAILED_TESTS -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"
