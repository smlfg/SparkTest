# DGX Spark Playbooks

A comprehensive multi-agent system for managing NVIDIA DGX infrastructure with GPU-accelerated computing capabilities.

## Overview

This project provides a distributed architecture of 10 specialized agents, each handling specific aspects of DGX infrastructure management. All agents share common interfaces, health check mechanisms, and configuration schemas for seamless integration and orchestration.

## Architecture

```
dgx-spark-playbooks/
├── agents/              # 10 specialized agents
│   ├── agent1_infra/
│   ├── agent2_dashboard/
│   ├── agent3_compute/
│   ├── agent4_storage/
│   ├── agent5_networking/
│   ├── agent6_monitoring/
│   ├── agent7_security/
│   ├── agent8_analytics/
│   ├── agent9_orchestration/
│   └── agent10_integration/
├── shared/              # Shared interfaces and utilities
│   ├── base.Dockerfile
│   ├── config_schema.yaml
│   ├── health_check.py
│   └── utils/
├── tests/               # Test suite
│   ├── unit/
│   └── integration/
├── docker-compose.yml   # Orchestration configuration
└── README.md
```

## Agents

### Agent 1: Infrastructure Management (Port 8001)
Handles resource allocation and infrastructure monitoring.

### Agent 2: Dashboard and Visualization (Port 8002)
Provides visualization and dashboard interfaces.

### Agent 3: Distributed Compute Orchestration (Port 8003)
Manages distributed compute workloads.

### Agent 4: Data Storage and Management (Port 8004)
Handles data storage, retrieval, and management.

### Agent 5: Network Configuration and Routing (Port 8005)
Manages network configuration and traffic routing.

### Agent 6: System Monitoring and Metrics (Port 8006)
Collects and reports system metrics and monitoring data.

### Agent 7: Security and Access Control (Port 8007)
Manages security policies and access control.

### Agent 8: Data Analytics and Processing (Port 8008)
Performs data analytics and processing tasks.

### Agent 9: Workflow Orchestration (Port 8009)
Orchestrates complex workflows across agents.

### Agent 10: External Systems Integration (Port 8010)
Integrates with external systems and APIs.

## Shared Interfaces

### 1. Docker Base Image
All agents use a common base image with NVIDIA PyTorch and CUDA toolkit:
```dockerfile
FROM nvcr.io/nvidia/pytorch:24.10-py3
```

### 2. Unified Configuration Schema
All agents follow a standardized configuration format defined in `shared/config_schema.yaml`:
```yaml
playbook:
  name: str
  version: str
  description: str
  dependencies: list[str]
  ports: list[int]
  volumes: list[str]
  gpu_required: bool
  gpu_count: int
  resources:
    memory: str
    cpus: float
  environment: dict
  health_check:
    endpoint: str
    interval: int
    timeout: int
    retries: int
```

### 3. Health Check API
Standardized health check functionality via `shared/health_check.py`:
```python
check_service(port, endpoint, timeout, host)
check_service_detailed(port, endpoint, timeout, host)
check_multiple_services(services)
wait_for_service(port, max_attempts, delay)
```

## Quick Start

### Prerequisites
- Docker with GPU support (NVIDIA Container Toolkit)
- NVIDIA GPU with CUDA 12.0+
- Docker Compose v3.8+
- Python 3.10+ (for local development)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd dgx-spark-playbooks
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Build and start all agents:
```bash
docker-compose up -d --build
```

4. Check agent health:
```bash
# Check all agents
for port in {8001..8010}; do
  curl http://localhost:$port/health
done
```

### Running Individual Agents

#### Using Docker
```bash
# Build a specific agent
docker build -t agent1_infra -f agents/agent1_infra/Dockerfile .

# Run with GPU support
docker run -p 8001:8001 --gpus all agent1_infra
```

#### Using Docker Compose
```bash
# Start a specific agent
docker-compose up agent1_infra

# Start multiple agents
docker-compose up agent1_infra agent2_dashboard
```

#### Local Development
```bash
# Navigate to agent directory
cd agents/agent1_infra

# Run the agent
CONFIG_PATH=config.yaml python main.py
```

## Configuration

Each agent has a `config.yaml` file that follows the shared schema. Example:

```yaml
playbook:
  name: "agent1_infra"
  version: "1.0.0"
  description: "Infrastructure management agent"
  dependencies: []
  ports: [8001]
  volumes:
    - "./agents/agent1_infra/data:/app/data"
    - "./shared:/app/shared"
  gpu_required: true
  gpu_count: 1
  resources:
    memory: "8g"
    cpus: 4.0
  environment:
    LOG_LEVEL: "INFO"
    ENVIRONMENT: "production"
  health_check:
    endpoint: "/health"
    interval: 30
    timeout: 10
    retries: 3
```

## API Endpoints

All agents expose the following standard endpoints:

### Health Check
```
GET /health
```
Returns agent health status.

### Root
```
GET /
```
Returns agent information and available endpoints.

### Information
```
GET /info
```
Returns agent configuration details.

### Status
```
GET /status
```
Returns agent status and resource usage.

## Testing

### Unit Tests
```bash
# Run unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=shared --cov-report=html
```

### Integration Tests
```bash
# Start all agents first
docker-compose up -d

# Run integration tests
pytest tests/integration/ -v -m integration

# Check health of all agents
pytest tests/integration/test_agent_health.py -v
```

### Test Specific Agent
```bash
pytest tests/integration/test_agent_health.py::test_agent_health_endpoint[agent1_infra] -v
```

## Development

### Adding a New Agent

1. Create agent directory:
```bash
mkdir -p agents/agent11_new_feature
```

2. Create configuration file:
```bash
cp agents/agent1_infra/config.yaml agents/agent11_new_feature/config.yaml
# Edit config.yaml with new agent details
```

3. Create main.py and Dockerfile:
```bash
cp agents/agent1_infra/main.py agents/agent11_new_feature/
cp agents/agent1_infra/Dockerfile agents/agent11_new_feature/
# Customize as needed
```

4. Add to docker-compose.yml:
```yaml
agent11_new_feature:
  build:
    context: .
    dockerfile: agents/agent11_new_feature/Dockerfile
  ports:
    - "8011:8011"
  # ... rest of configuration
```

### Code Quality

```bash
# Format code
black shared/ agents/

# Lint code
flake8 shared/ agents/

# Type checking
mypy shared/ agents/

# Sort imports
isort shared/ agents/
```

## Monitoring

### Health Check All Agents
```bash
# Using shared health check utility
python -c "
from shared.health_check import check_multiple_services
services = {f'agent{i}': {'port': 8000+i} for i in range(1, 11)}
results = check_multiple_services(services)
for agent, healthy in results.items():
    print(f'{agent}: {'✓' if healthy else '✗'}')
"
```

### View Logs
```bash
# All agents
docker-compose logs -f

# Specific agent
docker-compose logs -f agent1_infra

# With timestamps
docker-compose logs -f -t agent1_infra
```

### Resource Usage
```bash
# Check container stats
docker stats

# Check GPU usage
nvidia-smi

# Check specific agent
docker stats agent1_infra
```

## Troubleshooting

### Agent Not Starting
```bash
# Check logs
docker-compose logs agent1_infra

# Verify GPU access
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Rebuild without cache
docker-compose build --no-cache agent1_infra
```

### Port Conflicts
```bash
# Check which process is using a port
lsof -i :8001

# Change port in config.yaml and docker-compose.yml
```

### GPU Not Available
```bash
# Verify NVIDIA Container Toolkit installation
nvidia-container-cli info

# Restart Docker daemon
sudo systemctl restart docker

# Check GPU availability
nvidia-smi
```

## Performance Optimization

### GPU Memory Management
- Adjust `CUDA_VISIBLE_DEVICES` to allocate specific GPUs
- Set memory limits in docker-compose.yml
- Monitor GPU usage with `nvidia-smi`

### Container Resources
- Adjust CPU and memory limits in docker-compose.yml
- Use resource reservations for critical agents
- Monitor container stats with `docker stats`

### Network Performance
- Use host network mode for low-latency requirements
- Configure bridge network settings in docker-compose.yml
- Monitor network traffic with `docker network inspect`

## Security Considerations

### Best Practices
- Use read-only volumes where possible
- Implement authentication for production deployments
- Use secrets management for sensitive data
- Regular security updates for base images
- Network isolation between agents

### Environment Variables
Never commit sensitive data. Use `.env` files or secrets management:
```bash
# Create .env file (gitignored)
echo "API_KEY=your_secret_key" > .env

# Reference in docker-compose.yml
environment:
  - API_KEY=${API_KEY}
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[Specify your license here]

## Support

For issues and questions:
- Create an issue in the repository
- Check existing documentation in `agents/*/README.md`
- Review shared interface documentation in `shared/`

## Acknowledgments

Built on:
- NVIDIA PyTorch Container (24.10)
- FastAPI
- Docker with GPU support
- CUDA Toolkit 12.0

---

**Version:** 1.0.0
**Last Updated:** 2025-11-12
