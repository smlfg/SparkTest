# Agent 6 Quick Start Guide

Get started with Agent 6 fine-tuning in 5 minutes.

## Prerequisites

- Python 3.9+
- CUDA 12.1+
- 1+ NVIDIA GPUs (A100/H100 recommended)
- 100GB+ free disk space

## Installation

### Step 1: Clone and Setup

```bash
cd SparkTest
pip install -r requirements.txt
```

### Step 2: Configure Environment

```bash
# Create workspace directories
mkdir -p /workspace/{checkpoints,data,logs}

# Set environment variables
export WORKSPACE_ROOT=/workspace
export CHECKPOINT_DIR=/workspace/checkpoints
export DATA_DIR=/workspace/data
export LOG_DIR=/workspace/logs
```

### Step 3: Verify Installation

```bash
python agent6_training_config.py
```

Expected output:
```
============================================================
Agent 6: Fine-tuning Configuration Summary
============================================================
...
Environment Validation
Valid: True
```

## Quick Examples

### Example 1: PyTorch GPT-2 Fine-tuning

```python
# train_gpt2.py
from playbooks.pytorch_fine_tune import PyTorchDistributedTrainer, TrainingArgs
from transformers import AutoModelForCausalLM
import torch

# Configure
args = TrainingArgs(
    model_name="gpt2",
    train_data_path="/workspace/data/train.txt",
    output_dir="/workspace/checkpoints/gpt2",
    num_epochs=3,
    batch_size=4,
    learning_rate=5e-5,
)

# Initialize
trainer = PyTorchDistributedTrainer(args)
model = AutoModelForCausalLM.from_pretrained("gpt2")

# Prepare dummy data (replace with your data)
from torch.utils.data import TensorDataset
train_data = TensorDataset(torch.randn(100, 128), torch.randint(0, 2, (100,)))

# Train
trainer.train(model, train_data)
```

Run with:
```bash
# Single GPU
python train_gpt2.py

# Multi-GPU
torchrun --nproc_per_node=4 train_gpt2.py
```

### Example 2: FLUX Dreambooth LoRA

```python
# train_flux.py
from playbooks.flux_finetuning import FluxLoRATrainer, FluxTrainingArgs

args = FluxTrainingArgs(
    instance_prompt="a photo of sks dog",
    instance_data_dir="/workspace/data/flux/my_dog",
    max_train_steps=500,
    learning_rate=1e-4,
)

trainer = FluxLoRATrainer(args)
trainer.train()
```

Prepare your data:
```bash
# Add 5-10 images of your subject
mkdir -p /workspace/data/flux/my_dog
cp my_images/*.jpg /workspace/data/flux/my_dog/
```

Run:
```bash
python train_flux.py
```

### Example 3: Checkpoint Management

```python
from utils.checkpoint_manager import CheckpointManager

# Initialize
manager = CheckpointManager()

# Save
manager.save_checkpoint(
    model=model,
    step=1000,
    epoch=1,
    model_type="pytorch",
    metrics={"val_loss": 0.5}
)

# Load latest
manager.load_checkpoint("latest", model, model_type="pytorch")
```

## Next Steps

1. **Read the full README**: See [README.md](../README.md) for detailed documentation
2. **Configure your training**: Edit `agent6_training_config.py`
3. **Prepare your data**: See data preparation guides in `docs/DATA_PREPARATION.md`
4. **Monitor training**: Use TensorBoard or Weights & Biases
5. **Scale up**: Use Agent 1 for multi-node training

## Common Issues

### CUDA Out of Memory
```python
# Reduce batch size
args.batch_size = 1
args.gradient_accumulation_steps = 8

# Enable gradient checkpointing
args.gradient_checkpointing = True
```

### Slow Data Loading
```python
# Increase workers
from agent6_training_config import PYTORCH_CONFIG
PYTORCH_CONFIG["training"]["dataloader_num_workers"] = 8
```

### Import Errors
```bash
# Add to Python path
export PYTHONPATH=/home/user/SparkTest:$PYTHONPATH
```

## Resources

- Full Documentation: [README.md](../README.md)
- API Reference: [docs/API.md](API.md)
- Examples: [docs/EXAMPLES.md](EXAMPLES.md)
- Troubleshooting: [docs/TROUBLESHOOTING.md](TROUBLESHOOTING.md)

## Support

Having issues? Create an issue on GitHub or contact agent6-support@example.com
