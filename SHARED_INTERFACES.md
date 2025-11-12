# Shared Interfaces Documentation

This document describes the shared interfaces used across all agents in the DGX Spark Playbooks project.

## Overview

All agents share common infrastructure to ensure consistency, ease of deployment, and simplified monitoring.

## 1. Docker Base Image

**Location:** `shared/base.Dockerfile`

All agents inherit from a unified base Docker image that provides:

- **Base Image:** NVIDIA PyTorch 24.10 with Python 3
- **CUDA Toolkit:** Version 12.3
- **NVIDIA Container Toolkit:** For GPU access
- **Common Python Packages:**
  - `aiohttp`, `httpx` - Async HTTP clients
  - `fastapi`, `uvicorn` - Web frameworks
  - `numpy`, `pandas` - Data processing
  - `pytest` - Testing
  - `prometheus-client` - Metrics

### Usage

```dockerfile
FROM shared/base.Dockerfile

# Add agent-specific dependencies
RUN pip install --no-cache-dir agent-specific-package

# Copy agent code
COPY agent_code/ /app/

# Set entrypoint
CMD ["python", "main.py"]
```

### Building Agent Images

```bash
# Build with base image
docker build -f shared/base.Dockerfile -t dgx-spark/base:latest .

# Build agent-specific image
docker build -f agents/agent9/Dockerfile -t dgx-spark/agent9:latest .
```

---

## 2. Unified Configuration Schema

**Location:** `shared/config_schema.yaml`

All playbooks follow a standardized YAML configuration format.

### Schema Structure

```yaml
playbook:
  name: string              # Playbook identifier (e.g., "comfy-ui")
  description: string       # Human-readable description
  version: string           # Semantic version (e.g., "1.0.0")
  agent: string             # Agent ID (e.g., "agent9")

  dependencies: [string]    # List of dependent agents
  ports: [int]              # Exposed ports

  docker:
    image: string           # Docker image name
    environment: object     # Environment variables

  volumes: [string]         # Volume mounts

  gpu_required: boolean     # GPU requirement flag
  gpu_config:              # GPU configuration
    count: int
    capabilities: [string]

  resources:               # Resource limits
    cpu: string
    memory: string

  health_check:            # Health check config
    enabled: boolean
    endpoint: string
    interval: int
```

### Loading Configurations

```python
from shared.utils.config_loader import ConfigLoader

loader = ConfigLoader()
config = loader.load_config("playbooks/comfy_ui/config.yaml")

# Validate configuration
loader.validate_config(config)

# Access configuration values
playbook = config["playbook"]
ports = playbook["ports"]
dependencies = playbook["dependencies"]
```

### Creating Configurations

```python
from shared.utils.config_loader import create_config_from_template

config = create_config_from_template(
    name="my-playbook",
    agent="agent9",
    description="My custom playbook",
    ports=[8000],
    dependencies=["agent4"],
    gpu_required=True
)
```

---

## 3. Health Check API

**Location:** `shared/health_check.py`

Unified health checking for all services.

### Basic Usage

```python
from shared.health_check import HealthChecker

checker = HealthChecker(timeout=10)

# Check a single service
result = await checker.check_service(
    host="localhost",
    port=8188,
    endpoint="/health"
)

print(f"Status: {result.status.value}")
print(f"Response time: {result.response_time_ms}ms")
```

### Command Line Usage

```bash
# Check single service
python shared/health_check.py --port 8188 --endpoint /health

# Check all Agent 9 services
python shared/health_check.py --agent9

# Output as JSON
python shared/health_check.py --port 8188 --json
```

### Docker Health Checks

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python /app/shared/health_check.py --port 8188
```

### Docker Compose Integration

```yaml
services:
  my-service:
    healthcheck:
      test: ["CMD", "python", "/app/shared/health_check.py", "--port", "8188"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```

### Checking Multiple Services

```python
from shared.health_check import HealthChecker

checker = HealthChecker()

services = [
    {"name": "ComfyUI", "port": 8188, "endpoint": "/system_stats"},
    {"name": "RAG", "port": 3000, "endpoint": "/health"},
    {"name": "Chatbot", "port": 8080, "endpoint": "/health"}
]

results = await checker.check_multiple_services(services)
checker.print_results(results)
```

---

## 4. Shared Utilities

### Logger

**Location:** `shared/utils/logger.py`

Consistent logging across all agents.

```python
from shared.utils.logger import setup_logger

logger = setup_logger(
    name="agent9",
    level="INFO",
    log_format="json",
    log_file="/app/logs/agent9.log",
    agent="agent9",
    playbook="comfy-ui"
)

logger.info("Service started")
logger.error("Error occurred", extra={"error_code": 500})
```

### Config Loader

**Location:** `shared/utils/config_loader.py`

```python
from shared.utils.config_loader import load_playbook_config

config = load_playbook_config("playbooks/comfy_ui/config.yaml")
```

---

## 5. Directory Structure

All agents follow this structure:

```
dgx-spark-playbooks/
├── shared/                      # Shared infrastructure
│   ├── base.Dockerfile          # Base Docker image
│   ├── config_schema.yaml       # Configuration schema
│   ├── health_check.py          # Health check API
│   └── utils/                   # Shared utilities
│       ├── config_loader.py
│       └── logger.py
│
├── agents/                      # Agent implementations
│   ├── agent1_infra/
│   ├── agent2_dashboard/
│   ├── ...
│   └── agent9_applications/     # Current: Agent 9
│       ├── agent9_app_registry.py
│       └── playbooks/
│
├── tests/                       # Tests
│   ├── unit/
│   └── integration/
│
├── monitoring/                  # Monitoring configs
│   ├── prometheus.yml
│   └── grafana/
│
├── docker-compose.yml           # Main orchestration
└── README.md                    # Documentation
```

---

## 6. Environment Variables

All agents use consistent environment variable naming:

```bash
# Infrastructure URLs
AGENT_INFERENCE_URL=http://agent4:8000
AGENT_MULTIMODAL_URL=http://agent8:8888

# Model Configuration
EMBEDDING_MODEL=text-embedding-ada-002
LLM_MODEL=gpt-4

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

See `.env.example` for complete list.

---

## 7. Port Allocation

Standardized port ranges by agent:

| Agent | Port Range | Services |
|-------|------------|----------|
| Agent 1 | 7000-7099 | Infrastructure |
| Agent 2 | 7100-7199 | Dashboard |
| Agent 3 | 7200-7299 | Storage |
| Agent 4 | 8000-8099 | Inference |
| Agent 5 | 8100-8199 | Inference |
| Agent 6 | 8200-8299 | Training |
| Agent 7 | 8300-8399 | Optimization |
| Agent 8 | 8800-8899 | Multi-modal |
| Agent 9 | 3000-3099, 8080-8199 | Applications |
| Agent 10 | 9000-9099 | Integration |

### Agent 9 Ports

- 8188: ComfyUI
- 3000: RAG Workbench
- 8080: Multi-Agent Chatbot
- 3001: txt2kg
- 8081: VSS

---

## 8. Monitoring & Metrics

All services expose Prometheus metrics at `/metrics`:

```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

# Use in code
@request_duration.time()
async def process_request():
    request_count.inc()
    # ... handle request
```

### Standard Metrics

All services expose:
- `up` - Service availability
- `requests_total` - Request counter
- `request_duration_seconds` - Request latency
- `errors_total` - Error counter

GPU services additionally expose:
- `gpu_utilization_percent`
- `gpu_memory_used_bytes`
- `gpu_temperature_celsius`

---

## 9. Security

### Authentication (Optional)

```python
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(token: str = Depends(security)):
    # Verify JWT token
    if not is_valid_token(token):
        raise HTTPException(status_code=401)
```

### TLS/SSL (Optional)

```yaml
# docker-compose.yml
services:
  my-service:
    environment:
      - ENABLE_TLS=true
      - TLS_CERT_PATH=/certs/cert.pem
      - TLS_KEY_PATH=/certs/key.pem
    volumes:
      - ./certs:/certs:ro
```

---

## 10. Testing

All agents include standardized tests:

```python
# tests/unit/test_health.py
import pytest
from shared.health_check import HealthChecker

@pytest.mark.asyncio
async def test_health_check():
    checker = HealthChecker()
    result = await checker.check_service(
        host="localhost",
        port=8188,
        endpoint="/health"
    )
    assert checker.is_healthy(result)
```

Run tests:

```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# With coverage
pytest --cov=shared --cov=playbooks tests/
```

---

## 11. CI/CD Integration

GitHub Actions example:

```yaml
name: Agent 9 CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build base image
        run: docker build -f shared/base.Dockerfile -t base .
      - name: Run tests
        run: docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

---

## Support

For questions or issues with shared interfaces:
- Check documentation in `shared/`
- Review example configurations in playbooks
- See integration tests in `tests/integration/`
