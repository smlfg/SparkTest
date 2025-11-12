# API Reference

**GPU Training Platform - Complete API Documentation**

This document aggregates API information from all platform agents (Agent 1-6) providing a complete reference for programmatic access to the platform.

**Version**: 1.0
**Last Updated**: January 12, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Agent 1: Multi-Node Orchestration](#agent-1-multi-node-orchestration)
4. [Agent 2: Web Dashboard](#agent-2-web-dashboard)
5. [Agent 3: Training Orchestration](#agent-3-training-orchestration)
6. [Agent 4: Notebooks & Testing](#agent-4-notebooks--testing)
7. [Agent 5: Inference](#agent-5-inference)
8. [Agent 6: Documentation](#agent-6-documentation)
9. [WebSocket APIs](#websocket-apis)
10. [Error Handling](#error-handling)
11. [Rate Limits](#rate-limits)
12. [Python Client Library](#python-client-library)

---

## Overview

### Base URLs

```
Agent 1 (Multi-node):  http://platform-hostname:8001/api/v1
Agent 2 (Dashboard):   http://platform-hostname:8002/api/v1
Agent 3 (Training):    http://platform-hostname:8003/api/v1
Agent 4 (Notebooks):   http://platform-hostname:8004/api/v1
Agent 5 (Inference):   http://platform-hostname:8005/api/v1
Agent 6 (Docs):        http://platform-hostname:11000/docs
```

### Common Headers

```http
Content-Type: application/json
Authorization: Bearer <your-api-token>
X-API-Version: 1.0
```

### Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "metadata": {
    "timestamp": "2025-01-12T10:30:00Z",
    "request_id": "req-123456",
    "api_version": "1.0"
  }
}
```

**Error response**:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Dataset not found",
    "details": {...}
  },
  "metadata": {...}
}
```

---

## Authentication

### Obtain API Token

```http
POST /auth/token
Content-Type: application/json

{
  "username": "your-username",
  "password": "your-password"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "Bearer",
    "expires_in": 3600
  }
}
```

### Refresh Token

```http
POST /auth/refresh
Authorization: Bearer <refresh-token>
```

### Using API Tokens

Include in all requests:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Agent 1: Multi-Node Orchestration

**Base URL**: `http://platform-hostname:8001/api/v1`

### Discover Nodes

Get list of available compute nodes.

```http
GET /nodes/discover
```

**Response**:
```json
{
  "success": true,
  "data": {
    "nodes": [
      {
        "node_id": "node-001",
        "hostname": "gpu-node-1",
        "status": "available",
        "gpus": 8,
        "gpu_type": "A100",
        "memory_total": "640GB",
        "memory_available": "640GB"
      },
      {
        "node_id": "node-002",
        "hostname": "gpu-node-2",
        "status": "available",
        "gpus": 8,
        "gpu_type": "A100",
        "memory_total": "640GB",
        "memory_available": "320GB"
      }
    ],
    "total_nodes": 2,
    "total_gpus": 16
  }
}
```

### Register Training Job

Register a distributed training job across multiple nodes.

```http
POST /jobs/register
Content-Type: application/json

{
  "job_id": "job-12345",
  "agent": "agent3",
  "num_nodes": 2,
  "gpus_per_node": 4,
  "config": {
    "model": "llama-7b",
    "dataset": "my-dataset"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "job_id": "job-12345",
    "nodes": ["node-001", "node-002"],
    "master_addr": "192.168.1.100",
    "master_port": 29500,
    "status": "registered"
  }
}
```

### Get Node Status

```http
GET /nodes/{node_id}/status
```

**Response**:
```json
{
  "success": true,
  "data": {
    "node_id": "node-001",
    "status": "busy",
    "current_job": "job-12345",
    "gpu_utilization": [95, 94, 96, 95, 0, 0, 0, 0],
    "memory_usage": [38, 38, 38, 38, 0, 0, 0, 0]
  }
}
```

### Synchronize Checkpoint

Sync checkpoint across nodes.

```http
POST /checkpoints/sync
Content-Type: application/json

{
  "checkpoint_path": "/workspace/checkpoints/model-1000",
  "node_ids": ["node-001", "node-002"]
}
```

---

## Agent 2: Web Dashboard

**Base URL**: `http://platform-hostname:8002/api/v1`

### List Datasets

```http
GET /datasets?page=1&limit=20&type=chat
```

**Response**:
```json
{
  "success": true,
  "data": {
    "datasets": [
      {
        "dataset_id": "ds-001",
        "name": "customer-support-chat",
        "type": "chat",
        "size": "2.5MB",
        "num_examples": 1000,
        "created_at": "2025-01-10T12:00:00Z",
        "status": "ready"
      }
    ],
    "total": 42,
    "page": 1,
    "pages": 3
  }
}
```

### Upload Dataset

```http
POST /datasets/upload
Content-Type: multipart/form-data

file: <file-data>
name: "my-dataset"
description: "Training data for chatbot"
type: "chat"
```

**Response**:
```json
{
  "success": true,
  "data": {
    "dataset_id": "ds-042",
    "status": "processing",
    "upload_id": "upload-789"
  }
}
```

### Get Dataset Status

```http
GET /datasets/{dataset_id}
```

### Delete Dataset

```http
DELETE /datasets/{dataset_id}
```

### List Training Jobs

```http
GET /jobs?status=running&page=1&limit=10
```

**Response**:
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "job_id": "job-12345",
        "name": "my-chatbot-training",
        "status": "running",
        "progress": 0.45,
        "current_step": 450,
        "total_steps": 1000,
        "metrics": {
          "loss": 0.52,
          "learning_rate": 4.5e-5
        },
        "started_at": "2025-01-12T09:00:00Z",
        "eta": "2025-01-12T11:30:00Z"
      }
    ]
  }
}
```

### Get Job Details

```http
GET /jobs/{job_id}
```

### Get Job Logs

```http
GET /jobs/{job_id}/logs?tail=100&level=INFO
```

**Response**:
```json
{
  "success": true,
  "data": {
    "logs": [
      {"timestamp": "2025-01-12T10:00:00Z", "level": "INFO", "message": "Training started"},
      {"timestamp": "2025-01-12T10:01:00Z", "level": "INFO", "message": "Step 100/1000, loss=0.85"}
    ]
  }
}
```

---

## Agent 3: Training Orchestration

**Base URL**: `http://platform-hostname:8003/api/v1`

### Start Training Job

```http
POST /training/start
Content-Type: application/json

{
  "name": "chatbot-training-v1",
  "dataset_id": "ds-001",
  "model": {
    "base_model": "gpt2",
    "use_lora": true,
    "lora_config": {
      "r": 32,
      "alpha": 32
    }
  },
  "training": {
    "num_epochs": 3,
    "learning_rate": 5e-5,
    "batch_size": 8,
    "num_gpus": 4
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "job_id": "job-12345",
    "status": "initializing",
    "estimated_time": "2 hours",
    "estimated_cost": "8 GPU hours"
  }
}
```

### Stop Training Job

```http
POST /training/{job_id}/stop
```

### Pause/Resume Training

```http
POST /training/{job_id}/pause
POST /training/{job_id}/resume
```

### Get Training Metrics

```http
GET /training/{job_id}/metrics?start_step=0&end_step=1000
```

**Response**:
```json
{
  "success": true,
  "data": {
    "metrics": [
      {"step": 100, "loss": 0.85, "learning_rate": 5e-5, "gpu_memory": 12.5},
      {"step": 200, "loss": 0.72, "learning_rate": 4.8e-5, "gpu_memory": 12.5}
    ]
  }
}
```

### List Checkpoints

```http
GET /training/{job_id}/checkpoints
```

**Response**:
```json
{
  "success": true,
  "data": {
    "checkpoints": [
      {
        "checkpoint_id": "ckpt-1000",
        "step": 1000,
        "epoch": 1,
        "metrics": {"loss": 0.45, "val_loss": 0.52},
        "size": "1.2GB",
        "created_at": "2025-01-12T10:30:00Z",
        "is_best": true
      }
    ]
  }
}
```

### Download Checkpoint

```http
GET /training/{job_id}/checkpoints/{checkpoint_id}/download
```

---

## Agent 4: Notebooks & Testing

**Base URL**: `http://platform-hostname:8004/api/v1`

### Create Notebook

```http
POST /notebooks/create
Content-Type: application/json

{
  "name": "model-testing",
  "template": "model-evaluation",
  "kernel": "python3",
  "resources": {
    "gpu": 1,
    "memory": "16GB"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "notebook_id": "nb-001",
    "url": "http://platform-hostname:8888/notebooks/nb-001",
    "token": "abc123...",
    "status": "starting"
  }
}
```

### List Notebooks

```http
GET /notebooks?status=running
```

### Execute Cell

```http
POST /notebooks/{notebook_id}/execute
Content-Type: application/json

{
  "cell_id": "cell-1",
  "code": "print('Hello, world!')"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "output": "Hello, world!\n",
    "execution_time": 0.02,
    "status": "success"
  }
}
```

### Load Model for Testing

```http
POST /notebooks/{notebook_id}/load_model
Content-Type: application/json

{
  "checkpoint_id": "ckpt-1000",
  "device": "cuda:0"
}
```

### Run Inference

```http
POST /notebooks/{notebook_id}/inference
Content-Type: application/json

{
  "prompt": "How do I reset my password?",
  "max_length": 100,
  "temperature": 0.7
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "generated_text": "To reset your password, click on the 'Forgot Password' link...",
    "inference_time": 1.2,
    "tokens_generated": 45
  }
}
```

### Batch Inference

```http
POST /notebooks/{notebook_id}/batch_inference
Content-Type: application/json

{
  "prompts": [
    "How do I reset my password?",
    "What are your business hours?",
    "How do I track my order?"
  ],
  "batch_size": 8
}
```

---

## Agent 5: Inference

**Base URL**: `http://platform-hostname:8005/api/v1`

### Generate Text

```http
POST /inference/generate
Content-Type: application/json

{
  "model": "chatbot-v1",
  "prompt": "How do I reset my password?",
  "parameters": {
    "max_length": 100,
    "temperature": 0.7,
    "top_p": 0.9,
    "repetition_penalty": 1.2
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "generated_text": "To reset your password, click on 'Forgot Password' on the login page...",
    "tokens": 45,
    "inference_time_ms": 1200,
    "model_version": "chatbot-v1-checkpoint-1000"
  }
}
```

### Chat Completion

```http
POST /inference/chat
Content-Type: application/json

{
  "model": "chatbot-v1",
  "messages": [
    {"role": "user", "content": "Hi, I need help"},
    {"role": "assistant", "content": "Hello! How can I help you today?"},
    {"role": "user", "content": "How do I reset my password?"}
  ],
  "parameters": {
    "temperature": 0.7,
    "max_tokens": 150
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "message": {
      "role": "assistant",
      "content": "To reset your password: 1) Click 'Forgot Password' on login page..."
    },
    "finish_reason": "stop",
    "tokens_used": 48
  }
}
```

### Deploy Model

```http
POST /inference/models/deploy
Content-Type: application/json

{
  "checkpoint_id": "ckpt-1000",
  "name": "chatbot-v1",
  "config": {
    "num_gpus": 1,
    "batch_size": 8,
    "quantization": "8bit"
  }
}
```

### List Deployed Models

```http
GET /inference/models
```

**Response**:
```json
{
  "success": true,
  "data": {
    "models": [
      {
        "model_id": "model-chatbot-v1",
        "name": "chatbot-v1",
        "status": "ready",
        "requests_per_second": 5.2,
        "avg_latency_ms": 850,
        "deployed_at": "2025-01-12T08:00:00Z"
      }
    ]
  }
}
```

### Get Model Stats

```http
GET /inference/models/{model_id}/stats?period=24h
```

---

## Agent 6: Documentation

**Base URL**: `http://platform-hostname:11000`

### Access Documentation

```
GET /docs                           # Main documentation hub
GET /docs/student-handbook          # Student handbook
GET /docs/quickstart                # Quick start guide
GET /docs/faq                       # FAQ
GET /docs/troubleshooting           # Troubleshooting guide
GET /docs/use-cases/chatbot         # Chatbot use case
GET /docs/use-cases/classifier      # Classification use case
GET /docs/use-cases/code-assistant  # Code generation use case
GET /docs/api-reference             # This document
```

### Search Documentation

```http
GET /docs/search?q=training+loss&limit=10
```

**Response**:
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "title": "Troubleshooting: Training Loss is NaN",
        "url": "/docs/troubleshooting#training-loss-is-nan",
        "excerpt": "If your training loss becomes NaN...",
        "relevance": 0.95
      }
    ]
  }
}
```

---

## WebSocket APIs

### Real-Time Training Metrics

```javascript
const ws = new WebSocket('ws://platform-hostname:8003/ws/training/job-12345');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Step ${data.step}: Loss=${data.loss}`);
};

// Receive:
// {"step": 100, "loss": 0.85, "lr": 5e-5, "gpu_memory": 12.5}
// {"step": 101, "loss": 0.84, "lr": 4.99e-5, "gpu_memory": 12.5}
```

### Notebook Kernel Output

```javascript
const ws = new WebSocket('ws://platform-hostname:8004/ws/notebooks/nb-001');

ws.send(JSON.stringify({
  "action": "execute",
  "code": "print('Hello')"
}));

ws.onmessage = (event) => {
  const output = JSON.parse(event.data);
  console.log(output.content);  // "Hello"
};
```

---

## Error Handling

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `AUTH_FAILED` | Authentication failed | 401 |
| `FORBIDDEN` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `INVALID_INPUT` | Invalid request parameters | 400 |
| `RESOURCE_LIMIT` | Quota or resource limit exceeded | 429 |
| `SERVER_ERROR` | Internal server error | 500 |
| `GPU_OOM` | GPU out of memory | 507 |
| `TRAINING_FAILED` | Training job failed | 500 |

### Error Response Example

```json
{
  "success": false,
  "error": {
    "code": "GPU_OOM",
    "message": "CUDA out of memory. Tried to allocate 2.5 GB",
    "details": {
      "available_memory": "1.2 GB",
      "requested_memory": "2.5 GB",
      "suggestion": "Reduce batch size or enable gradient checkpointing"
    }
  },
  "metadata": {
    "request_id": "req-123456",
    "timestamp": "2025-01-12T10:30:00Z"
  }
}
```

---

## Rate Limits

### Default Limits

| Endpoint | Requests/Minute | Requests/Hour |
|----------|----------------|---------------|
| `/auth/*` | 10 | 100 |
| `/datasets/*` | 60 | 1000 |
| `/training/*` | 30 | 500 |
| `/inference/*` | 600 | 10000 |
| `/notebooks/*` | 120 | 2000 |

### Rate Limit Headers

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 42
X-RateLimit-Reset: 1673524800
```

### Rate Limit Exceeded

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again in 45 seconds.",
    "details": {
      "limit": 60,
      "reset_at": "2025-01-12T10:31:00Z"
    }
  }
}
```

---

## Python Client Library

### Installation

```bash
pip install gpu-platform-client
```

### Quick Start

```python
from gpu_platform import Client

# Initialize client
client = Client(
    base_url="http://platform-hostname",
    api_token="your-api-token"
)

# Upload dataset
dataset = client.datasets.upload(
    file_path="data.csv",
    name="my-dataset",
    type="chat"
)

# Start training
job = client.training.start(
    name="my-chatbot",
    dataset_id=dataset.id,
    model="gpt2",
    config={
        "num_epochs": 3,
        "learning_rate": 5e-5,
        "num_gpus": 4
    }
)

# Monitor training
for metrics in job.stream_metrics():
    print(f"Step {metrics.step}: Loss={metrics.loss}")

# Wait for completion
job.wait_for_completion()

# Load best checkpoint
model = client.models.load(job.best_checkpoint_id)

# Generate text
output = model.generate("How do I reset my password?")
print(output.text)
```

### Examples

**Upload and train**:
```python
# Upload dataset
dataset = client.datasets.upload("customer-support.csv", type="chat")

# Configure training
config = {
    "model": {"base_model": "gpt2", "use_lora": True},
    "training": {"num_epochs": 3, "batch_size": 8}
}

# Start training
job = client.training.start("chatbot-v1", dataset.id, config)

# Get updates
job.on_progress(lambda p: print(f"{p}% complete"))
job.on_complete(lambda: print("Training done!"))
```

**Inference**:
```python
# Deploy model
model = client.inference.deploy(checkpoint_id="ckpt-1000", name="chatbot-v1")

# Generate
response = model.generate(
    "What are your business hours?",
    temperature=0.7,
    max_length=100
)
print(response.text)

# Chat
conversation = client.inference.chat(model_id="chatbot-v1")
conversation.send("Hi, I need help")
response = conversation.receive()
print(response.content)
```

**Notebooks**:
```python
# Create notebook
notebook = client.notebooks.create("model-testing", template="evaluation")

# Execute code
result = notebook.execute("""
model = load_model('checkpoint-1000')
output = model.generate('Hello')
print(output)
""")
print(result.output)

# Load model in notebook
notebook.load_model("checkpoint-1000")

# Run inference
output = notebook.inference("How do I reset my password?")
```

---

## Code Examples

### Complete Training Pipeline

```python
from gpu_platform import Client
import time

client = Client(api_token="your-token")

# 1. Upload dataset
print("Uploading dataset...")
dataset = client.datasets.upload(
    file_path="training_data.jsonl",
    name="chatbot-dataset-v1",
    description="Customer support conversations",
    type="chat"
)

# Wait for processing
while dataset.status == "processing":
    time.sleep(5)
    dataset.refresh()

print(f"Dataset ready: {dataset.num_examples} examples")

# 2. Start training
print("Starting training...")
job = client.training.start(
    name="chatbot-v1",
    dataset_id=dataset.id,
    model_config={
        "base_model": "microsoft/phi-2",
        "use_lora": True,
        "lora_config": {"r": 32, "alpha": 32}
    },
    training_config={
        "num_epochs": 3,
        "learning_rate": 5e-5,
        "batch_size": 8,
        "num_gpus": 4,
        "mixed_precision": "bf16"
    }
)

# 3. Monitor progress
for update in job.stream_updates():
    if update.type == "metrics":
        print(f"Step {update.step}/{update.total_steps}: Loss={update.loss:.4f}")
    elif update.type == "checkpoint":
        print(f"Checkpoint saved: {update.checkpoint_id}")

# 4. Wait for completion
job.wait_for_completion(timeout=3600*4)  # 4 hours max

# 5. Deploy model
print("Deploying model...")
model = client.inference.deploy(
    checkpoint_id=job.best_checkpoint_id,
    name="chatbot-v1-prod",
    config={"num_gpus": 1, "quantization": "8bit"}
)

# 6. Test
response = model.generate("How do I reset my password?")
print(f"Model response: {response.text}")
```

---

## Support

**API Issues**:
- GitHub: https://github.com/platform/api/issues
- Email: api-support@platform-url.com

**Documentation**:
- Main docs: http://platform-hostname:11000/docs
- API changelog: http://platform-hostname:11000/docs/api-changelog

**Community**:
- Forum: forum.platform-url.com/c/api
- Slack: #api-developers

---

*Last updated: January 12, 2025*

*API Version: 1.0*
