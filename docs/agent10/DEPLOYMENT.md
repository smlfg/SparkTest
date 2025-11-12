# SparkTest Deployment Guide

## Overview

This document provides comprehensive deployment instructions for the SparkTest multi-agent distributed computing platform.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [One-Command Deployment](#one-command-deployment)
- [Manual Deployment](#manual-deployment)
- [Configuration](#configuration)
- [Deployment Verification](#deployment-verification)
- [Deployment Modes](#deployment-modes)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 4 cores
- RAM: 8GB
- Disk: 20GB free space
- OS: Linux, macOS, or Windows (with WSL2)

**Recommended Requirements:**
- CPU: 8+ cores
- RAM: 16GB
- Disk: 50GB free space
- OS: Linux (Ubuntu 20.04+ or similar)

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- Git
- curl
- bash

### Port Requirements

The following ports must be available:

| Port | Service | Description |
|------|---------|-------------|
| 8000 | API Gateway | REST API |
| 8080 | Spark Master | Spark Web UI |
| 7077 | Spark Master | Spark RPC |
| 5432 | PostgreSQL | Database |
| 6379 | Redis | Cache/Queue |
| 3000 | Grafana | Monitoring UI |
| 9090 | Prometheus | Metrics |

## Pre-Deployment Checklist

Run the pre-flight checks before deployment:

```bash
# Check system resources
df -h .                    # Disk space
free -h                    # RAM
docker info                # Docker status

# Check ports
for port in 8000 8080 5432 6379 3000 9090; do
    nc -z localhost $port && echo "Port $port is in use"
done

# Check Docker
docker ps                  # Docker is running
docker-compose --version   # Compose is installed
```

## One-Command Deployment

The simplest way to deploy SparkTest:

```bash
# Clone repository
git clone https://github.com/yourusername/SparkTest.git
cd SparkTest

# Deploy
./agent10_deploy.sh
```

This script will:
1. ✅ Check dependencies
2. ✅ Run pre-flight checks (disk, RAM, ports)
3. ✅ Create required directories
4. ✅ Set up monitoring configurations
5. ✅ Initialize database
6. ✅ Pull Docker images
7. ✅ Build custom images
8. ✅ Start services in correct order
9. ✅ Wait for health checks
10. ✅ Run smoke tests
11. ✅ Display access URLs

**Expected deployment time: < 5 minutes**

## Manual Deployment

For more control over the deployment process:

### Step 1: Prepare Environment

```bash
# Clone repository
git clone https://github.com/yourusername/SparkTest.git
cd SparkTest

# Create environment file
cat > .env <<EOF
# Spark Configuration
SPARK_MASTER_URL=spark://spark-master:7077
SPARK_WORKER_MEMORY=2G
SPARK_WORKER_CORES=2

# Database Configuration
POSTGRES_USER=sparktest
POSTGRES_PASSWORD=sparktest123
POSTGRES_DB=sparktest_db

# Redis Configuration
REDIS_URL=redis://redis:6379

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin123
EOF

# Create required directories
mkdir -p spark/{jobs,data,logs}
mkdir -p database/init
mkdir -p reports
mkdir -p monitoring/grafana/{dashboards,provisioning}
```

### Step 2: Configure Services

```bash
# Set up monitoring
./scripts/setup_monitoring.sh

# Set up database initialization
./scripts/setup_database.sh
```

### Step 3: Deploy Infrastructure

```bash
# Start infrastructure services first
docker-compose up -d postgres redis

# Wait for infrastructure
sleep 10

# Verify
docker-compose exec postgres pg_isready -U sparktest
docker-compose exec redis redis-cli ping
```

### Step 4: Deploy Spark Cluster

```bash
# Start Spark cluster
docker-compose up -d spark-master spark-worker-1 spark-worker-2

# Wait for cluster
sleep 15

# Verify
curl http://localhost:8080
```

### Step 5: Deploy Application Services

```bash
# Start application and monitoring
docker-compose up -d api-gateway prometheus grafana test-runner

# Wait for services
sleep 10

# Verify
curl http://localhost:8000/health
```

### Step 6: Verify Deployment

```bash
# Check all services
docker-compose ps

# Run health check
./scripts/health_check.sh

# Run smoke tests
./run_integration_tests.sh smoke
```

## Configuration

### Environment Variables

Create a `.env` file to customize configuration:

```bash
# Spark Configuration
SPARK_MASTER_URL=spark://spark-master:7077
SPARK_WORKER_MEMORY=4G           # Adjust based on available RAM
SPARK_WORKER_CORES=4              # Adjust based on available CPU
SPARK_WORKER_INSTANCES=2          # Number of worker nodes

# Database Configuration
POSTGRES_USER=sparktest
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=sparktest_db
DATABASE_URL=postgresql://sparktest:password@postgres:5432/sparktest_db

# Redis Configuration
REDIS_URL=redis://redis:6379
REDIS_PASSWORD=your_redis_password    # Optional

# API Configuration
API_PORT=8000
API_WORKERS=4

# Monitoring
PROMETHEUS_RETENTION_TIME=15d
GRAFANA_ADMIN_PASSWORD=your_secure_password
```

### Resource Limits

Edit `docker-compose.yml` to adjust resource limits:

```yaml
services:
  spark-worker-1:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Network Configuration

For production deployments, configure external networks:

```yaml
networks:
  sparktest-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

## Deployment Verification

### Health Checks

```bash
# Comprehensive health check
./scripts/health_check.sh

# Expected output: "All systems operational ✅"
```

### Service Verification

```bash
# Check all containers are running
docker-compose ps

# Check service health individually
curl http://localhost:8000/health          # API Gateway
curl http://localhost:8080                 # Spark Master
curl http://localhost:3000/api/health      # Grafana
curl http://localhost:9090/-/healthy       # Prometheus
```

### Functional Testing

```bash
# Run smoke tests (quick validation)
./run_integration_tests.sh smoke

# Run full integration tests
./run_integration_tests.sh

# Run agent-specific tests
./run_integration_tests.sh agent 1
```

### Performance Validation

```bash
# Run performance benchmarks
./benchmark_suite.sh

# Monitor system in real-time
./scripts/monitor.sh
```

## Deployment Modes

### Development Mode (Default)

```bash
# Deploy with all services
./agent10_deploy.sh

# Features:
# - Auto-reload enabled
# - Debug logging
# - Test runner available
# - All monitoring enabled
```

### Production Mode

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Features:
# - Optimized for performance
# - Reduced logging
# - Resource limits enforced
# - Health checks enabled
```

### Minimal Mode (Testing)

```bash
# Deploy only core services
docker-compose up -d postgres redis spark-master api-gateway

# Use for:
# - Quick testing
# - CI/CD pipelines
# - Resource-constrained environments
```

## Clean Deployment

Remove existing deployment and start fresh:

```bash
# Stop and remove everything
./agent10_deploy.sh --clean

# This will:
# - Stop all containers
# - Remove volumes
# - Clean up networks
# - Perform fresh deployment
```

## Deployment Automation

### CI/CD Integration

GitHub Actions example:

```yaml
name: Deploy SparkTest

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Deploy SparkTest
        run: |
          ./agent10_deploy.sh
          ./run_integration_tests.sh smoke

      - name: Verify deployment
        run: ./scripts/health_check.sh
```

### Kubernetes Deployment (Advanced)

For Kubernetes deployments:

```bash
# Convert docker-compose to Kubernetes manifests
kompose convert

# Apply manifests
kubectl apply -f k8s/

# Verify deployment
kubectl get pods -n sparktest
```

## Troubleshooting

### Common Issues

#### Issue: Ports Already in Use

```bash
# Find and kill processes using required ports
lsof -ti:8000 | xargs kill -9

# Or deploy with different ports
PORT=18000 ./agent10_deploy.sh
```

#### Issue: Insufficient Resources

```bash
# Check resource usage
docker stats

# Reduce worker memory
export SPARK_WORKER_MEMORY=1G
./agent10_deploy.sh
```

#### Issue: Services Won't Start

```bash
# Check logs
docker-compose logs -f

# Restart specific service
docker-compose restart api-gateway

# Full restart
docker-compose down && ./agent10_deploy.sh
```

#### Issue: Database Connection Failed

```bash
# Check PostgreSQL logs
docker-compose logs postgres

# Reset database
docker-compose down -v
./agent10_deploy.sh
```

#### Issue: Spark Workers Not Connecting

```bash
# Check Spark Master logs
docker-compose logs spark-master

# Check worker logs
docker-compose logs spark-worker-1

# Restart cluster
docker-compose restart spark-master spark-worker-1 spark-worker-2
```

### Diagnostic Commands

```bash
# View all logs
docker-compose logs --tail=100

# Check specific service
docker-compose logs -f api-gateway

# Inspect container
docker-compose exec api-gateway env

# Check networks
docker network ls | grep sparktest

# Check volumes
docker volume ls | grep sparktest
```

### Getting Help

1. **Check logs**: `docker-compose logs -f`
2. **Run health check**: `./scripts/health_check.sh`
3. **Consult documentation**: README.md, ARCHITECTURE.md
4. **Search issues**: GitHub Issues
5. **Contact support**: sparktest@example.com

## Post-Deployment Steps

### 1. Change Default Passwords

```bash
# Update Grafana password
docker-compose exec grafana grafana-cli admin reset-admin-password NewPassword

# Update database password
docker-compose exec postgres psql -U sparktest -c "ALTER USER sparktest WITH PASSWORD 'newpassword';"
```

### 2. Set Up Backups

```bash
# Create initial backup
./scripts/backup.sh

# Set up automated backups (cron)
echo "0 2 * * * cd /path/to/SparkTest && ./scripts/backup.sh" | crontab -
```

### 3. Configure Monitoring Alerts

- Access Grafana: http://localhost:3000
- Set up alert channels
- Configure alert rules
- Test notifications

### 4. Document Deployment

```bash
# Record deployment details
echo "Deployed: $(date)" > DEPLOYMENT_INFO.txt
echo "Version: $(git describe --tags)" >> DEPLOYMENT_INFO.txt
echo "Commit: $(git rev-parse HEAD)" >> DEPLOYMENT_INFO.txt
```

## Deployment Checklist

- [ ] System requirements met
- [ ] Prerequisites installed
- [ ] Ports available
- [ ] Configuration customized
- [ ] Deployment successful (< 5 min)
- [ ] All services running
- [ ] Health checks passing
- [ ] Smoke tests passing
- [ ] Monitoring accessible
- [ ] Default passwords changed
- [ ] Backups configured
- [ ] Documentation updated

## Next Steps

After successful deployment:

1. **Run full test suite**: `./run_integration_tests.sh`
2. **Run benchmarks**: `./benchmark_suite.sh`
3. **Set up monitoring**: Configure Grafana dashboards
4. **Review operations guide**: [OPERATIONS.md](OPERATIONS.md)
5. **Set up disaster recovery**: [DISASTER_RECOVERY.md](DISASTER_RECOVERY.md)

---

**Document Version**: 1.0
**Last Updated**: 2025-01-12
**Maintained By**: Agent 10 Team
