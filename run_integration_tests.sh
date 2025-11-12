#!/bin/bash

################################################################################
# Integration Test Runner
# Runs comprehensive integration tests for all SparkTest agents
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║            SparkTest Integration Test Suite                 ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_services() {
    log_info "Checking if services are running..."

    if ! docker-compose ps | grep -q "Up"; then
        log_error "Services are not running. Please run ./agent10_deploy.sh first"
        exit 1
    fi

    log_success "Services are running"
}

run_smoke_tests() {
    log_info "Running smoke tests..."
    echo ""

    docker-compose exec -T test-runner pytest -v -m smoke \
        --tb=short \
        --color=yes \
        || return 1

    log_success "Smoke tests passed"
}

run_integration_tests() {
    log_info "Running integration tests..."
    echo ""

    docker-compose exec -T test-runner pytest -v -m integration \
        --tb=short \
        --color=yes \
        --junit-xml=/reports/integration-tests.xml \
        --html=/reports/integration-tests.html \
        --self-contained-html \
        || return 1

    log_success "Integration tests passed"
}

run_agent_tests() {
    local agent=$1
    log_info "Running Agent $agent tests..."
    echo ""

    docker-compose exec -T test-runner pytest -v -m "agent${agent}" \
        --tb=short \
        --color=yes \
        || return 1

    log_success "Agent $agent tests passed"
}

run_all_agent_tests() {
    log_info "Running tests for all agents..."
    echo ""

    local failed_agents=()

    for i in {1..10}; do
        if docker-compose exec -T test-runner pytest -v -m "agent${i}" \
            --tb=short \
            --color=yes 2>/dev/null; then
            log_success "✓ Agent $i tests passed"
        else
            log_error "✗ Agent $i tests failed"
            failed_agents+=($i)
        fi
    done

    if [ ${#failed_agents[@]} -eq 0 ]; then
        log_success "All agent tests passed"
        return 0
    else
        log_error "Failed agents: ${failed_agents[*]}"
        return 1
    fi
}

run_coverage_report() {
    log_info "Generating coverage report..."
    echo ""

    docker-compose exec -T test-runner pytest \
        --cov=/app \
        --cov-report=html:/reports/coverage \
        --cov-report=term \
        tests/

    log_success "Coverage report generated at reports/coverage/index.html"
}

show_test_summary() {
    echo ""
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                   Test Summary                               ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    if [ -f "reports/integration-tests.xml" ]; then
        log_info "Test reports available:"
        echo "  - JUnit XML: reports/integration-tests.xml"
        echo "  - HTML Report: reports/integration-tests.html"
    fi

    echo ""
}

################################################################################
# Main Test Flow
################################################################################

main() {
    print_banner

    check_services

    local test_mode="${1:-all}"

    case "$test_mode" in
        smoke)
            run_smoke_tests
            ;;
        integration)
            run_integration_tests
            ;;
        agent)
            if [ -z "$2" ]; then
                log_error "Please specify agent number: ./run_integration_tests.sh agent <number>"
                exit 1
            fi
            run_agent_tests "$2"
            ;;
        agents)
            run_all_agent_tests
            ;;
        coverage)
            run_coverage_report
            ;;
        all)
            log_info "Running complete test suite..."
            echo ""

            run_smoke_tests || { log_error "Smoke tests failed"; exit 1; }
            echo ""

            run_integration_tests || { log_error "Integration tests failed"; exit 1; }
            echo ""

            run_all_agent_tests || log_error "Some agent tests failed"
            echo ""
            ;;
        *)
            echo "Usage: $0 [MODE] [OPTIONS]"
            echo ""
            echo "Modes:"
            echo "  all           Run all tests (default)"
            echo "  smoke         Run smoke tests only"
            echo "  integration   Run integration tests"
            echo "  agent <N>     Run tests for specific agent (1-10)"
            echo "  agents        Run tests for all agents"
            echo "  coverage      Generate coverage report"
            echo ""
            echo "Examples:"
            echo "  $0                    # Run all tests"
            echo "  $0 smoke              # Run smoke tests"
            echo "  $0 agent 1            # Run Agent 1 tests"
            echo "  $0 coverage           # Generate coverage report"
            echo ""
            exit 1
            ;;
    esac

    show_test_summary

    log_success "Test execution completed! 🎉"
}

main "$@"
