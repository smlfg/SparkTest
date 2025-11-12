# Quick Start Guide - Agent 9: Application Layer

Get Agent 9 up and running in under 5 minutes!

## Prerequisites

- Docker with NVIDIA Container Toolkit
- Docker Compose v1.28+
- NVIDIA GPU (for ComfyUI and VSS)
- 32GB+ RAM recommended
- Agent 4/5 (inference services) running
- Agent 8 (multi-modal processing) running

## 1. Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd SparkTest

# Copy environment template
cp .env.example .env

# Edit configuration (optional)
vim .env
```

## 2. Start All Services

```bash
# Start everything with one command
docker-compose up -d

# View startup logs
docker-compose logs -f

# Wait for services to be healthy (2-3 minutes)
```

## 3. Verify Services

```bash
# Check health of all services
python shared/health_check.py --agent9

# Or check individual services
curl http://localhost:8188/system_stats  # ComfyUI
curl http://localhost:3000/health        # RAG Workbench
curl http://localhost:8080/health        # Chatbot
curl http://localhost:3001/health        # txt2kg
curl http://localhost:8081/health        # VSS
```

## 4. Access Applications

### ComfyUI - Image Generation
```
URL: http://localhost:8188
Description: Advanced image generation with node-based workflows
Try: Create a workflow and generate images
```

### RAG Workbench - Question Answering
```
URL: http://localhost:3000
Description: Retrieval-Augmented Generation system
Try: POST to /api/query with a question
```

### Multi-Agent Chatbot
```
URL: http://localhost:8080
Description: Orchestrated multi-agent conversations
Try: POST to /api/chat with a message
```

### Knowledge Graph Visualizer
```
URL: http://localhost:3001
Description: Text to knowledge graph extraction
Try: POST text to /api/process
```

### Video Search & Summarization
```
URL: http://localhost:8081
Description: Video analysis and search
Try: POST video to /api/ingest
```

### Monitoring
```
Prometheus: http://localhost:9090
Grafana: http://localhost:3002
  Username: admin
  Password: admin
```

## 5. Test Drive

### Example 1: RAG Query

```bash
curl -X POST http://localhost:3000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Apache Spark?",
    "top_k": 3
  }'
```

### Example 2: Multi-Agent Chat

```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain distributed computing",
    "conversation_id": "test_001"
  }'
```

### Example 3: Knowledge Graph Extraction

```bash
curl -X POST http://localhost:3001/api/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Apache Spark is a unified analytics engine..."
  }'
```

### Example 4: ComfyUI Image Generation

```python
from playbooks.comfy_ui.deployment import ComfyUIClient

client = ComfyUIClient("http://localhost:8188")

workflow = client.create_txt2img_workflow(
    prompt="Beautiful sunset over mountains, 4k",
    width=512,
    height=512
)

prompt_id = await client.queue_prompt(workflow)
print(f"Queued: {prompt_id}")
```

## 6. Explore Demos

Each playbook includes a standalone demo:

```bash
# ComfyUI demo
python playbooks/comfy_ui/deployment.py

# RAG Workbench demo
python playbooks/rag_ai_workbench/application.py

# Multi-Agent Chatbot demo
python playbooks/multi_agent_chatbot/orchestration.py

# Knowledge Graph demo
python playbooks/txt2kg/pipeline.py

# Video Analysis demo
python playbooks/vss/tool.py
```

## 7. Project Structure

```
SparkTest/
│
├── agent9_app_registry.py       # Central service registry
│
├── shared/                      # Shared infrastructure
│   ├── base.Dockerfile          # Base Docker image
│   ├── config_schema.yaml       # Config standard
│   ├── health_check.py          # Health API
│   └── utils/                   # Utilities
│       ├── config_loader.py
│       └── logger.py
│
├── playbooks/                   # Agent 9 Applications
│   ├── comfy_ui/               # Image generation
│   │   ├── deployment.py
│   │   └── config.yaml
│   ├── rag_ai_workbench/       # RAG pipeline
│   │   ├── application.py
│   │   └── config.yaml
│   ├── multi_agent_chatbot/    # Multi-agent system
│   │   ├── orchestration.py
│   │   └── config.yaml
│   ├── txt2kg/                 # Knowledge graphs
│   │   ├── pipeline.py
│   │   └── config.yaml
│   └── vss/                    # Video analysis
│       ├── tool.py
│       └── config.yaml
│
├── monitoring/                  # Observability
│   ├── prometheus.yml          # Metrics collection
│   └── grafana/                # Dashboards
│
├── tests/                       # Test suites
│   ├── unit/
│   └── integration/
│
├── docker-compose.yml           # Orchestration
├── .env.example                 # Configuration template
├── requirements.txt             # Python dependencies
│
├── README.md                    # Full documentation
├── SHARED_INTERFACES.md         # Interface specs
└── QUICKSTART.md               # This file
```

## 8. Common Operations

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f comfy-ui
docker-compose logs -f rag-workbench

# Last 100 lines
docker-compose logs --tail=100 chatbot
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart comfy-ui

# Restart with rebuild
docker-compose up -d --build comfy-ui
```

### Scale Services

```bash
# Scale RAG Workbench to 3 instances
docker-compose up -d --scale rag-workbench=3

# Scale Chatbot to 5 instances
docker-compose up -d --scale multi-agent-chatbot=5
```

### Stop Services

```bash
# Stop all
docker-compose down

# Stop but keep volumes
docker-compose down --volumes=false

# Stop and remove everything
docker-compose down -v --remove-orphans
```

## 9. Development Mode

### Run Services Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export AGENT_INFERENCE_URL=http://localhost:8000
export AGENT_MULTIMODAL_URL=http://localhost:8888

# Run a service
cd playbooks/rag_ai_workbench
python application.py
```

### Run Tests

```bash
# All tests
pytest tests/

# With coverage
pytest --cov=shared --cov=playbooks tests/

# Specific test
pytest tests/unit/test_health.py -v
```

### Build Custom Images

```bash
# Build base image
docker build -f shared/base.Dockerfile -t dgx-spark/base:latest .

# Build service image
docker build -t dgx-spark/comfy-ui:latest \
  --build-arg BASE_IMAGE=dgx-spark/base:latest \
  -f playbooks/comfy_ui/Dockerfile .
```

## 10. Monitoring & Debugging

### Check Service Health

```bash
# Quick check
python shared/health_check.py --agent9

# Detailed check with JSON
python shared/health_check.py --port 8188 --json

# Check from Python
python -c "
import asyncio
from shared.health_check import check_agent9_services
asyncio.run(check_agent9_services())
"
```

### View Metrics

```bash
# Prometheus metrics
curl http://localhost:8188/metrics  # ComfyUI
curl http://localhost:3000/metrics  # RAG Workbench
curl http://localhost:8080/metrics  # Chatbot

# Prometheus UI
open http://localhost:9090

# Grafana Dashboards
open http://localhost:3002
```

### Debug Container

```bash
# Enter running container
docker-compose exec comfy-ui bash

# Check logs
docker-compose logs --tail=100 -f comfy-ui

# Inspect container
docker inspect agent9-comfy-ui

# Check resource usage
docker stats agent9-comfy-ui
```

## 11. Configuration

### Environment Variables

Edit `.env` file:

```bash
# Infrastructure URLs
AGENT_INFERENCE_URL=http://agent4:8000
AGENT_MULTIMODAL_URL=http://agent8:8888

# Model Configuration
LLM_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-ada-002

# Service Ports
COMFYUI_PORT=8188
RAG_WORKBENCH_PORT=3000

# Resources
COMFYUI_MEMORY=16G
RAG_MEMORY=8G

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Playbook Configuration

Each playbook has a `config.yaml`:

```bash
# View configuration
cat playbooks/comfy_ui/config.yaml

# Validate configuration
python -c "
from shared.utils.config_loader import ConfigLoader
loader = ConfigLoader()
config = loader.load_config('playbooks/comfy_ui/config.yaml')
print('Configuration is valid!')
"
```

## 12. Troubleshooting

### Services won't start

```bash
# Check Docker
docker --version
docker-compose --version

# Check GPU
nvidia-smi

# Check ports
netstat -tulpn | grep -E '8188|3000|8080|3001|8081'

# Check logs
docker-compose logs
```

### Health checks fail

```bash
# Wait longer (services need 60-90s to start)
sleep 60
python shared/health_check.py --agent9

# Check dependencies
curl http://agent4:8000/health
curl http://agent8:8888/health
```

### Out of memory

```bash
# Reduce replicas
docker-compose up -d --scale rag-workbench=1

# Adjust memory limits in docker-compose.yml
vim docker-compose.yml
# Change: memory: "8G" to memory: "4G"

# Restart services
docker-compose restart
```

### GPU not available

```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:12.3.0-base-ubuntu22.04 nvidia-smi

# Check container GPU access
docker-compose exec comfy-ui nvidia-smi
```

## 13. Next Steps

1. **Explore Documentation**
   - Read [README.md](README.md) for detailed information
   - Check [SHARED_INTERFACES.md](SHARED_INTERFACES.md) for architecture

2. **Customize Applications**
   - Modify playbook code in `playbooks/`
   - Update configurations in `config.yaml` files
   - Add custom models and data

3. **Integrate with Your Stack**
   - Connect Agent 4/5 for inference
   - Connect Agent 8 for multi-modal processing
   - Add your own data sources

4. **Deploy to Production**
   - Set up Kubernetes deployment
   - Configure authentication and TLS
   - Set up backup and monitoring

5. **Contribute**
   - Add new playbooks
   - Improve existing features
   - Submit pull requests

## Support

- Documentation: `README.md`, `SHARED_INTERFACES.md`
- Health Check: `python shared/health_check.py --agent9`
- Logs: `docker-compose logs -f`
- Issues: GitHub Issues

---

**You're all set!** Start exploring Agent 9 applications and building amazing AI-powered tools! 🚀
