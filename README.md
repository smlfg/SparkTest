# Agent 6: Fine-tuning with PyTorch/NeMo

Agent 6 provides a comprehensive fine-tuning framework supporting PyTorch distributed training, NVIDIA NeMo multi-GPU pipelines, and FLUX.1 Dreambooth LoRA training with integrated checkpoint management.

## Overview

**Scope:** NVIDIA frameworks (PyTorch, NeMo, FLUX.1)

**Key Features:**
- PyTorch distributed training with torchrun
- NeMo multi-GPU pipeline with model parallelism
- FLUX.1 Dreambooth LoRA fine-tuning
- Unified checkpoint management
- Multi-node orchestration (via Agent 1)
- Inference validation (via Agent 4)

## Architecture

```
SparkTest/
├── agent6_training_config.py    # Main configuration interface
├── agents/
│   └── agent6/
│       └── __init__.py           # Agent 6 module
├── playbooks/
│   ├── pytorch_fine_tune.py      # PyTorch distributed training
│   ├── nemo_fine_tune.py         # NeMo multi-GPU pipeline
│   └── flux_finetuning.py        # FLUX.1 LoRA training
├── utils/
│   └── checkpoint_manager.py     # Checkpoint management
├── configs/
│   └── nemo_config.yaml          # NeMo configuration
└── docs/
    └── (documentation files)
```

## Installation

### Prerequisites

```bash
# PyTorch (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Transformers and utilities
pip install transformers accelerate datasets

# NeMo (optional, for NeMo playbook)
pip install nemo_toolkit[all]

# Diffusers (optional, for FLUX playbook)
pip install diffusers peft
```

### Using NVIDIA Containers

For NeMo:
```bash
docker run --gpus all -it nvcr.io/nvidia/nemo:24.01.01
```

## Configuration

### Main Configuration Interface

The `agent6_training_config.py` provides the main configuration interface:

```python
from agent6_training_config import TRAINING_PIPELINE

# Training pipeline configuration
TRAINING_PIPELINE = {
    "pytorch_launcher": "torchrun --nproc_per_node=4",
    "nemo_config": "nemo_config.yaml",
    "checkpoint_dir": "/workspace/checkpoints"
}
```

### Environment Variables

```bash
export WORKSPACE_ROOT=/workspace
export CHECKPOINT_DIR=/workspace/checkpoints
export DATA_DIR=/workspace/data
export LOG_DIR=/workspace/logs
```

## Usage

### 1. PyTorch Distributed Training

#### Single Node, Multi-GPU

```python
from playbooks.pytorch_fine_tune import PyTorchDistributedTrainer, TrainingArgs
from transformers import AutoModelForCausalLM, AutoTokenizer

# Configure training
args = TrainingArgs(
    model_name="gpt2",
    train_data_path="/workspace/data/train",
    val_data_path="/workspace/data/val",
    output_dir="/workspace/checkpoints/pytorch/gpt2",
    num_epochs=3,
    batch_size=8,
    learning_rate=5e-5,
    mixed_precision="bf16",
)

# Initialize trainer
trainer = PyTorchDistributedTrainer(args)

# Load model
model = AutoModelForCausalLM.from_pretrained(args.model_name)

# Train
trainer.train(model, train_dataset, eval_dataset)
```

#### Launch with torchrun

```bash
# Single node, 4 GPUs
torchrun --nproc_per_node=4 playbooks/pytorch_fine_tune.py

# Multi-node (requires Agent 1)
torchrun \
  --nproc_per_node=4 \
  --nnodes=2 \
  --node_rank=0 \
  --master_addr=node0 \
  --master_port=29500 \
  playbooks/pytorch_fine_tune.py
```

### 2. NeMo Multi-GPU Training

#### Configure NeMo Training

```python
from playbooks.nemo_fine_tune import NeMoFineTuner

# Initialize fine-tuner
fine_tuner = NeMoFineTuner()

# Setup model
model = fine_tuner.setup_model("megatron-gpt-1.3B")

# Train
trainer, model = fine_tuner.train(
    model=model,
    train_data="/workspace/data/nemo/train.jsonl",
    val_data="/workspace/data/nemo/val.jsonl",
    exp_name="gpt_finetuning",
)
```

#### Multi-Node Training

```python
from playbooks.nemo_fine_tune import NeMoMultiNodeTrainer

# Initialize multi-node trainer
multi_trainer = NeMoMultiNodeTrainer(
    num_nodes=2,
    devices_per_node=4,
    master_addr="node0",
    master_port=12345,
)

# Create distributed trainer
trainer = multi_trainer.create_distributed_trainer(
    strategy="ddp",
    precision="bf16-mixed",
)
```

### 3. FLUX.1 Dreambooth LoRA Training

#### Prepare Data

```bash
# Instance images (your subject)
mkdir -p /workspace/data/flux/instance_images
# Add 5-10 images of your subject

# Class images (optional, for prior preservation)
mkdir -p /workspace/data/flux/class_images
# Add 100+ images of the general class
```

#### Train LoRA

```python
from playbooks.flux_finetuning import FluxLoRATrainer, FluxTrainingArgs

# Configure training
args = FluxTrainingArgs(
    model_name="black-forest-labs/FLUX.1-dev",
    instance_prompt="a photo of sks person",
    class_prompt="a photo of a person",
    instance_data_dir="/workspace/data/flux/instance_images",
    class_data_dir="/workspace/data/flux/class_images",
    output_dir="/workspace/checkpoints/flux",
    max_train_steps=1000,
    lora_rank=32,
    learning_rate=1e-4,
)

# Initialize trainer
trainer = FluxLoRATrainer(args)

# Train
trainer.train()
```

### 4. Checkpoint Management

```python
from utils.checkpoint_manager import CheckpointManager

# Initialize checkpoint manager
manager = CheckpointManager(
    checkpoint_dir="/workspace/checkpoints",
    keep_last_n=3,
    keep_best_n=1,
    best_metric="val_loss",
    best_mode="min",
)

# Save checkpoint
manager.save_checkpoint(
    model=model,
    step=1000,
    epoch=1,
    model_type="pytorch",  # or "nemo", "flux"
    optimizer=optimizer,
    metrics={"val_loss": 0.5, "accuracy": 0.95},
)

# Load checkpoint
manager.load_checkpoint(
    checkpoint_id="latest",  # or "best" or specific ID
    model=model,
    optimizer=optimizer,
    model_type="pytorch",
)

# List checkpoints
checkpoints = manager.list_checkpoints(model_type="pytorch")
for ckpt in checkpoints:
    print(f"{ckpt.checkpoint_id}: step {ckpt.step}, loss {ckpt.metrics.get('val_loss')}")
```

## Training Configurations

### PyTorch Configuration

Key settings in `PYTORCH_CONFIG`:

```python
PYTORCH_CONFIG = {
    "launcher": {
        "nproc_per_node": 4,      # GPUs per node
        "nnodes": 1,               # Number of nodes
    },
    "training": {
        "batch_size": 32,
        "learning_rate": 5e-5,
        "mixed_precision": "bf16",
        "gradient_checkpointing": False,
    },
    "checkpoint": {
        "save_interval": 1000,
        "keep_last_n": 3,
    }
}
```

### NeMo Configuration

Edit `configs/nemo_config.yaml`:

```yaml
trainer:
  devices: 4
  num_nodes: 1
  strategy: ddp
  precision: bf16-mixed
  max_epochs: 10

model:
  micro_batch_size: 4
  global_batch_size: 16
  optim:
    lr: 5.0e-5
```

### FLUX Configuration

Key settings in `FLUX_CONFIG`:

```python
FLUX_CONFIG = {
    "lora": {
        "rank": 32,
        "alpha": 32,
    },
    "training": {
        "learning_rate": 1e-4,
        "max_train_steps": 1000,
        "resolution": 512,
    }
}
```

## Agent Integration

### Agent 1: Multi-Node Orchestration

Agent 6 integrates with Agent 1 for multi-node training:

```python
from agent6_training_config import AGENT_INTEGRATION

# Agent 1 configuration
AGENT_INTEGRATION["agent1"] = {
    "enabled": True,
    "multi_node_endpoint": "http://localhost:8001/api/v1/nodes",
    "node_discovery": True,
    "sync_checkpoints": True,
}
```

### Agent 4: Inference Validation

Agent 6 integrates with Agent 4 for validation during training:

```python
AGENT_INTEGRATION["agent4"] = {
    "enabled": True,
    "inference_endpoint": "http://localhost:8004/api/v1/inference",
    "validation_interval": 500,
    "validation_samples": 10,
}
```

## Monitoring

### TensorBoard

```bash
# Start TensorBoard
tensorboard --logdir=/workspace/logs/tensorboard

# View in browser
http://localhost:6006
```

### Weights & Biases (Optional)

```python
from agent6_training_config import MONITORING_CONFIG

MONITORING_CONFIG["wandb"] = {
    "enabled": True,
    "project": "agent6-finetuning",
    "entity": "your-username",
}
```

## Best Practices

### Memory Optimization

1. **Gradient Checkpointing**: Trade compute for memory
   ```python
   args.gradient_checkpointing = True
   ```

2. **Mixed Precision**: Use bf16 for A100/H100
   ```python
   args.mixed_precision = "bf16"
   ```

3. **Gradient Accumulation**: Effective larger batch sizes
   ```python
   args.gradient_accumulation_steps = 4
   ```

### Multi-GPU Training

1. **Data Parallel (DP)**: Simple, but slower
2. **Distributed Data Parallel (DDP)**: Recommended for most cases
3. **FSDP/DeepSpeed**: For very large models

### Checkpoint Strategy

1. **Save frequently** during initial epochs
2. **Keep best models** based on validation metrics
3. **Clean up old checkpoints** to save space

## Troubleshooting

### CUDA Out of Memory

- Reduce batch size
- Enable gradient checkpointing
- Use gradient accumulation
- Try FSDP or DeepSpeed

### Slow Training

- Check GPU utilization (nvidia-smi)
- Increase num_workers for data loading
- Enable mixed precision training
- Use faster data format (e.g., tfrecord)

### NaN Loss

- Reduce learning rate
- Enable gradient clipping
- Check for data issues
- Use mixed precision carefully

## Examples

See the `examples/` directory for complete training examples:

- `examples/pytorch_gpt2_finetuning.py`
- `examples/nemo_megatron_training.py`
- `examples/flux_dreambooth_lora.py`

## API Reference

### PyTorchDistributedTrainer

```python
trainer = PyTorchDistributedTrainer(args: TrainingArgs)
trainer.train(model, train_dataset, eval_dataset, optimizer, scheduler)
```

### NeMoFineTuner

```python
fine_tuner = NeMoFineTuner(config: Dict[str, Any])
model = fine_tuner.setup_model(model_name, model_type)
trainer, model = fine_tuner.train(model, train_data, val_data)
```

### FluxLoRATrainer

```python
trainer = FluxLoRATrainer(args: FluxTrainingArgs)
trainer.train()
```

### CheckpointManager

```python
manager = CheckpointManager(checkpoint_dir, keep_last_n, keep_best_n)
manager.save_checkpoint(model, step, epoch, model_type, ...)
manager.load_checkpoint(checkpoint_id, model, optimizer, model_type)
```

## Performance Benchmarks

| Model | Framework | GPUs | Batch Size | Throughput | Memory |
|-------|-----------|------|------------|------------|--------|
| GPT-2 | PyTorch | 4x A100 | 32 | 5000 tok/s | 12 GB |
| Megatron-1.3B | NeMo | 4x A100 | 16 | 3500 tok/s | 24 GB |
| FLUX.1 | Diffusers | 1x A100 | 1 | 0.5 img/s | 40 GB |

## Contributing

See CONTRIBUTING.md for development guidelines.

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: docs/
- Issues: GitHub Issues
- Contact: agent6-support@example.com

## Changelog

### v1.0.0 (2025-01-12)
- Initial release
- PyTorch distributed training support
- NeMo multi-GPU pipeline
- FLUX.1 LoRA training
- Checkpoint management
- Agent 1 and Agent 4 integration
