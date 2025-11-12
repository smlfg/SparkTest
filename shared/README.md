# Shared Infrastructure

This directory contains shared components used by all agents in the DGX Spark Playbooks system.

## Contents

### Core Files

1. **`base.Dockerfile`** - Base Docker image for all agents
   - Based on NVIDIA PyTorch with CUDA support
   - Includes common dependencies and utilities
   - Pre-configured with GPU support

2. **`config_schema.yaml`** - Unified configuration schema
   - Standard format for all playbook configurations
   - Validation rules and examples
   - Documentation for all configuration options

3. **`health_check.py`** - Health check API
   - Service health monitoring
   - Port availability checking
   - Detailed health status reporting

### Utilities (`utils/`)

- **`config_loader.py`** - Configuration loading and validation
- **`logger.py`** - Standardized logging setup
- **`docker_utils.py`** - Docker operations and checks

## Usage

### Using the Base Image

```dockerfile
# In your agent's Dockerfile
FROM dgx-spark-base:latest

# Your agent-specific configuration
...
```

### Health Checks

```python
from shared import check_service, wait_for_service

# Quick check
if check_service(port=8888, endpoint="/health"):
    print("Service is healthy")

# Wait for service
wait_for_service(port=8888, timeout=60)
```

```bash
# CLI usage
python shared/health_check.py 8888 --endpoint /health
python shared/health_check.py 8888 --wait --wait-timeout 60
```

### Configuration Loading

```python
from shared.utils import load_config, validate_config

# Load configuration
config = load_config("path/to/config.yaml")

# Validate configuration
validate_config(config)
```

### Logging

```python
from shared.utils import setup_logger

# Setup logger
logger = setup_logger(
    name="agent3",
    level="INFO",
    log_file="logs/agent3.log",
    log_format="json"
)

logger.info("Agent started")
```

### Docker Utilities

```python
from shared.utils import check_docker, is_container_running

# Check Docker
if check_docker():
    print("Docker is available")

# Check container
if is_container_running("agent3-jax-dev"):
    print("Container is running")
```

## Configuration Schema

All agents should follow the unified configuration schema defined in `config_schema.yaml`.

### Required Fields

```yaml
name: "playbook-name"
agent: "agent3"
version: "1.0.0"
```

### Example Configuration

```yaml
name: "jax-environment"
agent: "agent3"
version: "1.0.0"
description: "JAX development environment"

dependencies:
  - "agent1"
  - "docker"

ports:
  - 8888
  - 6006

gpu_required: true
gpu_config:
  count: 1
  capabilities: ["compute", "utility"]

health_check:
  enabled: true
  endpoint: "/health"
  port: 8888
```

## Building the Base Image

```bash
# Build base image
docker build -f shared/base.Dockerfile -t dgx-spark-base:latest .

# Or use docker-compose
docker-compose build base
```

## Testing

```bash
# Run shared module tests
pytest tests/unit/test_health_check.py
pytest tests/unit/test_config_loader.py

# Run all tests
pytest tests/
```

## Integration

All agents should:

1. **Extend the base image** or install shared dependencies
2. **Follow the configuration schema** for consistency
3. **Implement health check endpoints** for monitoring
4. **Use shared utilities** for common operations
5. **Log using the standard logger** for centralized logging

## Dependencies

### Python Packages

Core shared dependencies (pre-installed in base image):
- `fastapi` - Web framework
- `requests` / `httpx` - HTTP clients
- `pyyaml` - YAML parsing
- `pydantic` - Data validation
- `pytest` - Testing framework

### System Requirements

- Docker 20.10+
- NVIDIA Docker runtime (for GPU support)
- Python 3.11+

## Development

### Adding New Utilities

1. Create module in `shared/utils/`
2. Add imports to `shared/utils/__init__.py`
3. Write tests in `tests/unit/`
4. Update this README

### Modifying Base Image

1. Edit `shared/base.Dockerfile`
2. Rebuild: `docker build -f shared/base.Dockerfile -t dgx-spark-base:latest .`
3. Test with existing agents
4. Update version and documentation

## See Also

- [Main README](../README.md)
- [Configuration Schema](config_schema.yaml)
- [Agent 3 Documentation](../agents/agent3_dev_environments/README.md)
- [Testing Guide](../tests/README.md)
