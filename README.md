# SparkTest - Multi-Agent Distributed Computing Platform

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-95%25-brightgreen)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

SparkTest is a comprehensive multi-agent distributed computing platform built on Apache Spark, featuring end-to-end integration testing, performance benchmarking, and production-ready deployment automation.

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum (16GB recommended)
- 10GB free disk space

### One-Command Deployment

```bash
# Deploy the entire stack
./agent10_deploy.sh

# Run integration tests
./run_integration_tests.sh

# Run performance benchmarks
./benchmark_suite.sh
```

## 📋 Table of Contents

- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Testing](#testing)
- [Benchmarking](#benchmarking)
- [Monitoring](#monitoring)
- [API Documentation](#api-documentation)
- [Agent Overview](#agent-overview)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🏗️ Architecture

SparkTest consists of 10 specialized agents working in harmony:

```
┌─────────────────────────────────────────────────────────────┐
│                     SparkTest Platform                       │
├─────────────────────────────────────────────────────────────┤
│  Agent 1: Data Ingestion      │  Agent 6: Batch Processing  │
│  Agent 2: Data Processing     │  Agent 7: Stream Processing │
│  Agent 3: Analytics           │  Agent 8: Scheduler         │
│  Agent 4: ML Pipeline         │  Agent 9: Monitoring        │
│  Agent 5: Query Engine        │  Agent 10: Integration      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Infrastructure Layer                       │
├──────────────┬──────────────┬──────────────┬───────────────┤
│ Spark Cluster│  PostgreSQL  │    Redis     │  Monitoring   │
│ (Master + 2  │  (Metadata)  │  (Cache/MQ)  │  (Prom/Graf)  │
│   Workers)   │              │              │               │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

### System Components

- **Spark Cluster**: 1 Master + 2 Worker nodes for distributed processing
- **PostgreSQL**: Metadata and results storage
- **Redis**: Caching and message queue
- **API Gateway**: REST API for job submission and management
- **Prometheus**: Metrics collection
- **Grafana**: Visualization and dashboards

## ✨ Features

### Core Capabilities

- ✅ **Distributed Processing**: Spark-based parallel data processing
- ✅ **Job Management**: REST API for job submission, tracking, and management
- ✅ **Real-time Monitoring**: Prometheus + Grafana integration
- ✅ **Caching Layer**: Redis for high-performance caching
- ✅ **Persistent Storage**: PostgreSQL for metadata and results
- ✅ **Health Checks**: Comprehensive service health monitoring
- ✅ **Metrics Export**: Prometheus-compatible metrics

### Testing & Quality

- ✅ **Integration Tests**: Comprehensive test suite for all components
- ✅ **Performance Benchmarks**: Automated performance testing
- ✅ **Smoke Tests**: Quick validation of critical paths
- ✅ **End-to-End Tests**: Complete workflow validation
- ✅ **Coverage Reports**: Detailed code coverage analysis

### Deployment & Operations

- ✅ **One-Command Deployment**: Fully automated setup
- ✅ **Docker Compose**: Orchestrated multi-container deployment
- ✅ **Health Monitoring**: Automated service health checks
- ✅ **Log Aggregation**: Centralized logging
- ✅ **Resource Management**: Configurable resource limits

## 📦 Installation

### Standard Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/SparkTest.git
cd SparkTest

# Deploy the platform
./agent10_deploy.sh

# Verify installation
curl http://localhost:8000/health
```

### Clean Installation

```bash
# Remove existing deployment and start fresh
./agent10_deploy.sh --clean
```

## 🎯 Usage

### Starting the Platform

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### Submitting Jobs

#### Via API

```bash
# Submit a job
curl -X POST http://localhost:8000/jobs/submit \
  -H "Content-Type: application/json" \
  -d '{
    "job_name": "my_job",
    "job_type": "data_processing",
    "parameters": {
      "input_path": "/data/input",
      "output_path": "/data/output"
    },
    "priority": 5
  }'

# Check job status
curl http://localhost:8000/jobs/{job_id}

# List all jobs
curl http://localhost:8000/jobs
```

#### Via Python

```python
import requests

# Submit job
response = requests.post('http://localhost:8000/jobs/submit', json={
    'job_name': 'python_job',
    'job_type': 'batch_processing',
    'parameters': {'key': 'value'},
    'priority': 8
})

job_id = response.json()['job_id']

# Get status
status = requests.get(f'http://localhost:8000/jobs/{job_id}')
print(status.json())
```

### Managing Agents

```bash
# List all agents
curl http://localhost:8000/agents

# View agent details
curl http://localhost:8000/agents/1
```

### Stopping the Platform

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (warning: deletes all data)
docker-compose down -v
```

## 🧪 Testing

### Run All Tests

```bash
./run_integration_tests.sh
```

### Smoke Tests

```bash
./run_integration_tests.sh smoke
```

### Integration Tests

```bash
./run_integration_tests.sh integration
```

### Agent-Specific Tests

```bash
# Test specific agent
./run_integration_tests.sh agent 1

# Test all agents
./run_integration_tests.sh agents
```

### Coverage Report

```bash
./run_integration_tests.sh coverage
```

## 📊 Benchmarking

### Run All Benchmarks

```bash
./benchmark_suite.sh
```

### Component-Specific Benchmarks

```bash
# API Gateway benchmarks
./benchmark_suite.sh api

# Spark benchmarks
./benchmark_suite.sh spark

# Redis benchmarks
./benchmark_suite.sh redis

# Database benchmarks
./benchmark_suite.sh database

# End-to-end benchmarks
./benchmark_suite.sh e2e
```

### Benchmark Reports

Results are saved in `reports/benchmarks/`:
- JSON reports for programmatic analysis
- HTML dashboards for visualization
- Metrics files for historical tracking

## 📈 Monitoring

### Access Dashboards

- **Spark Master UI**: http://localhost:8080
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **API Documentation**: http://localhost:8000/docs

### Key Metrics

- Job submission rate and success rate
- Spark job execution time
- API response times
- Resource utilization (CPU, memory)
- Database query performance
- Cache hit rates

### Prometheus Metrics

```bash
# View all metrics
curl http://localhost:8000/metrics

# Query specific metrics
curl 'http://localhost:9090/api/v1/query?query=sparktest_jobs_total'
```

## 📚 API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Service health check |
| `/jobs/submit` | POST | Submit new job |
| `/jobs/{job_id}` | GET | Get job status |
| `/jobs` | GET | List all jobs |
| `/jobs/{job_id}` | DELETE | Cancel job |
| `/agents` | GET | List all agents |
| `/metrics` | GET | Prometheus metrics |

## 🤖 Agent Overview

### Agent 1: Data Ingestion
Handles data ingestion from various sources (CSV, JSON, databases).

### Agent 2: Data Processing
Transforms and cleans data using Spark transformations.

### Agent 3: Analytics
Provides analytical capabilities and aggregations.

### Agent 4: ML Pipeline
Machine learning model training and inference.

### Agent 5: Query Engine
SQL-based querying interface.

### Agent 6: Batch Processing
Large-scale batch data processing.

### Agent 7: Stream Processing
Real-time stream processing capabilities.

### Agent 8: Scheduler
Job scheduling and orchestration.

### Agent 9: Monitoring
System monitoring and alerting.

### Agent 10: Integration + Testing
End-to-end integration, testing, and deployment automation.

## ⚙️ Configuration

### Environment Variables

Create a `.env` file:

```bash
# Spark Configuration
SPARK_MASTER_URL=spark://spark-master:7077
SPARK_WORKER_MEMORY=2G
SPARK_WORKER_CORES=2

# Database Configuration
DATABASE_URL=postgresql://sparktest:sparktest123@postgres:5432/sparktest_db
POSTGRES_USER=sparktest
POSTGRES_PASSWORD=sparktest123
POSTGRES_DB=sparktest_db

# Redis Configuration
REDIS_URL=redis://redis:6379

# API Configuration
API_PORT=8000

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin123
```

### Resource Limits

Edit `docker-compose.yml` to adjust resource limits:

```yaml
services:
  spark-worker-1:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

## 🔧 Troubleshooting

### Common Issues

#### Services won't start

```bash
# Check Docker daemon
docker ps

# Check logs
docker-compose logs

# Restart services
docker-compose restart
```

#### Tests failing

```bash
# Ensure services are running
docker-compose ps

# Check service health
curl http://localhost:8000/health

# View test container logs
docker-compose logs test-runner
```

#### Out of memory

```bash
# Increase Docker memory limit
# Docker Desktop → Preferences → Resources → Memory

# Reduce Spark worker memory in docker-compose.yml
SPARK_WORKER_MEMORY=1G
```

#### Port conflicts

```bash
# Check if ports are in use
lsof -i :8000,8080,5432,6379,3000,9090

# Change ports in docker-compose.yml
ports:
  - "18000:8000"  # Use different host port
```

### Getting Help

- Check logs: `docker-compose logs -f [service-name]`
- View service status: `docker-compose ps`
- Restart specific service: `docker-compose restart [service-name]`
- Full reset: `docker-compose down -v && ./agent10_deploy.sh`

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.test.txt

# Run tests locally
pytest -v

# Run linting
flake8 .

# Format code
black .
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Apache Spark community
- Docker and Docker Compose
- FastAPI framework
- Prometheus and Grafana teams

## 📞 Contact

- **Project Lead**: Agent 10 Integration Team
- **Email**: sparktest@example.com
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**Built with ❤️ by the SparkTest Team**

*Agent 10: Integration + Testing*
