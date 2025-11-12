#!/bin/bash

################################################################################
# SparkTest Health Check Script
# Comprehensive health check for all system components
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
TIMEOUT=5
OVERALL_STATUS=0

################################################################################
# Helper Functions
################################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

log_error() {
    echo -e "${RED}[✗]${NC} $1"
    OVERALL_STATUS=1
}

print_banner() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║            SparkTest Health Check System                    ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo "Checking system health at $(date)"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

check_docker() {
    print_section "Docker Status"

    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        return 1
    fi
    log_success "Docker is installed"

    if ! docker ps &> /dev/null; then
        log_error "Docker daemon is not running"
        return 1
    fi
    log_success "Docker daemon is running"

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        return 1
    fi
    log_success "Docker Compose is installed"
}

check_containers() {
    print_section "Container Status"

    local containers=(
        "sparktest-master:Spark Master"
        "sparktest-worker-1:Spark Worker 1"
        "sparktest-worker-2:Spark Worker 2"
        "sparktest-postgres:PostgreSQL"
        "sparktest-redis:Redis"
        "sparktest-api:API Gateway"
        "sparktest-prometheus:Prometheus"
        "sparktest-grafana:Grafana"
    )

    for container_info in "${containers[@]}"; do
        IFS=':' read -r container_name display_name <<< "$container_info"

        if docker ps | grep -q "$container_name"; then
            local status=$(docker inspect --format='{{.State.Status}}' "$container_name" 2>/dev/null)
            if [ "$status" == "running" ]; then
                log_success "$display_name is running"
            else
                log_warning "$display_name is $status"
            fi
        else
            log_error "$display_name is not running"
        fi
    done
}

check_api_gateway() {
    print_section "API Gateway Health"

    # Check API is reachable
    if curl -sf http://localhost:8000/health > /dev/null; then
        log_success "API Gateway is reachable"

        # Check health endpoint
        local health_response=$(curl -s http://localhost:8000/health)
        local status=$(echo "$health_response" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

        if [ "$status" == "healthy" ] || [ "$status" == "degraded" ]; then
            log_success "API Gateway health status: $status"

            # Check individual services
            local redis_status=$(echo "$health_response" | grep -o '"redis":"[^"]*"' | cut -d'"' -f4)
            local db_status=$(echo "$health_response" | grep -o '"database":"[^"]*"' | cut -d'"' -f4)
            local spark_status=$(echo "$health_response" | grep -o '"spark":"[^"]*"' | cut -d'"' -f4)

            [ "$redis_status" == "healthy" ] && log_success "  Redis: $redis_status" || log_warning "  Redis: $redis_status"
            [ "$db_status" == "healthy" ] && log_success "  Database: $db_status" || log_warning "  Database: $db_status"
            [ "$spark_status" == "healthy" ] && log_success "  Spark: $spark_status" || log_warning "  Spark: $spark_status"
        else
            log_error "API Gateway health status: $status"
        fi
    else
        log_error "API Gateway is not reachable"
    fi

    # Check API endpoints
    if curl -sf http://localhost:8000/ > /dev/null; then
        log_success "Root endpoint is accessible"
    else
        log_warning "Root endpoint is not accessible"
    fi

    if curl -sf http://localhost:8000/agents > /dev/null; then
        log_success "Agents endpoint is accessible"
    else
        log_warning "Agents endpoint is not accessible"
    fi
}

check_spark_cluster() {
    print_section "Spark Cluster Health"

    # Check Spark Master UI
    if curl -sf http://localhost:8080 > /dev/null; then
        log_success "Spark Master UI is accessible"

        # Check worker count
        local worker_count=$(curl -s http://localhost:8080 | grep -o "Workers ([0-9]*)" | grep -o "[0-9]*" || echo "0")
        if [ "$worker_count" -ge 2 ]; then
            log_success "Spark workers: $worker_count (healthy)"
        else
            log_warning "Spark workers: $worker_count (expected 2+)"
        fi
    else
        log_error "Spark Master UI is not accessible"
    fi
}

check_database() {
    print_section "Database Health"

    # Check PostgreSQL
    if docker-compose exec -T postgres pg_isready -U sparktest > /dev/null 2>&1; then
        log_success "PostgreSQL is ready"

        # Check database exists
        if docker-compose exec -T postgres psql -U sparktest -d sparktest_db -c "SELECT 1" > /dev/null 2>&1; then
            log_success "Database 'sparktest_db' is accessible"

            # Check table count
            local table_count=$(docker-compose exec -T postgres psql -U sparktest -d sparktest_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'" | tr -d ' ')
            log_success "Database has $table_count tables"
        else
            log_error "Database 'sparktest_db' is not accessible"
        fi
    else
        log_error "PostgreSQL is not ready"
    fi
}

check_redis() {
    print_section "Redis Health"

    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_success "Redis is responding to PING"

        # Check memory usage
        local used_memory=$(docker-compose exec -T redis redis-cli INFO memory | grep "used_memory_human" | cut -d':' -f2 | tr -d '\r')
        log_success "Redis memory usage: $used_memory"

        # Check key count
        local key_count=$(docker-compose exec -T redis redis-cli DBSIZE | cut -d':' -f2 | tr -d '\r')
        log_success "Redis has $key_count keys"
    else
        log_error "Redis is not responding"
    fi
}

check_monitoring() {
    print_section "Monitoring Stack Health"

    # Check Prometheus
    if curl -sf http://localhost:9090/-/healthy > /dev/null; then
        log_success "Prometheus is healthy"

        # Check targets
        local targets=$(curl -s http://localhost:9090/api/v1/targets | grep -o '"health":"[^"]*"' | wc -l)
        log_success "Prometheus has $targets targets configured"
    else
        log_error "Prometheus is not healthy"
    fi

    # Check Grafana
    if curl -sf http://localhost:3000/api/health > /dev/null; then
        log_success "Grafana is healthy"
    else
        log_error "Grafana is not healthy"
    fi
}

check_disk_space() {
    print_section "Disk Space"

    local usage=$(df -h . | awk 'NR==2 {print $5}' | tr -d '%')
    local available=$(df -h . | awk 'NR==2 {print $4}')

    if [ "$usage" -lt 80 ]; then
        log_success "Disk usage: ${usage}% (${available} available)"
    elif [ "$usage" -lt 90 ]; then
        log_warning "Disk usage: ${usage}% (${available} available)"
    else
        log_error "Disk usage: ${usage}% (${available} available) - Critical!"
    fi

    # Check Docker disk usage
    local docker_usage=$(docker system df -v 2>/dev/null | grep "Total" | awk '{print $4}' || echo "N/A")
    log_info "Docker disk usage: $docker_usage"
}

check_memory() {
    print_section "Memory Usage"

    if command -v free &> /dev/null; then
        local mem_usage=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
        local mem_available=$(free -h | awk 'NR==2 {print $7}')

        if [ "$mem_usage" -lt 80 ]; then
            log_success "Memory usage: ${mem_usage}% (${mem_available} available)"
        elif [ "$mem_usage" -lt 90 ]; then
            log_warning "Memory usage: ${mem_usage}% (${mem_available} available)"
        else
            log_error "Memory usage: ${mem_usage}% (${mem_available} available) - Critical!"
        fi
    else
        log_info "Memory check skipped (free command not available)"
    fi
}

check_network() {
    print_section "Network Connectivity"

    # Check Docker network
    if docker network inspect sparktest_sparktest-network > /dev/null 2>&1; then
        log_success "Docker network exists"
    else
        log_error "Docker network not found"
    fi

    # Check port accessibility
    local ports=(8000 8080 5432 6379 3000 9090)
    for port in "${ports[@]}"; do
        if nc -z localhost "$port" 2>/dev/null || curl -sf "http://localhost:$port" > /dev/null 2>&1; then
            log_success "Port $port is accessible"
        else
            log_warning "Port $port is not accessible"
        fi
    done
}

check_logs_for_errors() {
    print_section "Recent Errors in Logs"

    local error_count=$(docker-compose logs --tail=100 2>&1 | grep -i "error\|exception\|fatal" | wc -l)

    if [ "$error_count" -eq 0 ]; then
        log_success "No recent errors in logs"
    elif [ "$error_count" -lt 5 ]; then
        log_warning "$error_count errors found in recent logs"
    else
        log_error "$error_count errors found in recent logs"
    fi
}

print_summary() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}Health Check Summary${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""

    if [ $OVERALL_STATUS -eq 0 ]; then
        log_success "All systems operational ✅"
        echo ""
        echo "System is healthy and ready for use."
    else
        log_error "Some systems are not healthy ⚠️"
        echo ""
        echo "Please review the errors above and take corrective action."
        echo "Check logs with: docker-compose logs -f"
    fi

    echo ""
    echo "Health check completed at $(date)"
    echo ""
}

################################################################################
# Main Health Check Flow
################################################################################

main() {
    print_banner

    check_docker
    check_containers
    check_api_gateway
    check_spark_cluster
    check_database
    check_redis
    check_monitoring
    check_disk_space
    check_memory
    check_network
    check_logs_for_errors

    print_summary

    exit $OVERALL_STATUS
}

# Handle arguments
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Perform comprehensive health check of SparkTest system"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo "  --json         Output results in JSON format"
    echo ""
    echo "Exit Codes:"
    echo "  0 - All systems healthy"
    echo "  1 - Some systems unhealthy"
    echo ""
    exit 0
fi

main

exit $OVERALL_STATUS
