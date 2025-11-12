# SparkTest Architecture Documentation

## Overview

SparkTest is a multi-agent distributed computing platform designed for scalable data processing, testing, and monitoring. This document provides a comprehensive overview of the system architecture.

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  (HTTP Clients, CLI Tools, Web Dashboard, External Services)    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI Application (Port 8000)                         │   │
│  │  - REST API Endpoints                                    │   │
│  │  - Request Validation                                    │   │
│  │  - Authentication & Authorization                        │   │
│  │  - Rate Limiting                                         │   │
│  │  - Prometheus Metrics Export                             │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestration Layer                          │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐   │
│  │   Redis MQ     │  │  Job Scheduler │  │  Agent Manager  │   │
│  │  - Queue       │  │  - Priorities  │  │  - Coordination │   │
│  │  - Cache       │  │  - Retry Logic │  │  - Health Check │   │
│  │  - Pub/Sub     │  │  - Timeouts    │  │  - Load Balance │   │
│  └────────────────┘  └────────────────┘  └─────────────────┘   │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Processing Layer                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              Apache Spark Cluster                       │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│  │  │ Spark Master │  │ Worker Node 1│  │ Worker Node 2│  │    │
│  │  │ (Port 7077)  │  │              │  │              │  │    │
│  │  │ (UI: 8080)   │  │              │  │              │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  Multi-Agent System:                                             │
│  ┌─────────┬─────────┬─────────┬─────────┬──────────┐          │
│  │ Agent 1 │ Agent 2 │ Agent 3 │ Agent 4 │ Agent 5  │          │
│  │ Ingest  │ Process │Analytics│   ML    │  Query   │          │
│  └─────────┴─────────┴─────────┴─────────┴──────────┘          │
│  ┌─────────┬─────────┬─────────┬─────────┬──────────┐          │
│  │ Agent 6 │ Agent 7 │ Agent 8 │ Agent 9 │ Agent 10 │          │
│  │  Batch  │ Stream  │Schedule │ Monitor │  Test    │          │
│  └─────────┴─────────┴─────────┴─────────┴──────────┘          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Storage Layer                               │
│  ┌──────────────────┐         ┌───────────────────┐             │
│  │   PostgreSQL     │         │      Redis        │             │
│  │   (Port 5432)    │         │   (Port 6379)     │             │
│  │                  │         │                   │             │
│  │ - Job Metadata   │         │ - Session Cache   │             │
│  │ - Results        │         │ - Job Queue       │             │
│  │ - Metrics        │         │ - Temp Storage    │             │
│  │ - Audit Logs     │         │ - Pub/Sub         │             │
│  └──────────────────┘         └───────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring Layer                              │
│  ┌──────────────────┐         ┌───────────────────┐             │
│  │   Prometheus     │────────▶│     Grafana       │             │
│  │   (Port 9090)    │         │   (Port 3000)     │             │
│  │                  │         │                   │             │
│  │ - Metrics Store  │         │ - Dashboards      │             │
│  │ - Alerting       │         │ - Visualization   │             │
│  │ - Time Series DB │         │ - Alerting UI     │             │
│  └──────────────────┘         └───────────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. API Gateway

**Technology**: FastAPI (Python 3.11)

**Responsibilities**:
- HTTP request handling
- Request validation using Pydantic models
- Job submission and management
- Authentication and authorization
- Rate limiting and throttling
- Metrics export (Prometheus format)
- Health check endpoints

**Key Endpoints**:
- `POST /jobs/submit` - Submit new jobs
- `GET /jobs/{job_id}` - Get job status
- `GET /jobs` - List all jobs
- `DELETE /jobs/{job_id}` - Cancel job
- `GET /health` - Health check
- `GET /metrics` - Prometheus metrics

**Port**: 8000

### 2. Spark Cluster

**Technology**: Apache Spark 3.5.0

**Architecture**:
- 1 Master node (coordinator)
- 2 Worker nodes (executors)

**Master Node**:
- Cluster coordination
- Resource allocation
- Job scheduling
- Worker management
- Web UI (port 8080)
- RPC endpoint (port 7077)

**Worker Nodes**:
- Task execution
- Data processing
- Resource reporting
- Configurable memory and cores

**Configuration**:
- Worker Memory: 2GB per worker
- Worker Cores: 2 cores per worker
- Shuffle Partitions: 4 (optimized for small cluster)

### 3. PostgreSQL Database

**Technology**: PostgreSQL 15 Alpine

**Purpose**: Persistent storage for metadata and results

**Schema**:

```sql
-- Jobs table
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(255) UNIQUE NOT NULL,
    job_name VARCHAR(255) NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL,
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    parameters JSONB,
    result JSONB,
    error_message TEXT
);

-- Metrics table
CREATE TABLE metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(255) NOT NULL,
    metric_value NUMERIC NOT NULL,
    tags JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- Audit logs table
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    entity_id VARCHAR(255),
    user_id VARCHAR(255),
    details JSONB,
    timestamp TIMESTAMP DEFAULT NOW()
);
```

**Port**: 5432

### 4. Redis

**Technology**: Redis 7 Alpine

**Use Cases**:
1. **Job Queue**: FIFO queue for job scheduling
2. **Cache**: Fast access to frequently used data
3. **Session Storage**: User session management
4. **Pub/Sub**: Event broadcasting
5. **Temporary Storage**: Intermediate results

**Key Data Structures**:
- `job:{job_id}` - Hash containing job metadata
- `job_queue` - List for job queue
- `cache:{key}` - Cached data
- Pub/Sub channels for events

**Port**: 6379

### 5. Monitoring Stack

#### Prometheus

**Technology**: Prometheus (latest)

**Responsibilities**:
- Metrics collection from API Gateway
- Time-series data storage
- Alert evaluation
- PromQL query interface

**Scrape Targets**:
- API Gateway (sparktest-api:8000/metrics)
- Spark Master (spark-master:8080/metrics)
- Self-monitoring (prometheus:9090)

**Scrape Interval**: 15 seconds

**Port**: 9090

#### Grafana

**Technology**: Grafana (latest)

**Features**:
- Visual dashboards
- Real-time metrics
- Custom alerts
- Multiple data sources
- User management

**Credentials**:
- Username: admin
- Password: admin123

**Port**: 3000

## Agent Architecture

### Agent 1: Data Ingestion
**Responsibility**: Ingest data from various sources

**Capabilities**:
- CSV/JSON file ingestion
- Database connectors
- API data fetching
- Stream ingestion

**Technologies**: PySpark, pandas

### Agent 2: Data Processing
**Responsibility**: Transform and clean data

**Capabilities**:
- Data cleaning
- Transformations
- Filtering
- Enrichment

**Technologies**: PySpark DataFrame API

### Agent 3: Analytics
**Responsibility**: Analytical computations

**Capabilities**:
- Aggregations
- Statistical analysis
- Reporting
- Data summarization

**Technologies**: PySpark SQL

### Agent 4: ML Pipeline
**Responsibility**: Machine learning workflows

**Capabilities**:
- Model training
- Feature engineering
- Predictions
- Model evaluation

**Technologies**: PySpark MLlib

### Agent 5: Query Engine
**Responsibility**: SQL-based querying

**Capabilities**:
- SQL query execution
- Query optimization
- Result caching
- JDBC connections

**Technologies**: PySpark SQL

### Agent 6: Batch Processing
**Responsibility**: Large-scale batch jobs

**Capabilities**:
- Batch data processing
- Large dataset handling
- Scheduled batch jobs
- ETL pipelines

**Technologies**: PySpark

### Agent 7: Stream Processing
**Responsibility**: Real-time data processing

**Capabilities**:
- Stream ingestion
- Real-time transformations
- Windowing operations
- Stream analytics

**Technologies**: PySpark Structured Streaming

### Agent 8: Scheduler
**Responsibility**: Job scheduling and orchestration

**Capabilities**:
- Job scheduling
- Dependency management
- Retry logic
- Priority queuing

**Technologies**: Python, Redis

### Agent 9: Monitoring
**Responsibility**: System monitoring and alerting

**Capabilities**:
- Metrics collection
- Health checks
- Alerting
- Performance monitoring

**Technologies**: Prometheus, Grafana

### Agent 10: Integration + Testing
**Responsibility**: Testing and deployment

**Capabilities**:
- Integration testing
- Performance benchmarking
- Deployment automation
- CI/CD orchestration

**Technologies**: pytest, Docker Compose

## Data Flow

### Job Submission Flow

```
1. Client → API Gateway
   POST /jobs/submit with job parameters

2. API Gateway → Redis
   Store job metadata in hash
   Push job ID to queue

3. API Gateway → Client
   Return job_id and status

4. Scheduler (Agent 8) → Redis
   Poll job queue
   Fetch job metadata

5. Scheduler → Spark Cluster
   Submit Spark job with parameters

6. Spark Cluster → Processing
   Execute job across worker nodes

7. Spark Cluster → Redis/PostgreSQL
   Store intermediate/final results

8. Agent 9 → Prometheus
   Export metrics

9. Client → API Gateway
   GET /jobs/{job_id} for status

10. API Gateway → Redis/PostgreSQL
    Fetch job status and results

11. API Gateway → Client
    Return job status and results
```

## Scalability Considerations

### Horizontal Scaling

**Spark Workers**:
```yaml
# Add more workers in docker-compose.yml
spark-worker-3:
  image: bitnami/spark:3.5.0
  environment:
    - SPARK_MODE=worker
    - SPARK_MASTER_URL=spark://spark-master:7077
```

**API Gateway**:
```yaml
# Add load balancer and multiple API instances
api-gateway-2:
  build: ./services/api-gateway
  environment:
    - INSTANCE_ID=2
```

### Vertical Scaling

Adjust resource limits in `docker-compose.yml`:

```yaml
services:
  spark-worker-1:
    environment:
      - SPARK_WORKER_MEMORY=4G
      - SPARK_WORKER_CORES=4
```

## Security Considerations

### Current Implementation
- Basic health checks
- Internal network isolation
- No external authentication (development mode)

### Production Recommendations
1. **Authentication**: Implement JWT or OAuth2
2. **Encryption**: Enable TLS/SSL for all communications
3. **Network**: Use private networks and firewalls
4. **Secrets**: Use secret management (Vault, AWS Secrets Manager)
5. **Database**: Enable SSL connections
6. **API**: Rate limiting and API keys
7. **Monitoring**: Secure Grafana with strong passwords

## Performance Optimization

### Spark Optimization
- Tune `spark.sql.shuffle.partitions` based on data size
- Enable broadcast joins for small tables
- Cache frequently accessed DataFrames
- Use appropriate file formats (Parquet, ORC)

### Redis Optimization
- Set appropriate memory limits
- Enable persistence for critical data
- Use Redis Cluster for horizontal scaling

### Database Optimization
- Create indexes on frequently queried columns
- Use connection pooling
- Implement query caching
- Regular VACUUM operations

### API Optimization
- Implement response caching
- Use async/await for I/O operations
- Enable HTTP/2
- Compress responses

## Disaster Recovery

### Backup Strategy
1. **Database**: Daily automated backups
2. **Redis**: RDB snapshots + AOF logs
3. **Configuration**: Version control all configs
4. **Monitoring**: Alert on backup failures

### Recovery Procedures
1. **Database Restore**: `pg_restore` from backup
2. **Redis Restore**: Load RDB snapshot
3. **Service Recovery**: Redeploy from git + backups

## Monitoring and Alerting

### Key Metrics to Monitor
- Job submission rate
- Job success/failure rate
- API response time (p50, p95, p99)
- Spark job execution time
- Resource utilization (CPU, memory, disk)
- Database query performance
- Cache hit rate

### Alert Conditions
- Job failure rate > 10%
- API response time > 1s (p95)
- Disk usage > 80%
- Memory usage > 85%
- Service health check failures
- Database connection pool exhaustion

## Testing Strategy

### Unit Tests
- Individual function testing
- Mocked dependencies
- Fast execution

### Integration Tests
- Component interaction testing
- Real service dependencies
- Docker-based test environment

### End-to-End Tests
- Complete workflow validation
- Production-like environment
- User scenario testing

### Performance Tests
- Load testing
- Stress testing
- Benchmark comparisons

## Deployment Models

### Development
- Single machine
- docker-compose
- Minimal resources

### Staging
- Multi-node cluster
- Kubernetes or docker-compose
- Production-like configuration

### Production
- Kubernetes cluster
- Horizontal pod autoscaling
- High availability
- Load balancing
- Multi-region deployment

## Future Enhancements

1. **Kubernetes Support**: Helm charts for K8s deployment
2. **Stream Processing**: Enhanced real-time capabilities
3. **ML Models**: Pre-built model repository
4. **UI Dashboard**: Web-based management console
5. **Multi-tenancy**: Support for multiple tenants
6. **Advanced Security**: Enhanced authentication and authorization
7. **Data Catalog**: Metadata management system
8. **Workflow DAGs**: Visual workflow builder

---

**Document Version**: 1.0
**Last Updated**: 2025-01-12
**Maintained By**: Agent 10 Team
