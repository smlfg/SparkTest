# Agent 5: Inference Engine

GPU-accelerated LLM inference using Ollama, NVIDIA NIM, and Open WebUI.

## Components

- **Ollama**: Local GPU-accelerated model inference
- **Open WebUI**: Web-based chat interface
- **NVIDIA NIM**: Enterprise-grade inference microservices
- **Model Management API**: Unified API for all inference backends

## Quick Start

See parent README.md for deployment instructions.

## Configuration

Configuration file: `agent5_config.yaml`

## Structure

```
agent5_inference/
├── api/                    # Model Management API
├── playbooks/             # Ansible deployment playbooks
├── scripts/               # Deployment and management scripts
├── docker/                # Docker configurations
├── configs/               # Configuration files
├── agent5_config.yaml     # Agent configuration
└── README.md             # This file
```

## Models

### Ollama Models
- llama3.1:70b
- mistral:7b
- codellama:13b
- neural-chat:7b
- mixtral:8x7b

### NIM Models
- llama-3.1-405b-instruct
- llama-3.1-70b-instruct
- llama-3.1-8b-instruct

## API Endpoints

- `GET /health` - Health check
- `GET /api/models` - List models
- `POST /api/completion` - Text completion
- `POST /api/chat` - Chat completion

See main documentation for detailed usage.
