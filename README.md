# Agent 7: LoRA Fine-tuning System

Efficient fine-tuning framework with Unsloth, LLaMA Factory, and Vision-Language Model support.

## 🚀 Features

### 1. **Unsloth QLoRA Pipeline** (Memory-Efficient)
- 4-bit quantization with QLoRA
- 2x faster training
- 50% less VRAM usage
- Optimized gradient checkpointing

### 2. **LLaMA Factory Web UI** (All-in-One GUI)
- User-friendly Gradio interface
- No-code fine-tuning
- Dataset management
- Real-time monitoring
- Model export (GGUF, AWQ, GPTQ)

### 3. **VLM Fine-tuning** (Vision-Language Models)
- LLaVA support
- Qwen-VL support
- MiniGPT-4 compatible
- Multimodal LoRA adapters

### 4. **LoRA Adapter Management**
- Central registry system
- Version tracking
- Easy loading/merging
- Metadata management

## 📦 Installation

```bash
# Clone repository
git clone <repository-url>
cd SparkTest

# Install dependencies
pip install -r requirements.txt

# Or install individual components
pip install unsloth
pip install llamafactory[torch,metrics]
```

## 🎯 Quick Start

### Launch LLaMA Factory UI

```bash
# Python
python agent7_lora_api.py ui

# Or with custom port
python agent7_lora_api.py ui --port 8080 --share
```

Access at: http://localhost:7860

### Quick Training with Unsloth

```python
from agent7_lora_api import Agent7LoRAAPI

# Initialize API
api = Agent7LoRAAPI()

# Quick train
api.quick_train_unsloth(
    dataset_path="./data/train.json",
    model_name="unsloth/llama-3-8b-bnb-4bit",
    adapter_name="my_adapter",
    num_epochs=3,
    learning_rate=2e-4
)
```

### Fine-tune Vision-Language Model

```python
from agent7_lora_api import Agent7LoRAAPI

# Initialize API
api = Agent7LoRAAPI()

# Create VLM pipeline
vlm = api.create_vlm_pipeline(
    model_name="llava-hf/llava-1.5-7b-hf",
    model_type="llava",
    lora_r=8
)

# Setup and train
vlm.setup_model()
dataset, collate_fn = vlm.prepare_dataset(
    dataset_path="./data/vlm_train.json",
    image_column="image",
    text_column="text"
)
vlm.train(dataset, collate_fn)
vlm.save_adapter("./workspace/loras/my_vlm_adapter")
```

## 📋 Usage Examples

### 1. Unsloth QLoRA Training

```python
from agent7_lora.pipelines.unsloth_qlora import UnslothQLoRAPipeline

# Create pipeline
pipeline = UnslothQLoRAPipeline(
    model_name="unsloth/llama-3-8b-bnb-4bit",
    lora_r=16,
    lora_alpha=16
)

# Setup model
pipeline.setup_model()

# Prepare dataset
dataset = pipeline.prepare_dataset(
    dataset_path="./data/train.json",
    dataset_format="alpaca"
)

# Train
trainer = pipeline.train(
    dataset=dataset,
    output_dir="./outputs/my_adapter",
    num_train_epochs=3,
    learning_rate=2e-4
)

# Save adapter
pipeline.save_lora_adapter("./outputs/my_adapter", adapter_name="my_adapter")
```

### 2. LLaMA Factory CLI Training

```python
from agent7_lora.ui.llama_factory_launcher import LLaMAFactoryUI

# Initialize UI manager
ui = LLaMAFactoryUI()

# Create training config
config_file = ui.create_training_config(
    config_name="my_training",
    model_name="meta-llama/Llama-3-8B",
    dataset_name="alpaca",
    lora_rank=8,
    learning_rate=5e-5,
    num_epochs=3
)

# Train via CLI (without UI)
ui.train_cli(config_file)
```

### 3. Adapter Management

```python
from agent7_lora_api import Agent7LoRAAPI

# Initialize API
api = Agent7LoRAAPI()

# List all adapters
adapters = api.list_adapters()
for adapter in adapters:
    print(f"{adapter['name']} - {adapter['base_model']}")

# Search adapters
results = api.search_adapters("llama")

# Load adapter
adapter = api.load_adapter("my_adapter", base_model=model)

# Merge adapter with base model
api.merge_adapter(
    adapter_name="my_adapter",
    base_model_path="meta-llama/Llama-3-8B",
    output_path="./merged_model"
)
```

### 4. Merge LoRA to Base Model

```bash
# Command line
python agent7_lora/scripts/merge_lora_to_base.py \
  --base-model meta-llama/Llama-3-8B \
  --adapter ./workspace/loras/my_adapter \
  --output ./merged_model

# Python
from agent7_lora_api import Agent7LoRAAPI

api = Agent7LoRAAPI()
api.merge_adapter(
    adapter_name="my_adapter",
    base_model_path="meta-llama/Llama-3-8B",
    output_path="./merged_model"
)
```

## 📁 Directory Structure

```
SparkTest/
├── agent7_lora_api.py          # Main API interface
├── requirements.txt             # Dependencies
├── README.md                    # This file
│
├── agent7_lora/                 # Core modules
│   ├── pipelines/
│   │   └── unsloth_qlora.py    # Unsloth QLoRA pipeline
│   ├── ui/
│   │   └── llama_factory_launcher.py  # LLaMA Factory UI
│   ├── vlm/
│   │   └── vlm_finetuning.py   # VLM fine-tuning
│   ├── adapters/
│   │   └── lora_manager.py     # LoRA management
│   ├── scripts/
│   │   └── merge_lora_to_base.py  # Merge utility
│   └── configs/                 # Configuration files
│
└── workspace/                   # Working directory
    ├── loras/                   # LoRA adapters
    │   └── registry.json        # Adapter registry
    ├── datasets/                # Training datasets
    ├── configs/                 # Training configs
    └── outputs/                 # Training outputs
```

## 🔧 Configuration

### Registry Configuration

```python
LORA_REGISTRY = {
    "adapters": "/workspace/loras",
    "merge_script": "agent7_lora/scripts/merge_lora_to_base.py",
    "ui_endpoint": "http://localhost:7860"
}
```

### Training Configuration

```python
config = {
    "model": {
        "name": "unsloth/llama-3-8b-bnb-4bit",
        "max_seq_length": 2048,
        "load_in_4bit": True,
    },
    "lora": {
        "r": 16,
        "alpha": 16,
        "dropout": 0.05,
        "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"]
    },
    "training": {
        "num_train_epochs": 3,
        "per_device_train_batch_size": 2,
        "gradient_accumulation_steps": 4,
        "learning_rate": 2e-4,
    }
}
```

## 🎮 CLI Commands

```bash
# Launch LLaMA Factory UI
python agent7_lora_api.py ui

# List all adapters
python agent7_lora_api.py list

# Show registry info
python agent7_lora_api.py info

# Search adapters
python agent7_lora_api.py search "llama"

# Get help
python agent7_lora_api.py --help
```

## 📊 Supported Models

### Language Models (LLM)
- LLaMA 2, LLaMA 3
- Mistral, Mixtral
- Qwen, Qwen2
- Phi-3
- Gemma

### Vision-Language Models (VLM)
- LLaVA 1.5, LLaVA 1.6
- Qwen-VL
- MiniGPT-4
- BLIP-2

## 🔬 Advanced Features

### Custom LoRA Configuration

```python
pipeline = UnslothQLoRAPipeline(
    model_name="meta-llama/Llama-3-8B",
    lora_r=32,                    # Higher rank = more capacity
    lora_alpha=64,                # Typically 2x lora_r
    lora_dropout=0.1,
    target_modules=[              # Custom target modules
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ]
)
```

### Dataset Formats

**Alpaca Format:**
```json
[
  {
    "instruction": "Write a poem about AI",
    "input": "",
    "output": "Silicon dreams in neural streams..."
  }
]
```

**ShareGPT Format:**
```json
[
  {
    "conversations": [
      {"from": "human", "value": "Hello!"},
      {"from": "gpt", "value": "Hi! How can I help?"}
    ]
  }
]
```

**VLM Format:**
```json
[
  {
    "image": "./images/cat.jpg",
    "text": "USER: <image>\nWhat is in this image?\nASSISTANT: A cat sitting on a couch."
  }
]
```

## 🐛 Troubleshooting

### CUDA Out of Memory
```python
# Reduce batch size and increase gradient accumulation
pipeline.train(
    dataset=dataset,
    per_device_train_batch_size=1,
    gradient_accumulation_steps=8
)
```

### Slow Training
```python
# Use Unsloth optimizations
from unsloth import FastLanguageModel
model = FastLanguageModel.from_pretrained(...)
```

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## 📚 Resources

- [Unsloth Documentation](https://github.com/unslothai/unsloth)
- [LLaMA Factory](https://github.com/hiyouga/LLaMA-Factory)
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)

## 🤝 Contributing

Contributions welcome! Please open issues or pull requests.

## 📄 License

MIT License - See LICENSE file for details.

## 🙏 Acknowledgments

- Unsloth team for memory-efficient training
- LLaMA Factory for the comprehensive GUI
- HuggingFace for transformers and PEFT
- Tim Dettmers for QLoRA

---

**Agent 7: Fine-tuning made efficient and accessible** 🚀
