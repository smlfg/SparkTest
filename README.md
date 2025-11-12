# Agent 9: Application Layer

End-user applications and interfaces for the distributed AI infrastructure.

## Overview

Agent 9 provides production-ready application templates and deployment playbooks for building end-user AI applications. It integrates with Agent 4/5 (inference) and Agent 8 (multi-modal) to deliver complete, scalable solutions.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Agent 9: Application Layer                  │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   ComfyUI    │  │  RAG AI      │  │ Multi-Agent  │  │
│  │   :8188      │  │  Workbench   │  │   Chatbot    │  │
│  │              │  │   :3000      │  │    :8080     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐                     │
│  │   txt2kg     │  │     VSS      │                     │
│  │   :3001      │  │   :8081      │                     │
│  │              │  │              │                     │
│  └──────────────┘  └──────────────┘                     │
│                                                           │
└─────────────────────────────────────────────────────────┘
           │                    │                  │
           ▼                    ▼                  ▼
    ┌──────────┐         ┌──────────┐      ┌──────────┐
    │ Agent 4/5│         │ Agent 4/5│      │ Agent 8  │
    │Inference │         │Inference │      │Multi-modal│
    └──────────┘         └──────────┘      └──────────┘
```

## Applications

### 1. ComfyUI (Port 8188)

Advanced image generation interface with node-based workflow editor.

**Features:**
- Node-based workflow creation
- Text-to-image generation
- Image-to-image transformation
- Multiple model support
- Real-time preview
- Workflow templating

**Playbook:** `comfy-ui`

**Usage:**
```python
from playbooks.comfy_ui.deployment import ComfyUIClient

client = ComfyUIClient("http://localhost:8188")

# Generate an image
workflow = client.create_txt2img_workflow(
    prompt="A beautiful sunset over mountains, highly detailed, 4k",
    negative_prompt="blurry, low quality",
    width=512,
    height=512,
    steps=20
)

prompt_id = await client.queue_prompt(workflow)
image_bytes = await client.generate_image(prompt="...")
```

**Dependencies:** Agent 4/5 (inference), Agent 8 (multi-modal)

---

### 2. RAG AI Workbench (Port 3000)

Retrieval-Augmented Generation pipeline with vector search and document processing.

**Features:**
- Document ingestion and indexing
- Vector similarity search
- Context-aware generation
- Multiple embedding models
- Real-time query processing
- REST API interface

**Playbook:** `rag-ai-workbench`

**Usage:**
```python
from playbooks.rag_ai_workbench.application import RAGWorkbench

workbench = RAGWorkbench(agent_url="http://localhost:8000")

# Ingest documents
documents = [
    {"content": "Document text...", "metadata": {"source": "docs"}},
]
await workbench.ingest_documents(documents)

# Query
response = await workbench.query("What is Apache Spark?", top_k=3)
print(response.answer)
```

**Dependencies:** Agent 4/5 (inference)

---

### 3. Multi-Agent Chatbot (Port 8080)

Orchestrated multi-agent conversational system with specialized agents.

**Features:**
- Coordinator-based orchestration
- Specialized agent roles (Researcher, Analyst, Writer, Critic)
- Context-aware conversations
- Task decomposition
- Response synthesis
- Conversation history

**Playbook:** `multi-agent-chatbot`

**Agent Roles:**
- **Coordinator**: Orchestrates agent collaboration
- **Researcher**: Information gathering and synthesis
- **Analyst**: Data analysis and insights
- **Writer**: Content creation and editing
- **Critic**: Review and feedback

**Usage:**
```python
from playbooks.multi_agent_chatbot.orchestration import MultiAgentChatbot

chatbot = MultiAgentChatbot(llm_url="http://localhost:8000")

response = await chatbot.chat(
    user_input="Explain how Apache Spark works",
    conversation_id="conv_001",
    use_coordination=True
)
print(response['response'])
```

**Dependencies:** Agent 4/5 (inference)

---

### 4. txt2kg - Knowledge Graph Pipeline (Port 3001)

Text-to-Knowledge-Graph extraction and visualization.

**Features:**
- Named Entity Recognition (NER)
- Relationship extraction
- Graph construction
- Cytoscape.js visualization
- GraphViz export
- Multi-document processing

**Playbook:** `txt2kg`

**Usage:**
```python
from playbooks.txt2kg.pipeline import Text2KGPipeline

pipeline = Text2KGPipeline(agent_url="http://localhost:8000")

# Process text
kg = await pipeline.process_text("""
    Apache Spark is a unified analytics engine...
""")

# Get statistics
stats = kg.get_statistics()
print(f"Entities: {stats['num_entities']}")
print(f"Relationships: {stats['num_relationships']}")

# Export
from playbooks.txt2kg.pipeline import KnowledgeGraphVisualizer
visualizer = KnowledgeGraphVisualizer()
dot_format = visualizer.to_graphviz_dot(kg)
```

**Dependencies:** Agent 4/5 (inference)

---

### 5. VSS - Video Search + Summarization (Port 8081)

Video analysis tool with search and summarization capabilities.

**Features:**
- Frame extraction and analysis
- Audio transcription
- Semantic video search
- Automatic summarization
- Key moment detection
- Multi-modal indexing

**Playbook:** `vss`

**Usage:**
```python
from playbooks.vss.tool import VSSSystem

vss = VSSSystem(
    multimodal_url="http://localhost:8888",
    llm_url="http://localhost:8000"
)

# Ingest video
metadata = await vss.ingest_video("video.mp4", title="Tutorial Video")

# Generate summary
summary = await vss.generate_summary(metadata.video_id)
print(summary.overall_summary)

# Search
results = await vss.search("Apache Spark", search_type="transcript")
```

**Dependencies:** Agent 8 (multi-modal processing)

---

## Installation

### Prerequisites

- Python 3.8+
- Agent 4/5 inference services running
- Agent 8 multi-modal service running (for ComfyUI and VSS)

### Setup

```bash
# Clone repository
git clone <repository-url>
cd SparkTest

# Install dependencies
pip install -r requirements.txt

# Run application registry
python agent9_app_registry.py
```

## Application Registry

The central registry provides service discovery and health monitoring:

```python
from agent9_app_registry import get_registry

registry = get_registry()

# List all applications
apps = registry.list_applications()

# Get application URL
url = registry.get_app_url("rag_ui")

# Check health status
health = await registry.check_health("comfy_ui")

# Check all applications
all_health = await registry.check_all_health()
```

### Registry Output

```python
APPLICATIONS = {
    "comfy_ui": "http://localhost:8188",
    "rag_ui": "http://localhost:3000",
    "chatbot": "http://localhost:8080",
    "kg_viz": "http://localhost:3001"
}
```

## Deployment

### Docker Compose

Each playbook includes deployment configurations:

```bash
# ComfyUI deployment
cd playbooks/comfy_ui
docker-compose up -d

# RAG Workbench
cd playbooks/rag_ai_workbench
docker-compose up -d
```

### Kubernetes

Production deployments should use Kubernetes for orchestration:

```yaml
# Example deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: rag-workbench
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: rag-app
        image: agent9/rag-workbench:latest
        ports:
        - containerPort: 3000
        env:
        - name: AGENT_URL
          value: "http://agent4-service:8000"
```

## API Examples

### Health Check

```bash
curl http://localhost:3000/health
```

### RAG Query

```bash
curl -X POST http://localhost:3000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is Apache Spark?",
    "top_k": 3
  }'
```

### Multi-Agent Chat

```bash
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Explain distributed computing",
    "conversation_id": "conv_001"
  }'
```

## Configuration

### Environment Variables

```bash
# Agent 4/5 Inference URL
export AGENT_INFERENCE_URL="http://localhost:8000"

# Agent 8 Multi-modal URL
export AGENT_MULTIMODAL_URL="http://localhost:8888"

# Application ports
export COMFYUI_PORT=8188
export RAG_PORT=3000
export CHATBOT_PORT=8080
export KG_VIZ_PORT=3001
export VSS_PORT=8081
```

## Monitoring

All applications expose health endpoints:

- ComfyUI: `http://localhost:8188/system_stats`
- RAG Workbench: `http://localhost:3000/health`
- Chatbot: `http://localhost:8080/health`
- KG Viz: `http://localhost:3001/health`
- VSS: `http://localhost:8081/health`

## Development

### Running Playbook Demos

Each playbook includes a demo mode:

```bash
# ComfyUI demo
python playbooks/comfy_ui/deployment.py

# RAG Workbench demo
python playbooks/rag_ai_workbench/application.py

# Multi-Agent Chatbot demo
python playbooks/multi_agent_chatbot/orchestration.py

# txt2kg demo
python playbooks/txt2kg/pipeline.py

# VSS demo
python playbooks/vss/tool.py
```

### Testing

```bash
# Run all tests
pytest tests/

# Run specific playbook tests
pytest tests/test_rag_workbench.py
```

## Playbook Structure

Each playbook follows a standard structure:

```
playbooks/<playbook_name>/
├── __init__.py
├── <main_module>.py
├── docker-compose.yml (optional)
├── Dockerfile (optional)
└── README.md (optional)
```

## Troubleshooting

### Application won't start

1. Check that dependencies (Agent 4/5, Agent 8) are running
2. Verify port availability
3. Check logs for error messages

### Health check fails

```python
import asyncio
from agent9_app_registry import get_registry

async def diagnose():
    registry = get_registry()
    health = await registry.check_all_health()
    for app, status in health.items():
        print(f"{app}: {status.value}")

asyncio.run(diagnose())
```

### Performance issues

- Scale inference agents (Agent 4/5)
- Add caching layers
- Optimize batch sizes
- Use load balancing

## Dependencies

See `requirements.txt` for complete list:

- `aiohttp` - Async HTTP client
- `numpy` - Numerical computing
- `fastapi` - REST API framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation

## License

[Your License Here]

## Support

For issues and questions:
- GitHub Issues: [repository-url]/issues
- Documentation: [docs-url]

## Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

---

**Agent 9: Application Layer** - Building the future of AI applications
