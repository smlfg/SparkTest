# Agent 5: Inference Engine - Ollama + NVIDIA NIM

A comprehensive inference engine deployment solution combining **Ollama** for local GPU-accelerated LLM inference, **NVIDIA NIM** (Inference Microservices) for enterprise-grade models, and **Open WebUI** for a user-friendly interface.

## 🚀 Features

- **Ollama Integration**: GPU-accelerated local model inference
  - Multiple model support (Llama 3.1, Mistral, CodeLlama, etc.)
  - Docker containerized deployment
  - Automatic model pulling and management

- **NVIDIA NIM Support**: Enterprise-grade inference microservices
  - Support for Llama 3.1 (405B, 70B, 8B) and other models
  - OpenAI-compatible API
  - Load-balanced API gateway

- **Open WebUI**: Modern web interface
  - Chat interface for model interaction
  - User authentication and management
  - Multi-model support

- **Unified Model Management API**: Single API for all inference backends
  - RESTful API with OpenAPI documentation
  - Model registry and discovery
  - Health monitoring and status checks

## 📋 Prerequisites

### Hardware Requirements

- **For Ollama**:
  - NVIDIA GPU with 8GB+ VRAM (16GB+ recommended)
  - 16GB+ RAM
  - 50GB+ storage for models

- **For NIM**:
  - NVIDIA GPU with 24GB+ VRAM (80GB+ for 405B models)
  - 32GB+ RAM
  - 100GB+ storage

### Software Requirements

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Container Toolkit
- NVIDIA GPU Drivers 535+
- (Optional) Ansible 2.9+ for automated deployment

## 🛠️ Installation

### Option 1: Quick Start with Docker Compose (Recommended)

1. **Clone the repository**:
```bash
git clone <repository-url>
cd SparkTest
```

2. **Configure environment**:
```bash
cp configs/agent5.env.example .env
# Edit .env and add your NGC_API_KEY for NIM access
nano .env
```

3. **Deploy all services**:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

4. **Access the services**:
- Open WebUI: http://localhost:8080
- Model Management API: http://localhost:8888
- API Documentation: http://localhost:8888/docs

### Option 2: Manual Docker Compose Deployment

```bash
# Copy environment file
cp configs/agent5.env.example .env

# Edit with your settings
nano .env

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Option 3: Ansible Automated Deployment

1. **Configure inventory**:
```bash
nano configs/inventory.ini
```

2. **Run deployment playbook**:
```bash
cd playbooks
ansible-playbook -i ../configs/inventory.ini deploy-all.yml
```

3. **Deploy specific components**:
```bash
# Ollama only
ansible-playbook -i ../configs/inventory.ini ollama.yml

# Open WebUI only
ansible-playbook -i ../configs/inventory.ini open-webui.yml

# NIM only
ansible-playbook -i ../configs/inventory.ini nim-llm.yml
```

## 📚 Usage

### Model Management

#### List Available Models
```bash
# Using the management script
./scripts/manage-models.sh list

# Using the API
curl http://localhost:8888/api/models | jq '.'
```

#### Pull a Model (Ollama)
```bash
# Using the management script
./scripts/manage-models.sh pull llama3.1:70b

# Using the API
curl -X POST "http://localhost:8888/api/models/pull?model_name=llama3.1:70b"
```

#### Test a Model
```bash
# Using the management script
./scripts/manage-models.sh test llama3.1:70b ollama

# Using the API directly
curl -X POST http://localhost:8888/api/completion \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:70b",
    "prompt": "Explain quantum computing in simple terms",
    "max_tokens": 200,
    "provider": "ollama"
  }'
```

### Using the API

#### Python Example
```python
import requests

API_URL = "http://localhost:8888"

# List models
response = requests.get(f"{API_URL}/api/models")
models = response.json()
print(f"Available models: {models}")

# Generate completion
completion_request = {
    "model": "llama3.1:70b",
    "prompt": "Write a Python function to calculate fibonacci numbers",
    "max_tokens": 500,
    "temperature": 0.7,
    "provider": "ollama"
}

response = requests.post(
    f"{API_URL}/api/completion",
    json=completion_request
)
result = response.json()
print(result["response"])

# Chat completion
chat_request = {
    "model": "llama3.1:70b",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is machine learning?"}
    ],
    "max_tokens": 300,
    "provider": "ollama"
}

response = requests.post(
    f"{API_URL}/api/chat",
    json=chat_request
)
print(response.json())
```

#### cURL Examples
```bash
# Health check
curl http://localhost:8888/health

# List all models
curl http://localhost:8888/api/models

# Get model registry
curl http://localhost:8888/api/models/registry

# List providers
curl http://localhost:8888/api/providers

# Text completion (Ollama)
curl -X POST http://localhost:8888/api/completion \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral:7b",
    "prompt": "Once upon a time",
    "max_tokens": 100,
    "temperature": 0.8,
    "provider": "ollama"
  }'

# Chat completion (NIM)
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.1-70b-instruct",
    "messages": [
      {"role": "user", "content": "Hello, how are you?"}
    ],
    "max_tokens": 150,
    "provider": "nim"
  }'
```

### Using Open WebUI

1. Navigate to http://localhost:8080
2. Create an account (first user becomes admin)
3. Select a model from the dropdown
4. Start chatting!

## 🔗 Integration with Agent 3 (Training)

### Import Fine-Tuned Models

Import models fine-tuned with Agent 3 (LLaMA-Factory) into Ollama:

```bash
# Import a fine-tuned LoRA model
python agents/agent5_inference/scripts/import_finetuned.py \
  --checkpoint /path/to/agent3/output/student-chat-model \
  --model-name student-chatbot \
  --base-model meta-llama/Llama-3.1-8B-Instruct

# Test the imported model
ollama run student-chatbot
```

**Features:**
- Automatic LoRA adapter merging
- GGUF conversion (if llama.cpp available)
- Ollama Modelfile generation
- One-command import process

**Options:**
```bash
--checkpoint PATH       # Path to LoRA checkpoint from Agent 3
--model-name NAME       # Name for imported model in Ollama
--base-model MODEL      # Base model used for fine-tuning
--temperature FLOAT     # Default temperature (default: 0.7)
--context-length INT    # Context window (default: 4096)
--keep-merged          # Keep merged model directory
--no-cleanup           # Don't clean up temporary files
```

### Model Comparison API

Compare multiple models side-by-side to evaluate fine-tuning results:

```bash
# Compare base model vs fine-tuned model
curl -X POST http://localhost:8888/api/compare \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain photosynthesis in simple terms",
    "models": ["llama3.1:8b", "student-chatbot"],
    "max_tokens": 200,
    "temperature": 0.7
  }'
```

**Response:**
```json
{
  "prompt": "Explain photosynthesis...",
  "models_compared": 2,
  "successful": 2,
  "failed": 0,
  "average_tokens_per_sec": 11.9,
  "average_duration_ms": 1823.5,
  "results": [
    {
      "model": "llama3.1:8b",
      "response": "Photosynthesis is the process...",
      "eval_duration_ms": 1850.23,
      "tokens_per_second": 12.1,
      "total_tokens": 45
    },
    {
      "model": "student-chatbot",
      "response": "Photosynthesis is how plants...",
      "eval_duration_ms": 1796.77,
      "tokens_per_second": 11.7,
      "total_tokens": 42
    }
  ]
}
```

**Python Example:**
```python
import requests

response = requests.post(
    "http://localhost:8888/api/compare",
    json={
        "prompt": "What is a neural network?",
        "models": ["llama3.1:8b", "student-chatbot", "mistral:7b"],
        "max_tokens": 150
    }
)

results = response.json()
for result in results["results"]:
    print(f"{result['model']}: {result['tokens_per_second']:.1f} tok/s")
```

### Student Benchmark Suite

Comprehensive benchmarking for evaluating model performance:

```bash
# Benchmark a single model
python agents/agent5_inference/scripts/student_benchmark.py \
  --model student-chatbot

# Compare multiple models
python agents/agent5_inference/scripts/student_benchmark.py \
  --models llama3.1:8b student-chatbot mistral:7b

# Use custom prompts
python agents/agent5_inference/scripts/student_benchmark.py \
  --model student-chatbot \
  --prompts my_prompts.txt \
  --max-tokens 300

# Export results to JSON
python agents/agent5_inference/scripts/student_benchmark.py \
  --models llama3.1:8b student-chatbot \
  --output benchmark_results.json
```

**Default Benchmarks:**
- General knowledge questions
- Technical explanations
- Translation tasks
- Code generation
- Creative writing
- Math reasoning
- Language understanding
- Summarization
- Problem solving
- Comparative analysis

**Output:**
```
==================================================================
COMPARISON RESULTS
==================================================================
╔═══════════════════╦══════════════════╦═══════════════════╦═════════════╦══════════════╗
║ Model             ║ Avg Latency (s)  ║ Throughput (tok/s)║ Success Rate║ Total Tokens ║
╠═══════════════════╬══════════════════╬═══════════════════╬═════════════╬══════════════╣
║ llama3.1:8b       ║ 1.85             ║ 12.3              ║ 100.0%      ║ 450          ║
║ student-chatbot   ║ 1.92             ║ 11.8              ║ 100.0%      ║ 445          ║
║ mistral:7b        ║ 1.67             ║ 13.1              ║ 100.0%      ║ 435          ║
╚═══════════════════╩══════════════════╩═══════════════════╩═════════════╩══════════════╝
```

**Use Cases:**
- Evaluate fine-tuned models vs base models
- Compare different quantization levels
- Test model performance across task types
- Generate performance reports for students
- Validate training improvements

## 🔧 Configuration

### Environment Variables

Edit `.env` file or set these environment variables:

```bash
# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_PORT=11434

# Open WebUI Configuration
WEBUI_PORT=8080
WEBUI_NAME="Agent5 Inference Engine"
ENABLE_NGINX=false

# NIM Configuration
NIM_BASE_URL=http://localhost:8000
NIM_PORT=8000
NGC_API_KEY=your_nvidia_ngc_api_key_here

# Model Management API
API_HOST=0.0.0.0
API_PORT=8888

# GPU Configuration
NVIDIA_VISIBLE_DEVICES=all
NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

### Model Configuration

Edit the `MODEL_REGISTRY` in `api/agent5_model_api.py`:

```python
MODEL_REGISTRY = {
    "ollama_models": [
        "llama3.1:70b",
        "mistral:7b",
        "codellama:13b",
        "neural-chat:7b"
    ],
    "nim_endpoints": [
        "nvcr.io/nim/meta/llama-3.1-405b-instruct",
        "nvcr.io/nim/meta/llama-3.1-70b-instruct"
    ]
}
```

## 📊 Monitoring

### Check Service Status
```bash
# Docker Compose deployment
docker-compose ps
docker-compose logs -f [service-name]

# Check individual services
curl http://localhost:11434/api/tags  # Ollama
curl http://localhost:8080            # Open WebUI
curl http://localhost:8000/health     # NIM Gateway
curl http://localhost:8888/health     # Model API
```

### GPU Monitoring
```bash
# Check GPU usage
nvidia-smi

# Watch GPU usage
watch -n 1 nvidia-smi
```

### API Health Checks
```bash
./scripts/test-api.sh
```

## 🗂️ Project Structure

```
SparkTest/
├── api/
│   └── agent5_model_api.py      # Unified model management API
├── configs/
│   ├── agent5.env.example       # Environment configuration template
│   ├── inventory.ini            # Ansible inventory
│   └── nginx-nim.conf           # Nginx configuration for NIM gateway
├── docker/
│   └── Dockerfile.api           # Dockerfile for API service
├── playbooks/
│   ├── deploy-all.yml           # Main deployment playbook
│   ├── ollama.yml               # Ollama deployment playbook
│   ├── open-webui.yml           # Open WebUI deployment playbook
│   └── nim-llm.yml              # NIM deployment playbook
├── scripts/
│   ├── deploy.sh                # Main deployment script
│   ├── manage-models.sh         # Model management utilities
│   └── test-api.sh              # API testing script
├── docker-compose.yml           # Docker Compose configuration
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔍 Troubleshooting

### Ollama Issues

**Problem**: Ollama container fails to start
```bash
# Check GPU availability
nvidia-smi

# Check Docker logs
docker logs ollama

# Restart container
docker restart ollama
```

**Problem**: Models not loading
```bash
# Check available disk space
df -h

# Pull model manually
docker exec ollama ollama pull llama3.1:70b
```

### NIM Issues

**Problem**: NIM container fails to authenticate
```bash
# Verify NGC API key
echo $NGC_API_KEY

# Test NGC login
docker login nvcr.io
# Username: $oauthtoken
# Password: <NGC_API_KEY>
```

**Problem**: Out of GPU memory
```bash
# Check GPU memory
nvidia-smi

# Use smaller models or reduce batch size
# Edit docker-compose.yml to use fewer/smaller models
```

### API Issues

**Problem**: API not responding
```bash
# Check API logs
docker logs agent5-api

# Restart API
docker restart agent5-api

# Check connectivity
curl http://localhost:8888/health
```

## 🔐 Security Considerations

1. **NGC API Key**: Keep your NVIDIA NGC API key secure. Never commit it to version control.

2. **WebUI Authentication**: Enable authentication in Open WebUI for production deployments.

3. **Network Security**: Configure firewall rules to restrict access to inference endpoints.

4. **SSL/TLS**: Use reverse proxy (Nginx/Traefik) with SSL certificates for production.

## 🚢 Production Deployment

For production deployments, consider:

1. **Reverse Proxy**: Use Nginx or Traefik with SSL/TLS
2. **Monitoring**: Set up Prometheus + Grafana for metrics
3. **Load Balancing**: Deploy multiple inference backends
4. **Authentication**: Implement API key authentication
5. **Rate Limiting**: Protect against abuse
6. **Backup**: Regular backups of model data and configurations

## 📖 API Documentation

Once deployed, interactive API documentation is available at:
- Swagger UI: http://localhost:8888/docs
- ReDoc: http://localhost:8888/redoc

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues.

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM inference platform
- [NVIDIA NIM](https://www.nvidia.com/en-us/ai/) - Enterprise inference microservices
- [Open WebUI](https://github.com/open-webui/open-webui) - Web interface for LLMs

## 📞 Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review troubleshooting section

---

**Built with ❤️ for the Agent 5 Inference Engine**
