#!/bin/bash

################################################################################
# SparkTest Monitoring Script
# Continuous monitoring and alerting for SparkTest system
################################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Configuration
MONITOR_INTERVAL=${MONITOR_INTERVAL:-10}
LOG_FILE="${LOG_FILE:-logs/monitor.log}"

################################################################################
# Helper Functions
################################################################################

log_info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ⚠️  $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} ❌ $1" | tee -a "$LOG_FILE"
}

print_banner() {
    clear
    echo -e "${MAGENTA}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          SparkTest Real-Time Monitoring System              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo "Monitoring interval: ${MONITOR_INTERVAL}s | Press Ctrl+C to stop"
    echo ""
}

monitor_containers() {
    echo -e "${BLUE}━━━ Container Status ━━━${NC}"

    local containers=(
        "sparktest-master"
        "sparktest-worker-1"
        "sparktest-worker-2"
        "sparktest-postgres"
        "sparktest-redis"
        "sparktest-api"
        "sparktest-prometheus"
        "sparktest-grafana"
    )

    local all_healthy=true

    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
            # Get CPU and memory usage
            local stats=$(docker stats --no-stream --format "{{.CPUPerc}}|{{.MemUsage}}" "$container")
            local cpu=$(echo "$stats" | cut -d'|' -f1)
            local mem=$(echo "$stats" | cut -d'|' -f2)

            printf "  ${GREEN}✓${NC} %-25s CPU: %-8s MEM: %s\n" "$container" "$cpu" "$mem"
        else
            printf "  ${RED}✗${NC} %-25s ${RED}NOT RUNNING${NC}\n" "$container"
            all_healthy=false
            log_error "Container $container is not running"
        fi
    done

    echo ""
    return $([ "$all_healthy" = true ] && echo 0 || echo 1)
}

monitor_api_health() {
    echo -e "${BLUE}━━━ API Gateway Health ━━━${NC}"

    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        local health=$(curl -s http://localhost:8000/health)
        local status=$(echo "$health" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

        if [ "$status" == "healthy" ]; then
            echo -e "  ${GREEN}✓${NC} API Status: ${GREEN}HEALTHY${NC}"
        else
            echo -e "  ${YELLOW}⚠${NC} API Status: ${YELLOW}DEGRADED${NC}"
            log_warning "API Gateway is degraded"
        fi

        # Response time
        local response_time=$(curl -o /dev/null -s -w '%{time_total}' http://localhost:8000/health)
        echo -e "  ${BLUE}⏱${NC}  Response Time: ${response_time}s"

        if (( $(echo "$response_time > 1.0" | bc -l) )); then
            log_warning "API response time is high: ${response_time}s"
        fi
    else
        echo -e "  ${RED}✗${NC} API Status: ${RED}UNREACHABLE${NC}"
        log_error "API Gateway is unreachable"
    fi

    echo ""
}

monitor_spark_cluster() {
    echo -e "${BLUE}━━━ Spark Cluster ━━━${NC}"

    if curl -sf http://localhost:8080 > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Spark Master UI: ACCESSIBLE"

        # Try to get worker count (simple method)
        local master_page=$(curl -s http://localhost:8080)
        echo -e "  ${BLUE}ℹ${NC}  Master: http://localhost:8080"
    else
        echo -e "  ${RED}✗${NC} Spark Master UI: ${RED}UNREACHABLE${NC}"
        log_error "Spark Master is unreachable"
    fi

    echo ""
}

monitor_database() {
    echo -e "${BLUE}━━━ Database Status ━━━${NC}"

    if docker-compose exec -T postgres pg_isready -U sparktest > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} PostgreSQL: READY"

        # Get connection count
        local conn_count=$(docker-compose exec -T postgres psql -U sparktest -d sparktest_db -t -c "SELECT count(*) FROM pg_stat_activity" 2>/dev/null | tr -d ' ' || echo "N/A")
        echo -e "  ${BLUE}ℹ${NC}  Active Connections: $conn_count"

        # Get database size
        local db_size=$(docker-compose exec -T postgres psql -U sparktest -d sparktest_db -t -c "SELECT pg_size_pretty(pg_database_size('sparktest_db'))" 2>/dev/null | tr -d ' ' || echo "N/A")
        echo -e "  ${BLUE}ℹ${NC}  Database Size: $db_size"
    else
        echo -e "  ${RED}✗${NC} PostgreSQL: ${RED}NOT READY${NC}"
        log_error "PostgreSQL is not ready"
    fi

    echo ""
}

monitor_redis() {
    echo -e "${BLUE}━━━ Redis Status ━━━${NC}"

    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Redis: RESPONDING"

        # Get key count
        local key_count=$(docker-compose exec -T redis redis-cli DBSIZE 2>/dev/null | tr -d '\r' || echo "N/A")
        echo -e "  ${BLUE}ℹ${NC}  Keys: $key_count"

        # Get memory usage
        local mem_used=$(docker-compose exec -T redis redis-cli INFO memory 2>/dev/null | grep "used_memory_human" | cut -d':' -f2 | tr -d '\r' || echo "N/A")
        echo -e "  ${BLUE}ℹ${NC}  Memory: $mem_used"
    else
        echo -e "  ${RED}✗${NC} Redis: ${RED}NOT RESPONDING${NC}"
        log_error "Redis is not responding"
    fi

    echo ""
}

monitor_resources() {
    echo -e "${BLUE}━━━ System Resources ━━━${NC}"

    # Disk usage
    local disk_usage=$(df -h . | awk 'NR==2 {print $5}' | tr -d '%')
    local disk_avail=$(df -h . | awk 'NR==2 {print $4}')

    if [ "$disk_usage" -lt 80 ]; then
        echo -e "  ${GREEN}✓${NC} Disk: ${disk_usage}% used ($disk_avail available)"
    elif [ "$disk_usage" -lt 90 ]; then
        echo -e "  ${YELLOW}⚠${NC} Disk: ${disk_usage}% used ($disk_avail available)"
        log_warning "Disk usage is at ${disk_usage}%"
    else
        echo -e "  ${RED}✗${NC} Disk: ${disk_usage}% used ($disk_avail available) - CRITICAL"
        log_error "Disk usage is critical: ${disk_usage}%"
    fi

    # Memory usage
    if command -v free &> /dev/null; then
        local mem_usage=$(free | awk 'NR==2 {printf "%.0f", $3/$2 * 100}')
        local mem_avail=$(free -h | awk 'NR==2 {print $7}')

        if [ "$mem_usage" -lt 80 ]; then
            echo -e "  ${GREEN}✓${NC} Memory: ${mem_usage}% used ($mem_avail available)"
        elif [ "$mem_usage" -lt 90 ]; then
            echo -e "  ${YELLOW}⚠${NC} Memory: ${mem_usage}% used ($mem_avail available)"
            log_warning "Memory usage is at ${mem_usage}%"
        else
            echo -e "  ${RED}✗${NC} Memory: ${mem_usage}% used ($mem_avail available) - CRITICAL"
            log_error "Memory usage is critical: ${mem_usage}%"
        fi
    fi

    echo ""
}

monitor_metrics() {
    echo -e "${BLUE}━━━ Metrics Overview ━━━${NC}"

    # Get metrics from API
    if curl -sf http://localhost:8000/metrics > /dev/null 2>&1; then
        local metrics=$(curl -s http://localhost:8000/metrics)

        # Job count
        local job_count=$(echo "$metrics" | grep "sparktest_jobs_total" | tail -1 | awk '{print $2}' || echo "0")
        echo -e "  ${BLUE}ℹ${NC}  Total Jobs: $job_count"

        # API requests
        local api_requests=$(echo "$metrics" | grep "sparktest_api_requests_total" | tail -1 | awk '{print $2}' || echo "0")
        echo -e "  ${BLUE}ℹ${NC}  API Requests: $api_requests"
    else
        echo -e "  ${YELLOW}⚠${NC} Metrics endpoint unreachable"
    fi

    echo ""
}

print_footer() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "Next update in ${MONITOR_INTERVAL}s | $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

################################################################################
# Main Monitoring Loop
################################################################################

main() {
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"

    # Initial banner
    print_banner
    log_info "Monitoring started with interval ${MONITOR_INTERVAL}s"

    while true; do
        # Clear and show banner
        print_banner

        # Run all monitoring checks
        monitor_containers
        monitor_api_health
        monitor_spark_cluster
        monitor_database
        monitor_redis
        monitor_resources
        monitor_metrics

        # Footer
        print_footer

        # Wait for next iteration
        sleep "$MONITOR_INTERVAL"
    done
}

# Handle Ctrl+C gracefully
trap 'echo ""; log_info "Monitoring stopped"; exit 0' INT TERM

# Handle arguments
if [ "$1" == "--help" ] || [ "$1" == "-h" ]; then
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Real-time monitoring of SparkTest system"
    echo ""
    echo "Options:"
    echo "  -h, --help     Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  MONITOR_INTERVAL   Seconds between updates (default: 10)"
    echo "  LOG_FILE          Path to log file (default: logs/monitor.log)"
    echo ""
    echo "Examples:"
    echo "  $0                              # Monitor with 10s interval"
    echo "  MONITOR_INTERVAL=5 $0           # Monitor with 5s interval"
    echo "  LOG_FILE=/var/log/monitor.log $0  # Custom log location"
    echo ""
    exit 0
fi

main

exit 0
