# Shared Components

Shared infrastructure components used across all DGX Spark agents.

## Components

### 1. Base Docker Image (`base.Dockerfile`)

NVIDIA PyTorch-based image with:
- CUDA 12.3 support
- NVIDIA Container Toolkit
- Common Python packages (FastAPI, PyTorch, etc.)
- GPU monitoring utilities
- Health check capabilities

**Building:**
```bash
docker build -t dgx-spark-base:latest -f shared/base.Dockerfile .
```

### 2. Configuration Schema (`config_schema.yaml`)

Unified YAML schema defining standard configuration structure for all agents:
- Playbook metadata
- Port mappings
- Volume mounts
- GPU requirements
- Resource limits
- Health checks
- Monitoring setup

**Usage:**
```python
from shared.utils import load_config, validate_config

config = load_config('agent_config.yaml')
if validate_config(config):
    print("Configuration valid!")
```

### 3. Health Check API (`health_check.py`)

Standardized health checking for services:
- HTTP endpoint checking
- System resource monitoring (CPU, memory, disk)
- GPU monitoring (if available)
- Prometheus-ready metrics

**CLI Usage:**
```bash
# Check service health
python3 shared/health_check.py --port 8080 --endpoint /health

# Show system health
python3 shared/health_check.py --system

# JSON output
python3 shared/health_check.py --system --json
```

**Python Usage:**
```python
from shared.health_check import HealthChecker

checker = HealthChecker()

# Check service
result = checker.check_service(port=8080, endpoint="/health")
print(f"Status: {result.status}")

# Get system metrics
health = checker.get_system_health()
print(f"CPU: {health['cpu']['usage_percent']}%")
```

### 4. Utilities (`utils/`)

#### Config Loader
```python
from shared.utils import ConfigLoader

loader = ConfigLoader('config.yaml')
config = loader.load()
value = loader.get('key.nested.path', default='default_value')
```

#### Logger
```python
from shared.utils import setup_logger

logger = setup_logger(
    name='my_agent',
    level='INFO',
    log_file='/app/logs/agent.log',
    format='json'
)

logger.info("Service started")
```

#### Metrics Collector
```python
from shared.utils import MetricsCollector

metrics = MetricsCollector(prefix='agent5')
metrics.update_system_metrics()
metrics.record_request('GET', '/api/models', 200, duration=0.05)
```

#### Docker Manager
```python
from shared.utils import DockerManager

docker = DockerManager()

# List containers
containers = docker.list_containers(all=True)

# Check GPU support
has_gpu = docker.check_gpu_support()

# Get container stats
stats = docker.get_container_stats('container_name')
```

## Integration

### In Docker Images

```dockerfile
FROM dgx-spark-base:latest

# Copy shared utilities
COPY shared/ /app/shared/

# Your application code
COPY my_app.py /app/

# Use shared health check
HEALTHCHECK CMD python3 /app/shared/health_check.py --self-check
```

### In Python Applications

```python
# Add to Python path
import sys
sys.path.insert(0, '/app/shared')

# Import utilities
from shared.health_check import HealthChecker
from shared.utils import setup_logger, MetricsCollector

# Use in your application
logger = setup_logger('my_app')
checker = HealthChecker()
metrics = MetricsCollector()
```

### In Ansible Playbooks

```yaml
- name: Deploy agent with shared components
  hosts: all
  vars_files:
    - ../shared/config_schema.yaml
  tasks:
    - name: Validate agent configuration
      command: python3 /path/to/shared/validate_config.py {{ agent_config }}
```

## Standards

All agents must:
1. Conform to `config_schema.yaml` structure
2. Use shared health check endpoints
3. Implement standard logging format
4. Export Prometheus metrics (if monitoring enabled)
5. Use shared base image (when applicable)

## Development

### Adding New Utilities

1. Create module in `shared/utils/`
2. Add exports to `shared/utils/__init__.py`
3. Update this documentation
4. Add unit tests in `tests/unit/`

### Updating Schema

1. Modify `shared/config_schema.yaml`
2. Update validation logic if needed
3. Update all agent configurations
4. Document breaking changes

## Testing

```bash
# Run shared component tests
pytest tests/unit/ -v

# Test with specific agent
pytest tests/integration/test_agent5_integration.py -v
```

## Version

Current version: 1.0.0

See CHANGELOG.md for version history.
