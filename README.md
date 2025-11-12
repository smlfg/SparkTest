# DGX Spark Playbooks

**Multi-Agent Development and Deployment System**

A comprehensive infrastructure automation system featuring shared base images, unified configuration, health monitoring, and modular agent architecture.

## 🏗️ Architecture

### Shared Infrastructure

All agents build on common foundation:
- **Base Docker Image** - NVIDIA PyTorch with CUDA support
- **Unified Config Schema** - Standardized YAML configuration
- **Health Check API** - Service monitoring and validation
- **Common Utilities** - Logging, config loading, Docker ops

### Agent System

```
agents/
├── agent1_infra/           # Infrastructure (planned)
├── agent2_dashboard/       # Dashboard (planned)
├── agent3_dev_environments # ✅ Development Environments (implemented)
├── agent4_compute/         # Compute (planned)
├── agent5_storage/         # Storage (planned)
├── agent6_networking/      # Networking (planned)
├── agent7_security/        # Security (planned)
├── agent8_monitoring/      # Monitoring (planned)
├── agent9_backup/          # Backup (planned)
└── agent10_integration/    # Integration (planned)
```

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- NVIDIA Docker runtime (for GPU support)
- Python 3.11+
- 16GB+ RAM recommended

### Installation

```bash
# Clone repository
git clone https://github.com/smlfg/SparkTest.git
cd SparkTest

# Build shared base image
docker-compose build base

# Launch Agent 3 (Development Environments)
cd agents/agent3_dev_environments
./agent3_launch.sh all
```

## 📦 Agent 3: Development Environments (Implemented)

**Status**: ✅ Production Ready

### Features

- **VS Code Remote Server** - Web-based IDE (port 8443)
- **JAX ARM64 Container** - ML environment with Jupyter (port 8888)
- **Dev Templates** - Python, Rust, Go, C++ configurations
- **Launch Scripts** - Automated setup and management

### Usage

```bash
# From project root
cd agents/agent3_dev_environments

# Setup complete environment
./agent3_launch.sh all

# Individual components
./agent3_launch.sh vscode    # VS Code Server
./agent3_launch.sh jax       # JAX Container

# Check status
./agent3_launch.sh status
```

### Interface Output

```bash
# agent3_launch.sh
start_vscode_server --port 8443
launch_jax_container --gpus all
```

### Access Points

- **VS Code**: http://localhost:8443 (password: changeme123)
- **Jupyter Lab**: http://localhost:8888 (token: jaxdev123)
- **TensorBoard**: http://localhost:6006

[Full Agent 3 Documentation →](agents/agent3_dev_environments/README.md)

## 🛠️ Shared Infrastructure

### 1. Docker Base Image

```dockerfile
FROM nvcr.io/nvidia/pytorch:24.10-py3
RUN apt-get update && apt-get install -y \
    nvidia-container-toolkit \
    cuda-toolkit-12-0
```

**Build:**
```bash
docker build -f shared/base.Dockerfile -t dgx-spark-base:latest .
```

**Usage in Agents:**
```dockerfile
FROM dgx-spark-base:latest
# Your agent-specific configuration
```

### 2. Unified Config Schema

Standard YAML format for all playbooks:

```yaml
# Example: agent3/config.yaml
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

[Full Schema Documentation →](shared/config_schema.yaml)

### 3. Health Check API

```python
from shared import check_service, wait_for_service

# Quick health check
if check_service(port=8888, endpoint="/health"):
    print("Service is healthy")

# Wait for service to be ready
wait_for_service(port=8888, timeout=60)
```

**CLI Usage:**
```bash
# Check service
python shared/health_check.py 8888 --endpoint /health

# Wait for service
python shared/health_check.py 8888 --wait --wait-timeout 60

# JSON output
python shared/health_check.py 8888 --json
```

### 4. Common Utilities

```python
# Configuration loading
from shared.utils import load_config, validate_config
config = load_config("config.yaml")
validate_config(config)

# Logging
from shared.utils import setup_logger
logger = setup_logger("agent3", level="INFO")

# Docker operations
from shared.utils import check_docker, is_container_running
if check_docker():
    if is_container_running("agent3-jax-dev"):
        print("Container running")
```

[Full Utilities Documentation →](shared/README.md)

## 📂 Project Structure

```
dgx-spark-playbooks/
├── agents/                       # Agent implementations
│   ├── agent1_infra/
│   ├── agent2_dashboard/
│   └── agent3_dev_environments/  # ✅ Implemented
│       ├── agent3_launch.sh     # Main launcher
│       ├── playbooks/           # Ansible + Shell scripts
│       ├── containers/          # Docker configs
│       └── templates/           # Dev environment templates
├── shared/                       # Shared infrastructure
│   ├── base.Dockerfile          # Base Docker image
│   ├── config_schema.yaml       # Unified config format
│   ├── health_check.py          # Health monitoring API
│   └── utils/                   # Common utilities
│       ├── config_loader.py
│       ├── logger.py
│       └── docker_utils.py
├── tests/                        # Test suite
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── docker-compose.yml            # Root orchestration
├── README.md                     # This file
├── CONTRIBUTING.md               # Contribution guidelines
└── requirements.txt              # Python dependencies
```

## 🐳 Docker Compose

Orchestrate all agents from root:

```bash
# Build base image
docker-compose build base

# Launch all services
docker-compose up -d

# Launch specific agent
docker-compose up -d agent3-jax

# View logs
docker-compose logs -f agent3-jax

# Stop all
docker-compose down
```

### Available Services

- `base` - Base image build
- `agent3-jax` - JAX development container
- `tensorboard` - TensorBoard visualization
- `health-monitor` - Health check monitoring

[Full Docker Compose Config →](docker-compose.yml)

## 🧪 Testing

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/

# Run specific test suite
pytest tests/unit/              # Unit tests
pytest tests/integration/       # Integration tests

# Run with coverage
pytest tests/ --cov=shared --cov-report=html

# Run specific tests
pytest tests/unit/test_health_check.py
pytest tests/integration/test_agent3.py
```

## 🔧 Development

### Adding a New Agent

1. **Create agent directory**
   ```bash
   mkdir -p agents/agentN_name
   cd agents/agentN_name
   ```

2. **Create agent structure**
   ```bash
   mkdir -p playbooks containers templates scripts
   touch README.md
   ```

3. **Extend base image**
   ```dockerfile
   FROM dgx-spark-base:latest
   # Agent-specific configuration
   ```

4. **Follow config schema**
   ```yaml
   # config.yaml
   name: "agent-playbook"
   agent: "agentN"
   version: "1.0.0"
   ```

5. **Implement health check**
   ```python
   from shared import HealthStatus
   # Return health status
   ```

6. **Add to docker-compose.yml**
   ```yaml
   agentN-service:
     build: agents/agentN_name
     # ...
   ```

7. **Write tests**
   ```bash
   pytest tests/unit/test_agentN.py
   pytest tests/integration/test_agentN.py
   ```

### Development Workflow

1. Fork repository
2. Create feature branch
3. Implement changes
4. Write/update tests
5. Update documentation
6. Submit pull request

[Contributing Guide →](CONTRIBUTING.md)

## 🎯 Roadmap

### Phase 1: Foundation (Current)
- [x] Shared infrastructure
- [x] Base Docker image
- [x] Configuration schema
- [x] Health check API
- [x] Agent 3 implementation

### Phase 2: Core Agents (Next)
- [ ] Agent 1: Infrastructure setup
- [ ] Agent 2: Monitoring dashboard
- [ ] Agent 4: Compute orchestration

### Phase 3: Advanced Features
- [ ] Multi-node deployment
- [ ] Auto-scaling
- [ ] CI/CD integration
- [ ] Observability stack

### Phase 4: Enterprise Features
- [ ] RBAC and security
- [ ] Multi-tenancy
- [ ] Disaster recovery
- [ ] Cost optimization

## 📊 System Requirements

### Minimum
- CPU: 4 cores
- RAM: 8GB
- Disk: 50GB
- OS: Ubuntu 22.04 / Debian 11

### Recommended
- CPU: 16+ cores
- RAM: 64GB+
- Disk: 500GB+ NVMe
- GPU: NVIDIA A100 / H100
- OS: Ubuntu 22.04 LTS

### Software
- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker runtime
- Python 3.11+
- CUDA 12.0+

## 🔐 Security

- Non-root containers by default
- Minimal base images
- Security scanning with Trivy
- Secret management with Docker secrets
- Network isolation
- Read-only root filesystems where applicable

## 📖 Documentation

- [Shared Infrastructure](shared/README.md)
- [Agent 3: Development Environments](agents/agent3_dev_environments/README.md)
- [Configuration Schema](shared/config_schema.yaml)
- [Health Check API](shared/health_check.py)
- [Contributing Guide](CONTRIBUTING.md)
- [Testing Guide](tests/README.md)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:

- Code of conduct
- Development setup
- Coding standards
- Pull request process
- Testing requirements

## 📝 License

[To be determined]

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/smlfg/SparkTest/issues)
- **Discussions**: [GitHub Discussions](https://github.com/smlfg/SparkTest/discussions)
- **Documentation**: [Project Wiki](https://github.com/smlfg/SparkTest/wiki)

## 📈 Status

| Agent | Status | Coverage | Documentation |
|-------|--------|----------|---------------|
| Shared Infrastructure | ✅ Complete | 85% | ✅ Complete |
| Agent 1: Infrastructure | 📋 Planned | - | 📋 Planned |
| Agent 2: Dashboard | 📋 Planned | - | 📋 Planned |
| Agent 3: Dev Environments | ✅ Complete | 90% | ✅ Complete |
| Agent 4-10 | 📋 Planned | - | 📋 Planned |

## 🎉 Acknowledgments

Built with:
- NVIDIA PyTorch
- Docker & Docker Compose
- Python ecosystem
- JAX, FastAPI, Pytest

---

**DGX Spark Playbooks** - Enterprise-grade multi-agent infrastructure automation

[Get Started](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)
