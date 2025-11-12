# DGX Spark Playbooks

Unified infrastructure automation and deployment system for NVIDIA DGX systems with standardized playbooks, shared components, and comprehensive agent ecosystem.

## 📖 Overview

This repository provides a complete infrastructure-as-code solution for deploying and managing AI/ML workloads on NVIDIA DGX systems. It includes:

- **Shared Components**: Reusable Docker images, configuration schemas, health checks, and utilities
- **Agent Ecosystem**: Modular deployment agents for different infrastructure components
- **Standardized Configuration**: Unified YAML schema for consistent deployments
- **Testing Framework**: Comprehensive unit and integration tests
- **Monitoring & Observability**: Built-in health checks, metrics, and logging

## 🏗️ Repository Structure

```
dgx-spark-playbooks/
├── agents/                          # Deployment agents
│   ├── agent5_inference/           # Inference engine (Ollama + NIM)
│   │   ├── api/                    # Model management API
│   │   ├── playbooks/              # Ansible playbooks
│   │   ├── scripts/                # Deployment scripts
│   │   ├── docker/                 # Docker configurations
│   │   ├── configs/                # Configuration files
│   │   ├── agent5_config.yaml      # Agent configuration
│   │   └── README.md
│   └── ...                         # Other agents (agent1-agent10)
│
├── shared/                          # Shared components
│   ├── base.Dockerfile             # Base Docker image
│   ├── config_schema.yaml          # Unified configuration schema
│   ├── health_check.py             # Health check API
│   ├── utils/                      # Shared utilities
│   │   ├── config_loader.py
│   │   ├── logger.py
│   │   ├── metrics.py
│   │   └── docker_utils.py
│   └── README.md
│
├── tests/                           # Test suite
│   ├── unit/                       # Unit tests
│   ├── integration/                # Integration tests
│   └── conftest.py                 # Pytest configuration
│
├── docker-compose.yml              # Main docker-compose file
├── requirements.txt                # Python dependencies
├── pytest.ini                      # Pytest configuration
├── .gitignore
└── README.md                       # This file
```

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd dgx-spark-playbooks
```

### 2. Build Shared Base Image (Optional)

```bash
docker build -t dgx-spark-base:latest -f shared/base.Dockerfile .
```

### 3. Deploy Agent 5 (Inference Engine)

```bash
# Configure environment
cp agents/agent5_inference/configs/agent5.env.example .env
nano .env  # Add your NGC_API_KEY and other settings

# Deploy with Docker Compose
docker-compose up -d

# Or use deployment script
./agents/agent5_inference/scripts/deploy.sh
```

### 4. Access Services

- **Open WebUI**: http://localhost:8080
- **Model Management API**: http://localhost:8888
- **API Documentation**: http://localhost:8888/docs
- **Ollama**: http://localhost:11434

## 📦 Available Agents

### Agent 5: Inference Engine ✅ (Implemented)

GPU-accelerated LLM inference with Ollama and NVIDIA NIM.

**Components:**
- Ollama for local model inference
- NVIDIA NIM for enterprise models
- Open WebUI for chat interface
- Unified model management API

**Quick Deploy:**
```bash
cd agents/agent5_inference
./scripts/deploy.sh
```

**Documentation:** [agents/agent5_inference/README.md](agents/agent5_inference/README.md)

### Other Agents (Coming Soon)

- **Agent 1**: Infrastructure Foundation
- **Agent 2**: Monitoring Dashboard
- **Agent 3**: Data Pipeline
- **Agent 4**: Training Orchestration
- **Agent 6**: Model Registry
- **Agent 7**: Experiment Tracking
- **Agent 8**: Deployment Gateway
- **Agent 9**: Security & Compliance
- **Agent 10**: Integration Hub

## 🔧 Shared Components

All agents use standardized shared components for consistency and maintainability.

### Base Docker Image

NVIDIA PyTorch-based image with CUDA, common dependencies, and monitoring tools.

```dockerfile
FROM dgx-spark-base:latest
# Your agent-specific configuration
```

### Configuration Schema

Unified YAML schema ensures all agents follow the same configuration structure:

```yaml
name: "my-agent"
agent_id: "agent1"
gpu_required: true
ports:
  - name: "api"
    container: 8080
    host: 8080
    protocol: "tcp"
# ... see shared/config_schema.yaml for complete spec
```

### Health Check API

Standardized health checking across all services:

```python
from shared.health_check import HealthChecker

checker = HealthChecker()
result = checker.check_service(port=8080, endpoint="/health")
system_health = checker.get_system_health()
```

### Utilities

- **Config Loader**: Load and validate YAML configurations
- **Logger**: Structured logging (text/JSON)
- **Metrics**: Prometheus-compatible metrics collection
- **Docker Manager**: Docker API wrapper for container management

See [shared/README.md](shared/README.md) for detailed documentation.

## 🧪 Testing

### Run All Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run specific test suite
pytest tests/unit/ -v
pytest tests/integration/ -v

# Run with coverage
pytest --cov=shared --cov=agents
```

### Run Agent-Specific Tests

```bash
# Test Agent 5
pytest tests/unit/test_agent5.py -v
pytest tests/integration/test_agent5_integration.py -v

# Skip slow tests
pytest -m "not slow"
```

## 📊 Monitoring & Observability

### Health Checks

All services expose health check endpoints:

```bash
# Check API health
curl http://localhost:8888/health

# Check Ollama
curl http://localhost:11434/api/tags

# Use shared health checker
python3 shared/health_check.py --port 8888
python3 shared/health_check.py --system
```

### Metrics

Prometheus-compatible metrics available at:
- Model API: http://localhost:9090/metrics (if enabled)

### Logs

Structured JSON logging to stdout:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "logger": "agent5",
  "message": "Service started",
  "module": "main"
}
```

## 🔒 Security

### Best Practices

1. **Environment Variables**: Never commit secrets (.env files are gitignored)
2. **NGC API Keys**: Required for NIM, store securely
3. **Network Isolation**: Services communicate via Docker networks
4. **User Permissions**: Containers run as non-root where possible
5. **Image Scanning**: Scan base images for vulnerabilities

### Securing Deployments

```yaml
# In agent configuration
security:
  run_as_user: "1000:1000"
  privileged: false
  cap_drop:
    - ALL
  read_only_root_fs: false
```

## 📝 Development

### Adding a New Agent

1. **Create agent directory:**
```bash
mkdir -p agents/agentN_name/{api,playbooks,scripts,docker,configs}
```

2. **Create agent configuration:**
```yaml
# agents/agentN_name/agentN_config.yaml
name: "agent-name"
agent_id: "agentN"
# ... follow shared/config_schema.yaml
```

3. **Implement components:**
   - API/services in `api/`
   - Ansible playbooks in `playbooks/`
   - Deployment scripts in `scripts/`
   - Docker configs in `docker/`

4. **Add tests:**
```python
# tests/unit/test_agentN.py
# tests/integration/test_agentN_integration.py
```

5. **Update documentation:**
   - Agent README
   - Main README (this file)

### Using Shared Components

```python
# In your agent's Python code
import sys
sys.path.insert(0, '/app/shared')

from shared.health_check import HealthChecker
from shared.utils import setup_logger, MetricsCollector

logger = setup_logger('agentN')
metrics = MetricsCollector(prefix='agentN')
```

### Configuration Validation

```bash
# Validate agent configuration
python3 -c "
from shared.utils import load_config, validate_config
config = load_config('agents/agentN/agentN_config.yaml')
assert validate_config(config), 'Invalid configuration'
print('Configuration valid!')
"
```

## 🐛 Troubleshooting

### Common Issues

**Docker Build Fails:**
```bash
# Check Docker version
docker --version  # Should be 20.10+

# Check NVIDIA Container Toolkit
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

**GPU Not Available:**
```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all ubuntu nvidia-smi
```

**Service Won't Start:**
```bash
# Check logs
docker-compose logs -f service-name

# Check health
python3 shared/health_check.py --port 8888

# Restart service
docker-compose restart service-name
```

**Port Already in Use:**
```bash
# Find process using port
lsof -i :8888

# Change port in .env file
echo "API_PORT=8889" >> .env
docker-compose up -d
```

### Getting Help

1. Check agent-specific README
2. Review shared component documentation
3. Check integration tests for usage examples
4. Open an issue with:
   - Agent name and version
   - Error messages and logs
   - System information (`nvidia-smi`, `docker info`)

## 📚 Documentation

- **Main README**: This file
- **Shared Components**: [shared/README.md](shared/README.md)
- **Agent 5 (Inference)**: [agents/agent5_inference/README.md](agents/agent5_inference/README.md)
- **Configuration Schema**: [shared/config_schema.yaml](shared/config_schema.yaml)
- **API Documentation**: http://localhost:8888/docs (when deployed)

## 🤝 Contributing

### Guidelines

1. Follow existing directory structure
2. Conform to configuration schema
3. Add comprehensive tests
4. Update documentation
5. Use shared components
6. Include health checks

### Pull Request Process

1. Create feature branch
2. Implement changes
3. Add/update tests
4. Update documentation
5. Submit PR with description

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM inference
- [NVIDIA NIM](https://www.nvidia.com/en-us/ai/) - Enterprise inference
- [Open WebUI](https://github.com/open-webui/open-webui) - Web interface

---

**Version**: 1.0.0
**Last Updated**: 2024
**Maintained by**: DGX Spark Team
