# LLaMA Factory Fine-tuning for Agent 3

**Student-Friendly LLM Fine-tuning with Pre-configured Templates**

Complete fine-tuning setup using LLaMA Factory with ready-to-use templates for chat, classification, and code generation tasks.

## 🚀 Quick Start

### 1. Launch LLaMA Factory

```bash
# From project root
docker-compose up -d llama-factory training-monitor

# Access WebUI
open http://localhost:7860
```

### 2. Quick Start with Examples

```bash
cd agents/agent3_dev_environments/finetuning

# Chat fine-tuning
./scripts/launch_finetuning.sh quick-start chat

# Classification
./scripts/launch_finetuning.sh quick-start classification

# Code assistant
./scripts/launch_finetuning.sh quick-start code
```

### 3. Monitor Training

- **WebUI**: http://localhost:7860
- **Training Monitor API**: http://localhost:8001
- **Live WebSocket**: `ws://localhost:8001/ws/training/{job_id}`

## 📦 What's Included

### Student Templates

Pre-configured YAML templates for common tasks:

| Template | Model | Use Case | LoRA Rank |
|----------|-------|----------|-----------|
| `chat-finetune.yaml` | Llama-3.1-8B | Conversational AI | r=8 |
| `classification.yaml` | Mistral-7B | Text classification | r=16 |
| `code-assistant.yaml` | CodeLlama-13B | Code generation | r=16 |

### Example Datasets

Ready-to-use example datasets in `datasets/examples/`:

- `student-chat.json` - German/English chat examples
- `student-classification.json` - Sentiment & category classification
- `student-code.json` - Python code generation

### Tools

- **Dataset Validator** - Validates your datasets before training
- **Launch Script** - Simplified training interface
- **Training Monitor API** - Real-time training progress via WebSocket

## 📂 Directory Structure

```
finetuning/
├── templates/              # Pre-configured training templates
│   ├── chat-finetune.yaml
│   ├── classification.yaml
│   └── code-assistant.yaml
├── datasets/               # Your datasets go here
│   └── examples/          # Example datasets
│       ├── student-chat.json
│       ├── student-classification.json
│       └── student-code.json
├── models/                 # Downloaded models
├── checkpoints/            # Training outputs
├── scripts/                # Helper scripts
│   ├── launch_finetuning.sh
│   └── validate_dataset.py
└── api/                    # Training monitor API
    └── training_monitor.py
```

## 🎯 Usage Guide

### Using Pre-configured Templates

#### 1. Chat Fine-tuning

```bash
# Prepare your dataset (Alpaca format)
cat > datasets/my-chat.json <<EOF
[
  {
    "instruction": "Explain quantum computing",
    "input": "",
    "output": "Quantum computing uses quantum mechanics..."
  }
]
EOF

# Validate dataset
python scripts/validate_dataset.py datasets/my-chat.json --type chat

# Start training
./scripts/launch_finetuning.sh train \
  --template chat-finetune.yaml \
  --dataset my-chat.json
```

#### 2. Classification

```bash
# Prepare classification dataset
cat > datasets/my-classification.json <<EOF
[
  {
    "instruction": "Classify sentiment",
    "input": "Great product!",
    "output": "positive"
  }
]
EOF

# Train
./scripts/launch_finetuning.sh train \
  --template classification.yaml \
  --dataset my-classification.json
```

#### 3. Code Assistant

```bash
# Prepare code dataset
cat > datasets/my-code.json <<EOF
[
  {
    "instruction": "Write a function to reverse a string",
    "input": "",
    "output": "def reverse_string(s):\n    return s[::-1]"
  }
]
EOF

# Train
./scripts/launch_finetuning.sh train \
  --template code-assistant.yaml \
  --dataset my-code.json
```

### Dataset Format

All datasets use the Alpaca format:

```json
[
  {
    "instruction": "Task description or question",
    "input": "Optional input text (can be empty)",
    "output": "Expected output or answer"
  }
]
```

**Required fields:**
- `instruction`: What the model should do
- `output`: The desired response

**Optional fields:**
- `input`: Additional context or input text
- `system`: System message (for chat models)
- `history`: Conversation history (for chat models)

### Validating Datasets

```bash
# Auto-detect dataset type
python scripts/validate_dataset.py datasets/my-data.json

# Specify type
python scripts/validate_dataset.py datasets/my-data.json --type chat

# JSON output
python scripts/validate_dataset.py datasets/my-data.json --json
```

**Validation checks:**
- Required fields present
- Output length reasonable
- Label balance (for classification)
- Code syntax (for code datasets)

### Monitoring Training

#### Via WebUI

Access http://localhost:7860 for the LLaMA Factory web interface.

#### Via API

```bash
# List all jobs
curl http://localhost:8001/api/jobs

# Get job details
curl http://localhost:8001/api/jobs/{job_id}

# Get recent logs
curl http://localhost:8001/api/jobs/{job_id}/logs?lines=100

# Global stats
curl http://localhost:8001/api/stats
```

#### Via WebSocket

```python
import asyncio
import websockets
import json

async def monitor_training(job_id):
    uri = f"ws://localhost:8001/ws/training/{job_id}"

    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)

            if data["type"] == "loss_update":
                print(f"Loss: {data['loss']}")
            elif data["type"] == "progress_update":
                print(f"Progress: {data['progress']}%")

asyncio.run(monitor_training("student-chat-model"))
```

## 🔧 Customizing Templates

Templates are YAML files with training configuration. Edit them to customize:

```yaml
# templates/my-custom.yaml

model_name_or_path: meta-llama/Llama-3.1-8B-Instruct
stage: sft
finetuning_type: lora

# LoRA settings
lora_rank: 8          # Increase for more capacity
lora_alpha: 16        # Usually 2x rank
lora_dropout: 0.05

# Training hyperparameters
learning_rate: 2.0e-4
num_train_epochs: 3
per_device_train_batch_size: 2
gradient_accumulation_steps: 8

# Dataset
dataset: my_dataset
dataset_dir: /app/data
output_dir: /app/output/my-model

# Advanced
max_length: 2048
bf16: true
gradient_checkpointing: true
```

## 📊 Understanding Results

### Output Structure

After training, find your model in `checkpoints/`:

```
checkpoints/
└── student-chat-model/
    ├── checkpoint-500/        # Intermediate checkpoint
    ├── checkpoint-1000/
    ├── checkpoint-final/      # Final model
    ├── logs/                  # Training logs
    │   └── training.log
    ├── config.json           # Model config
    └── trainer_state.json    # Training state
```

### Loading Fine-tuned Model

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_path = "checkpoints/student-chat-model/checkpoint-final"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

# Generate
inputs = tokenizer("Explain AI:", return_tensors="pt")
outputs = model.generate(**inputs, max_length=100)
print(tokenizer.decode(outputs[0]))
```

## 🎓 Tips for Students

### Dataset Preparation

1. **Start small**: 50-100 high-quality examples
2. **Be specific**: Clear instructions, concise outputs
3. **Validate**: Always run `validate_dataset.py`
4. **Balance**: For classification, balance your labels
5. **Quality over quantity**: Better data = better model

### Training Tips

1. **Start with defaults**: Templates are pre-tuned
2. **Monitor loss**: Should decrease steadily
3. **Check validation**: Watch for overfitting
4. **Save checkpoints**: Resume if interrupted
5. **Experiment**: Try different LoRA ranks, learning rates

### Common Issues

**Out of Memory?**
- Reduce `per_device_train_batch_size`
- Increase `gradient_accumulation_steps`
- Use smaller model (7B instead of 13B)
- Enable `gradient_checkpointing`

**Poor Results?**
- More training data
- More training epochs
- Check dataset quality
- Validate outputs manually

**Training too slow?**
- Check GPU utilization
- Reduce `max_length`
- Use `bf16` if supported
- Reduce batch size

## 🔌 API Reference

### REST Endpoints

```bash
GET  /health                     # Health check
GET  /api/jobs                   # List all jobs
GET  /api/jobs/{job_id}          # Job details
GET  /api/jobs/{job_id}/logs     # Recent logs
GET  /api/stats                  # Global stats
```

### WebSocket

```bash
WS   /ws/training/{job_id}       # Real-time updates
```

**Message Types:**
- `connected`: Initial connection
- `loss_update`: Training loss update
- `progress_update`: Training progress
- `metric_update`: Evaluation metrics
- `log_line`: Raw log line
- `error`: Error message

## 🚀 Advanced Usage

### Multi-GPU Training

Edit template to use multiple GPUs:

```yaml
# In template YAML
fsdp: "full_shard"  # For multi-GPU
fsdp_transformer_layer_cls_to_wrap: "LlamaDecoderLayer"
```

### Custom Models

Use any Hugging Face model:

```yaml
model_name_or_path: meta-llama/Llama-2-13b-hf
# or
model_name_or_path: mistralai/Mixtral-8x7B-Instruct-v0.1
# or
model_name_or_path: google/gemma-7b
```

### Quantization

For 4-bit quantization (lower memory):

```yaml
quantization_bit: 4
quantization_type: nf4
```

### Resume Training

```yaml
resume_from_checkpoint: /app/output/my-model/checkpoint-500
```

## 📚 Resources

- [LLaMA Factory Docs](https://github.com/hiyouga/LLaMA-Factory)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [Alpaca Format](https://github.com/tatsu-lab/stanford_alpaca)
- [Hugging Face Models](https://huggingface.co/models)

## 🤝 Contributing

Improvements welcome!

1. Add new templates for different tasks
2. Create more example datasets
3. Improve validation logic
4. Enhance monitoring features

## 📝 License

Part of Agent 3: Development Environments

---

**Quick Reference Card**

```bash
# List templates
./scripts/launch_finetuning.sh list-templates

# List examples
./scripts/launch_finetuning.sh list-examples

# Validate dataset
./scripts/launch_finetuning.sh validate --dataset my-data.json

# Quick start
./scripts/launch_finetuning.sh quick-start chat

# Custom training
./scripts/launch_finetuning.sh train \
  --template my-template.yaml \
  --dataset my-dataset.json

# Monitor
./scripts/launch_finetuning.sh monitor
```

**Access Points:**
- WebUI: http://localhost:7860
- Monitor API: http://localhost:8001
- TensorBoard: http://localhost:6006
