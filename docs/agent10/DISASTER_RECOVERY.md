# SparkTest Disaster Recovery Plan

## Overview

This document outlines the disaster recovery procedures for the SparkTest platform, ensuring business continuity in the event of system failures, data loss, or other catastrophic events.

## Table of Contents

- [Disaster Recovery Objectives](#disaster-recovery-objectives)
- [Backup Strategy](#backup-strategy)
- [Recovery Procedures](#recovery-procedures)
- [Failure Scenarios](#failure-scenarios)
- [Rollback Procedures](#rollback-procedures)
- [Testing and Validation](#testing-and-validation)
- [Emergency Contacts](#emergency-contacts)

## Disaster Recovery Objectives

### Recovery Time Objective (RTO)

**Target RTO: 30 minutes**

| System Component | RTO Target | Priority |
|------------------|------------|----------|
| Database | 15 minutes | Critical |
| API Gateway | 10 minutes | Critical |
| Spark Cluster | 20 minutes | High |
| Monitoring | 30 minutes | Medium |

### Recovery Point Objective (RPO)

**Target RPO: 24 hours**

- Database: < 24 hours (daily backups)
- Configuration: < 1 hour (version controlled)
- Logs: < 24 hours (daily archives)
- Metrics: < 15 minutes (Prometheus retention)

### Service Level Agreement (SLA)

- **Availability Target**: 99.5% uptime
- **Maximum Downtime**: 3.6 hours/month
- **Planned Maintenance**: 4 hours/month

## Backup Strategy

### Backup Types

#### 1. Full System Backup

**Frequency**: Daily at 2:00 AM
**Retention**: 7 days
**Location**: `backups/` directory

```bash
# Automated daily backup
0 2 * * * cd /path/to/SparkTest && ./scripts/backup.sh
```

**Includes**:
- PostgreSQL database dump
- Redis RDB snapshot
- Configuration files
- Spark jobs and data
- Docker volumes
- Monitoring data

#### 2. Incremental Backup

**Frequency**: Every 6 hours
**Retention**: 24 hours

```bash
# Incremental backup script
0 */6 * * * cd /path/to/SparkTest && ./scripts/backup_incremental.sh
```

#### 3. Configuration Backup

**Frequency**: On every change
**Retention**: Version controlled (Git)

```bash
# Commit configuration changes
git add docker-compose.yml .env monitoring/
git commit -m "Update configuration"
git push
```

### Backup Locations

**Primary**: Local storage (`/backups`)
**Secondary**: Remote storage (S3, NFS, etc.)

```bash
# Sync to remote storage
rsync -av backups/ user@backup-server:/backups/sparktest/

# Or use cloud storage
aws s3 sync backups/ s3://sparktest-backups/
```

### Backup Verification

```bash
# Daily backup verification
./scripts/backup.sh && \
./scripts/verify_backup.sh backups/latest.tar.gz
```

Verification checklist:
- [ ] Backup file exists
- [ ] Backup size is reasonable
- [ ] Backup can be extracted
- [ ] Database dump is valid
- [ ] Manifest file is complete

## Recovery Procedures

### Full System Recovery

**Scenario**: Complete system failure, need to rebuild from scratch

**Time Estimate**: 30-45 minutes

**Steps**:

1. **Prepare Recovery Environment** (5 minutes)

```bash
# On new server or clean environment
git clone https://github.com/yourusername/SparkTest.git
cd SparkTest

# Verify prerequisites
docker --version
docker-compose --version
df -h  # Check disk space
```

2. **Restore from Backup** (15 minutes)

```bash
# Copy backup to recovery location
scp user@backup-server:/backups/sparktest/latest.tar.gz ./backups/

# Run restore script
./scripts/restore.sh backups/latest.tar.gz
```

3. **Verify Services** (5 minutes)

```bash
# Check all services are running
docker-compose ps

# Run health check
./scripts/health_check.sh
```

4. **Run Smoke Tests** (5 minutes)

```bash
# Verify functionality
./run_integration_tests.sh smoke
```

5. **Restore Traffic** (2 minutes)

```bash
# Update DNS or load balancer
# Point traffic to recovered system
```

6. **Monitor and Validate** (ongoing)

```bash
# Monitor system
./scripts/monitor.sh

# Check for errors
docker-compose logs -f | grep -i error
```

### Database Recovery

**Scenario**: Database corruption or data loss

**Time Estimate**: 15 minutes

```bash
# 1. Stop services using database
docker-compose stop api-gateway

# 2. Stop database
docker-compose stop postgres

# 3. Remove corrupted data
docker volume rm sparktest_postgres-data

# 4. Restore from backup
./scripts/restore.sh --database-only backups/latest.tar.gz

# 5. Restart services
docker-compose up -d postgres
sleep 10
docker-compose up -d api-gateway

# 6. Verify
docker-compose exec postgres psql -U sparktest -d sparktest_db -c "SELECT COUNT(*) FROM jobs;"
```

### Redis Recovery

**Scenario**: Redis data corruption or loss

**Time Estimate**: 5 minutes

```bash
# 1. Stop Redis
docker-compose stop redis

# 2. Restore RDB file
docker cp backups/redis.rdb $(docker-compose ps -q redis):/data/dump.rdb

# 3. Restart Redis
docker-compose up -d redis

# 4. Verify
docker-compose exec redis redis-cli DBSIZE
```

### Configuration Recovery

**Scenario**: Configuration files corrupted or lost

**Time Estimate**: 10 minutes

```bash
# 1. Revert to previous configuration
git checkout HEAD~1 docker-compose.yml

# Or restore from backup
cp backups/latest/docker-compose.yml .

# 2. Restart services with new config
docker-compose down
docker-compose up -d

# 3. Verify
./scripts/health_check.sh
```

### Spark Cluster Recovery

**Scenario**: Spark cluster failure

**Time Estimate**: 20 minutes

```bash
# 1. Stop Spark services
docker-compose stop spark-master spark-worker-1 spark-worker-2

# 2. Clean work directories
docker-compose exec spark-master rm -rf /tmp/spark-*

# 3. Restart cluster
docker-compose up -d spark-master
sleep 10
docker-compose up -d spark-worker-1 spark-worker-2

# 4. Verify
curl http://localhost:8080
```

## Failure Scenarios

### Scenario 1: Single Container Failure

**Detection**: Health check alerts, monitoring

**Recovery**:

```bash
# Identify failed container
docker-compose ps

# Restart container
docker-compose restart <service-name>

# If restart fails, recreate
docker-compose up -d --force-recreate <service-name>

# Verify
./scripts/health_check.sh
```

**Expected Recovery Time**: < 5 minutes

### Scenario 2: Database Failure

**Detection**: API errors, health check failures

**Recovery**:

```bash
# Follow Database Recovery procedure above
./scripts/restore.sh --database-only backups/latest.tar.gz
```

**Expected Recovery Time**: 15 minutes

### Scenario 3: Complete Infrastructure Failure

**Detection**: All services down, server unreachable

**Recovery**:

```bash
# Follow Full System Recovery procedure
# Provision new server
# Deploy from backup
./scripts/restore.sh backups/latest.tar.gz
```

**Expected Recovery Time**: 45 minutes

### Scenario 4: Data Corruption

**Detection**: Data integrity errors, application failures

**Recovery**:

```bash
# 1. Isolate corrupted data
docker-compose exec postgres pg_dump -U sparktest sparktest_db > corrupt_backup.sql

# 2. Restore from known good backup
./scripts/restore.sh backups/backup_before_corruption.tar.gz

# 3. Analyze and recover partial data if needed
# (Manual data recovery procedures)

# 4. Verify data integrity
./run_integration_tests.sh
```

**Expected Recovery Time**: 1-2 hours

### Scenario 5: Security Breach

**Detection**: Security alerts, suspicious activity

**Immediate Actions**:

```bash
# 1. Isolate system
docker-compose down

# 2. Analyze compromise
# Review logs, audit trails

# 3. Clean recovery
# Rebuild from clean backup
./scripts/restore.sh backups/pre_breach_backup.tar.gz

# 4. Security hardening
# Change all passwords
# Update security configurations
# Apply patches

# 5. Resume operations
docker-compose up -d
```

**Expected Recovery Time**: 2-4 hours

### Scenario 6: Network Failure

**Detection**: Network connectivity issues, service timeouts

**Recovery**:

```bash
# 1. Check network status
docker network ls
docker network inspect sparktest_sparktest-network

# 2. Recreate network if needed
docker-compose down
docker network prune -f
docker-compose up -d

# 3. Verify connectivity
docker-compose exec api-gateway ping spark-master
```

**Expected Recovery Time**: 10 minutes

## Rollback Procedures

### Automated Rollback

**Use Case**: Deployment failures, critical bugs

```bash
# Automatic rollback to last known good state
./scripts/rollback.sh --auto
```

### Manual Rollback Options

#### Option 1: Rollback to Previous Backup

```bash
# Interactive selection
./scripts/rollback.sh

# Select option 1 (backup) and choose backup
```

#### Option 2: Rollback to Previous Git Commit

```bash
# Rollback to specific commit
./scripts/rollback.sh --git <commit-hash>

# Or interactive
./scripts/rollback.sh
# Select option 2
```

#### Option 3: Rollback Configuration Only

```bash
# Rollback just configuration files
./scripts/rollback.sh --config
```

### Rollback Verification

After rollback:

```bash
# 1. Health check
./scripts/health_check.sh

# 2. Smoke tests
./run_integration_tests.sh smoke

# 3. Monitor for issues
./scripts/monitor.sh
```

## Testing and Validation

### Disaster Recovery Testing Schedule

- **Full DR Test**: Quarterly
- **Backup Restore Test**: Monthly
- **Component Failure Test**: Weekly

### DR Test Procedure

**Frequency**: Quarterly

**Steps**:

1. **Plan Test** (1 week before)
   - Schedule maintenance window
   - Notify stakeholders
   - Prepare test environment

2. **Execute Test** (Day of)
   - Simulate disaster scenario
   - Execute recovery procedures
   - Document time and issues
   - Verify functionality

3. **Post-Test Review** (1 week after)
   - Analyze results
   - Update procedures
   - Address gaps
   - Document lessons learned

### Test Scenarios

#### Test 1: Database Restore

```bash
# Create test backup
./scripts/backup.sh

# Simulate database loss
docker volume rm sparktest_postgres-data

# Restore and verify
./scripts/restore.sh backups/latest.tar.gz
./scripts/health_check.sh
```

**Success Criteria**: Database restored within RTO, all data present

#### Test 2: Full System Recovery

```bash
# Create clean environment
docker-compose down -v

# Full restore
./scripts/restore.sh backups/latest.tar.gz

# Verify
./run_integration_tests.sh
```

**Success Criteria**: System fully operational within RTO

#### Test 3: Rollback After Failed Deployment

```bash
# Deploy problematic version
docker-compose up -d

# Detect issues
./scripts/health_check.sh

# Rollback
./scripts/rollback.sh --auto

# Verify
./scripts/health_check.sh
```

**Success Criteria**: Rollback successful, system stable

### DR Documentation

Maintain the following:

- [ ] Current system architecture diagram
- [ ] Backup inventory and locations
- [ ] Recovery procedures (this document)
- [ ] Contact lists
- [ ] Test results and lessons learned
- [ ] Improvement action items

## Emergency Contacts

### Internal Contacts

| Role | Name | Phone | Email | Availability |
|------|------|-------|-------|--------------|
| On-Call Engineer | TBD | TBD | oncall@sparktest.com | 24/7 |
| Team Lead | TBD | TBD | lead@sparktest.com | Business hours |
| Engineering Manager | TBD | TBD | manager@sparktest.com | Business hours |
| CTO | TBD | TBD | cto@sparktest.com | Escalation only |

### External Contacts

| Service | Contact | Phone | Email |
|---------|---------|-------|-------|
| Cloud Provider | AWS Support | TBD | support@aws.com |
| Network Provider | TBD | TBD | TBD |
| Security Team | TBD | TBD | security@company.com |

### Escalation Path

1. **Level 1**: On-call engineer (respond within 15 min)
2. **Level 2**: Team lead (respond within 30 min)
3. **Level 3**: Engineering manager (respond within 1 hour)
4. **Level 4**: CTO (critical only)

## Communication Plan

### During Incident

1. **Initial Notification** (5 minutes)
   - Alert on-call team
   - Create incident ticket
   - Start incident log

2. **Status Updates** (Every 30 minutes)
   - Update stakeholders
   - Post to status page
   - Document progress

3. **Resolution Notification**
   - Announce recovery
   - Provide summary
   - Schedule post-mortem

### Status Page

Update: http://status.sparktest.com

```bash
# Post status update
curl -X POST https://status.sparktest.com/api/incidents \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"Investigating database issues"}'
```

## Post-Incident Procedures

### Immediate (< 24 hours)

1. Verify system stability
2. Monitor for recurring issues
3. Document incident timeline
4. Gather logs and evidence

### Short-term (< 1 week)

1. Conduct post-mortem meeting
2. Document root cause
3. Create action items
4. Update runbooks

### Long-term (< 1 month)

1. Implement preventive measures
2. Update DR procedures
3. Conduct training if needed
4. Review and improve monitoring

### Post-Mortem Template

```markdown
# Incident Post-Mortem

## Incident Summary
- Date/Time:
- Duration:
- Impact:
- Root Cause:

## Timeline
- [Time] Detection
- [Time] Response initiated
- [Time] Resolution

## What Went Well
-

## What Went Wrong
-

## Action Items
- [ ] Item 1 (Owner, Due Date)
- [ ] Item 2 (Owner, Due Date)

## Lessons Learned
-
```

## Continuous Improvement

### Metrics to Track

- Recovery time (actual vs target)
- Data loss (actual vs RPO)
- Backup success rate
- Test success rate
- Incident frequency

### Review Schedule

- **Monthly**: Review backup success rate
- **Quarterly**: Full DR test and review
- **Annually**: Comprehensive DR plan update

### Improvement Process

1. Identify gaps and issues
2. Prioritize improvements
3. Implement changes
4. Test and validate
5. Update documentation

## Appendix

### Quick Reference Commands

```bash
# Emergency procedures
./scripts/health_check.sh          # Check system health
./scripts/backup.sh                # Create backup
./scripts/restore.sh <path>        # Restore from backup
./scripts/rollback.sh --auto       # Automated rollback
docker-compose logs -f             # View logs
docker-compose restart <service>   # Restart service

# Common recovery commands
docker-compose down -v             # Full reset
docker-compose up -d               # Start all services
./run_integration_tests.sh smoke  # Quick validation
```

### Backup Locations

- Primary: `/path/to/SparkTest/backups/`
- Remote: `s3://sparktest-backups/` or `/remote/backup/sparktest/`
- Git: `https://github.com/yourusername/SparkTest`

### Critical File Locations

- Configuration: `docker-compose.yml`, `.env`
- Scripts: `scripts/`, `*.sh`
- Data: `spark/data/`, Docker volumes
- Logs: `spark/logs/`, Docker logs

---

**Document Version**: 1.0
**Last Updated**: 2025-01-12
**Next Review**: 2025-04-12
**Maintained By**: Agent 10 Team
**Approved By**: Engineering Manager

**IMPORTANT**: This is a living document. Update after each incident and DR test.
