# SparkTest Operations Guide

## Overview

This document provides comprehensive operational procedures for managing and maintaining the SparkTest platform in production.

## Table of Contents

- [Daily Operations](#daily-operations)
- [Monitoring](#monitoring)
- [Maintenance](#maintenance)
- [Backup and Restore](#backup-and-restore)
- [Scaling](#scaling)
- [Performance Tuning](#performance-tuning)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Incident Response](#incident-response)

## Daily Operations

### Morning Checklist

```bash
# 1. Check system health
./scripts/health_check.sh

# 2. Review overnight logs
docker-compose logs --since=12h | grep -i "error\|warning"

# 3. Check disk space
df -h

# 4. Review metrics
curl http://localhost:8000/metrics

# 5. Check job queue
curl http://localhost:8000/jobs | jq '.[] | select(.status=="pending")'
```

### Service Management

#### Starting Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api-gateway

# Start with logs
docker-compose up api-gateway
```

#### Stopping Services

```bash
# Stop all services
docker-compose stop

# Stop specific service
docker-compose stop spark-worker-1

# Stop and remove containers
docker-compose down
```

#### Restarting Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart api-gateway

# Restart with rebuild
docker-compose up -d --build api-gateway
```

### Log Management

#### Viewing Logs

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs -f api-gateway

# View last N lines
docker-compose logs --tail=100 spark-master

# Filter by time
docker-compose logs --since=1h
docker-compose logs --since=2025-01-12T10:00:00
```

#### Log Rotation

```bash
# Truncate logs
docker-compose logs --no-log-prefix > /dev/null

# Archive logs
docker-compose logs > logs/archive_$(date +%Y%m%d).log

# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete
```

### Job Management

#### Submitting Jobs

```bash
# Submit via API
curl -X POST http://localhost:8000/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "daily_batch",
    "job_type": "batch_processing",
    "parameters": {"date": "2025-01-12"},
    "priority": 5
  }'
```

#### Monitoring Jobs

```bash
# List all jobs
curl http://localhost:8000/jobs | jq .

# Get job status
curl http://localhost:8000/jobs/{job_id} | jq .

# List pending jobs
curl http://localhost:8000/jobs?status=pending | jq .

# List failed jobs
curl http://localhost:8000/jobs?status=failed | jq .
```

#### Managing Jobs

```bash
# Cancel job
curl -X DELETE http://localhost:8000/jobs/{job_id}

# Retry failed job
# (Resubmit with same parameters)

# Clear job queue
docker-compose exec redis redis-cli LTRIM job_queue 1 0
```

## Monitoring

### Real-Time Monitoring

```bash
# Start interactive monitor
./scripts/monitor.sh

# Monitor with custom interval
MONITOR_INTERVAL=5 ./scripts/monitor.sh

# Monitor and log to file
./scripts/monitor.sh 2>&1 | tee monitor_$(date +%Y%m%d).log
```

### Health Checks

```bash
# Run comprehensive health check
./scripts/health_check.sh

# Automated health check (cron)
*/5 * * * * cd /path/to/SparkTest && ./scripts/health_check.sh >> /var/log/sparktest_health.log 2>&1
```

### Accessing Dashboards

- **Spark Master UI**: http://localhost:8080
  - Monitor job execution
  - View worker status
  - Check resource usage

- **Grafana**: http://localhost:3000
  - View system metrics
  - Monitor performance
  - Configure alerts

- **Prometheus**: http://localhost:9090
  - Query metrics
  - View targets
  - Check alerts

### Key Metrics to Monitor

#### System Metrics
- CPU usage per container
- Memory usage per container
- Disk I/O
- Network traffic

#### Application Metrics
- Job submission rate
- Job success/failure rate
- Average job duration
- API response time
- Queue depth

#### Infrastructure Metrics
- Database connections
- Cache hit rate
- Spark worker status
- Container health

### Setting Up Alerts

#### Grafana Alerts

1. Access Grafana: http://localhost:3000
2. Navigate to Alerting → Alert rules
3. Create new alert rule:

```
Alert: High Error Rate
Condition: rate(sparktest_jobs_failed_total[5m]) > 0.1
For: 5m
Annotations:
  description: Job failure rate is above threshold
  summary: High job failure rate detected
```

#### Email Notifications

Configure in Grafana:
1. Go to Alerting → Contact points
2. Add email contact point
3. Test notification
4. Link to alert rules

## Maintenance

### Regular Maintenance Tasks

#### Daily
- Check system health
- Review error logs
- Monitor disk space
- Verify backups

#### Weekly
- Review performance metrics
- Clean up old logs
- Update documentation
- Test disaster recovery

#### Monthly
- Update dependencies
- Review security
- Capacity planning
- Performance tuning

### Database Maintenance

```bash
# Vacuum database
docker-compose exec postgres psql -U sparktest -d sparktest_db -c "VACUUM ANALYZE;"

# Check database size
docker-compose exec postgres psql -U sparktest -d sparktest_db -c "
  SELECT pg_size_pretty(pg_database_size('sparktest_db'));"

# Check table sizes
docker-compose exec postgres psql -U sparktest -d sparktest_db -c "
  SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename))
  FROM pg_tables WHERE schemaname = 'public'
  ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"

# Clean old job records
docker-compose exec postgres psql -U sparktest -d sparktest_db -c "
  DELETE FROM jobs WHERE completed_at < NOW() - INTERVAL '30 days';"
```

### Redis Maintenance

```bash
# Check memory usage
docker-compose exec redis redis-cli INFO memory

# Check key count
docker-compose exec redis redis-cli DBSIZE

# Clean expired keys
docker-compose exec redis redis-cli FLUSHDB

# Save data
docker-compose exec redis redis-cli SAVE
```

### Spark Maintenance

```bash
# Check Spark applications
curl http://localhost:8080/json/ | jq '.activeapps'

# Clean Spark work directory
docker-compose exec spark-master rm -rf /tmp/spark-*

# Check Spark logs
docker-compose logs spark-master | tail -100
```

## Backup and Restore

### Creating Backups

```bash
# Create full backup
./scripts/backup.sh

# Backup will be created in: backups/sparktest_backup_TIMESTAMP.tar.gz
```

### Automated Backups

Set up cron job:

```bash
# Edit crontab
crontab -e

# Add backup job (daily at 2 AM)
0 2 * * * cd /path/to/SparkTest && ./scripts/backup.sh >> /var/log/sparktest_backup.log 2>&1
```

### Restoring from Backup

```bash
# List available backups
ls -lh backups/

# Restore from specific backup
./scripts/restore.sh backups/sparktest_backup_20250112_020000.tar.gz

# Restore from latest backup
./scripts/restore.sh backups/latest.tar.gz
```

### Backup Verification

```bash
# Verify backup exists
test -f backups/latest.tar.gz && echo "Backup exists" || echo "Backup missing"

# Check backup size
ls -lh backups/latest.tar.gz

# Test restore (in test environment)
./scripts/restore.sh backups/latest.tar.gz --test
```

## Scaling

### Horizontal Scaling

#### Adding Spark Workers

Edit `docker-compose.yml`:

```yaml
spark-worker-3:
  image: bitnami/spark:3.5.0
  container_name: sparktest-worker-3
  environment:
    - SPARK_MODE=worker
    - SPARK_MASTER_URL=spark://spark-master:7077
    - SPARK_WORKER_MEMORY=2G
    - SPARK_WORKER_CORES=2
  depends_on:
    - spark-master
  networks:
    - sparktest-network
```

Then restart:

```bash
docker-compose up -d spark-worker-3
```

#### Scaling API Gateway

```bash
# Scale to 3 instances
docker-compose up -d --scale api-gateway=3

# With load balancer (nginx)
# Add load balancer configuration
```

### Vertical Scaling

Adjust resource limits in `docker-compose.yml`:

```yaml
spark-worker-1:
  environment:
    - SPARK_WORKER_MEMORY=4G
    - SPARK_WORKER_CORES=4
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 8G
```

### Auto-Scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: sparktest-api
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sparktest-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Performance Tuning

### Spark Optimization

```bash
# Tune shuffle partitions
SPARK_SQL_SHUFFLE_PARTITIONS=200

# Enable broadcast joins
SPARK_SQL_AUTOBR OADCASTJOIN_THRESHOLD=10485760

# Adjust executor memory
SPARK_EXECUTOR_MEMORY=4G
```

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_jobs_created_at ON jobs(created_at);
CREATE INDEX idx_jobs_status ON jobs(status);

-- Analyze tables
ANALYZE jobs;
ANALYZE metrics;

-- Tune configuration
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

### Redis Optimization

```bash
# Set memory limit
docker-compose exec redis redis-cli CONFIG SET maxmemory 512mb
docker-compose exec redis redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### API Optimization

```python
# Enable response caching
# Increase worker processes
# Use connection pooling
# Enable compression
```

## Security

### Access Control

```bash
# Change default passwords
docker-compose exec grafana grafana-cli admin reset-admin-password NewPassword

# Update database password
docker-compose exec postgres psql -U sparktest -c "ALTER USER sparktest WITH PASSWORD 'newpassword';"

# Set Redis password
docker-compose exec redis redis-cli CONFIG SET requirepass "strongpassword"
```

### Network Security

```bash
# Use internal networks only
# Enable SSL/TLS
# Configure firewall rules
# Use VPN for remote access
```

### Container Security

```bash
# Scan for vulnerabilities
trivy image sparktest-api:latest

# Update base images regularly
docker-compose pull
docker-compose up -d --build
```

## Troubleshooting

### Common Issues

See [DEPLOYMENT.md](DEPLOYMENT.md) Troubleshooting section for detailed solutions.

### Performance Issues

```bash
# Check resource usage
docker stats

# Identify slow queries
docker-compose exec postgres psql -U sparktest -d sparktest_db -c "
  SELECT query, calls, mean_exec_time
  FROM pg_stat_statements
  ORDER BY mean_exec_time DESC
  LIMIT 10;"

# Check Spark application performance
curl http://localhost:8080/json/
```

### Debugging

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Access container shell
docker-compose exec api-gateway bash

# Check network connectivity
docker-compose exec api-gateway ping spark-master

# Verify DNS resolution
docker-compose exec api-gateway nslookup postgres
```

## Incident Response

### Incident Classification

- **P1 (Critical)**: Complete service outage
- **P2 (High)**: Major functionality impaired
- **P3 (Medium)**: Minor functionality impaired
- **P4 (Low)**: Cosmetic issues

### Incident Response Steps

1. **Detect**: Monitoring alerts, user reports
2. **Assess**: Determine severity and impact
3. **Respond**: Immediate mitigation
4. **Resolve**: Fix root cause
5. **Document**: Post-mortem

### Emergency Procedures

#### System Down

```bash
# Check all services
docker-compose ps

# Restart all services
docker-compose restart

# If restart fails, restore from backup
./scripts/rollback.sh --auto
```

#### Data Corruption

```bash
# Stop services
docker-compose down

# Restore from latest backup
./scripts/restore.sh backups/latest.tar.gz

# Verify data integrity
./scripts/health_check.sh
```

#### Security Breach

1. Isolate affected systems
2. Change all credentials
3. Review audit logs
4. Apply security patches
5. Document incident

### On-Call Procedures

**On-Call Engineer Responsibilities:**
- Respond to alerts within 15 minutes
- Assess and escalate as needed
- Follow runbooks for common issues
- Document all actions taken
- Hand off to next on-call

**Escalation Path:**
1. On-call engineer
2. Team lead
3. Engineering manager
4. CTO

## Best Practices

1. **Always backup before changes**
2. **Test in staging first**
3. **Document all changes**
4. **Monitor after deployments**
5. **Follow security guidelines**
6. **Keep systems updated**
7. **Regular health checks**
8. **Maintain runbooks**

## Useful Commands

```bash
# Quick health check
curl http://localhost:8000/health

# View resource usage
docker stats --no-stream

# Check logs for errors
docker-compose logs | grep -i error

# Restart unhealthy service
docker-compose restart <service>

# Create backup
./scripts/backup.sh

# Run tests
./run_integration_tests.sh smoke

# Monitor system
./scripts/monitor.sh
```

## Resources

- [Deployment Guide](DEPLOYMENT.md)
- [Disaster Recovery](DISASTER_RECOVERY.md)
- [Architecture Documentation](../../ARCHITECTURE.md)
- [API Documentation](http://localhost:8000/docs)

---

**Document Version**: 1.0
**Last Updated**: 2025-01-12
**Maintained By**: Agent 10 Team
