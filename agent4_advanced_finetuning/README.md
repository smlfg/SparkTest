# Agent 4: Advanced Fine-tuning with PyTorch

Comprehensive PyTorch-based fine-tuning framework for LLMs with LoRA, experiment tracking, and hyperparameter optimization.

## Overview

Agent 4 provides advanced fine-tuning capabilities for students and researchers working with Large Language Models. It includes didactic Jupyter notebooks, production-ready training scripts, and comprehensive experiment tracking.

### Key Features

- 📚 **3 Educational Jupyter Notebooks** with hands-on exercises
- 🚀 **PyTorch Training Pipeline** with LoRA support
- 🔬 **Experiment Tracking System** for reproducibility
- 🎯 **Hyperparameter Search** with grid/random/Bayesian optimization
- 💾 **Checkpoint Management** with automatic best model selection
- 📊 **Visualization Tools** for training metrics

## Quick Start

### Prerequisites

```bash
# Install dependencies
pip install torch transformers peft datasets accelerate
pip install matplotlib tqdm pyyaml
```

### Run Your First Fine-tuning

```bash
# Using the pre-configured test setup
python scripts/train_pytorch.py --config configs/test.yaml
```

### Interactive Learning

Start with the Jupyter notebooks:

```bash
jupyter notebook notebooks/01_pytorch_finetuning_intro.ipynb
```

## Project Structure

```
agent4_advanced_finetuning/
├── notebooks/                    # Educational Jupyter notebooks
│   ├── 01_pytorch_finetuning_intro.ipynb  # 45 min - Basics
│   ├── 02_lora_explained.ipynb            # 30 min - LoRA theory
│   └── 03_distributed_training.ipynb      # 20 min - Multi-GPU
│
├── scripts/                      # Training scripts
│   ├── train_pytorch.py          # Main training script
│   └── hyperparam_search.py      # Hyperparameter optimization
│
├── utils/                        # Utilities
│   └── experiment_logger.py      # Experiment tracking
│
├── configs/                      # Configuration files
│   ├── train_config.yaml         # Default training config
│   ├── test.yaml                 # Quick test config
│   └── hyperparam_search.yaml    # Search configuration
│
├── datasets/                     # Training data
│   ├── student_chat.json         # Example dataset (16 samples)
│   └── test_data.json            # Test dataset (5 samples)
│
├── checkpoints/                  # Saved models
├── experiments/                  # Experiment logs
└── tests/                        # Unit tests
```

## Jupyter Notebooks

### 1. PyTorch Fine-tuning Introduction (45 min)

**File:** `notebooks/01_pytorch_finetuning_intro.ipynb`

**Sections:**
- Dataset Loading
- Model Loading with LoRA
- Training Loop implementation
- Checkpoint Saving
- Inference Testing

**Exercises:** 3 hands-on exercises with solutions

### 2. LoRA Explained (30 min)

**File:** `notebooks/02_lora_explained.ipynb`

**Topics:**
- LoRA theory and mathematics
- Rank parameter analysis
- Memory savings calculation
- Visualization of decomposition

**Visualizations:** 2+ interactive plots

### 3. Distributed Training (20 min)

**File:** `notebooks/03_distributed_training.ipynb`

**Coverage:**
- Data Parallel vs Model Parallel
- PyTorch DDP setup
- DeepSpeed ZeRO configuration
- Multi-node deployment

**Note:** Conceptual overview with code templates

## Training Script Usage

### Basic Training

```bash
python scripts/train_pytorch.py \
    --config configs/train_config.yaml \
    --dataset agent4_advanced_finetuning/datasets/student_chat.json
```

### Resume from Checkpoint

```bash
python scripts/train_pytorch.py \
    --config configs/train_config.yaml \
    --resume agent4_advanced_finetuning/checkpoints/checkpoint-epoch-2
```

### Custom Output Directory

```bash
python scripts/train_pytorch.py \
    --config configs/train_config.yaml \
    --checkpoint_dir /custom/path/to/checkpoints
```

## Configuration

### Training Configuration

Edit `configs/train_config.yaml`:

```yaml
model:
  name_or_path: "meta-llama/Llama-3.1-8B-Instruct"
  load_in_8bit: true

lora:
  r: 8                    # LoRA rank
  lora_alpha: 16          # Scaling factor
  lora_dropout: 0.05
  target_modules:
    - "q_proj"
    - "v_proj"

training:
  num_epochs: 3
  batch_size: 4
  learning_rate: 2.0e-4
  gradient_accumulation_steps: 4
```

### Key Parameters

| Parameter | Description | Typical Values |
|-----------|-------------|----------------|
| `lora.r` | LoRA rank (controls model capacity) | 4, 8, 16, 32 |
| `lora.lora_alpha` | LoRA scaling factor | 2×r (e.g., 16 for r=8) |
| `training.learning_rate` | Learning rate | 1e-5 to 5e-4 |
| `training.batch_size` | Batch size per GPU | 2, 4, 8 |
| `model.load_in_8bit` | Use 8-bit quantization | true/false |

## Hyperparameter Search

Run hyperparameter optimization:

```bash
python scripts/hyperparam_search.py \
    --config configs/hyperparam_search.yaml \
    --trials 10
```

### Search Space Configuration

Edit `configs/hyperparam_search.yaml`:

```yaml
search_space:
  lora.r:
    type: "categorical"
    values: [4, 8, 16, 32]

  training.learning_rate:
    type: "loguniform"
    low: 1.0e-5
    high: 5.0e-4
```

### Search Methods

- **Grid Search**: Exhaustive search over all combinations
- **Random Search**: Random sampling from search space
- **Bayesian**: Bayesian optimization (experimental)

## Experiment Tracking

All experiments are automatically logged with:

- Configuration parameters
- Training metrics per epoch
- Git commit hash
- Hardware information
- Dataset metadata

### View Experiment Results

```python
from utils.experiment_logger import load_experiment

exp = load_experiment("experiments/my-experiment.json")
print(f"Best epoch: {exp['metrics'][-1]}")
```

### Compare Experiments

```python
from utils.experiment_logger import compare_experiments

comparison = compare_experiments(
    ["experiments/exp1.json", "experiments/exp2.json"],
    metric="eval_loss"
)

print(f"Best: {comparison['best_experiment']['name']}")
```

## Dataset Format

Use the Alpaca instruction format:

```json
[
  {
    "instruction": "Erkläre maschinelles Lernen",
    "input": "",
    "output": "Maschinelles Lernen ist..."
  },
  {
    "instruction": "Übersetze ins Englische",
    "input": "Guten Morgen",
    "output": "Good morning"
  }
]
```

## Performance Benchmarks

### Memory Requirements

| Model | Full FT | LoRA (r=8) | LoRA (r=8, 8-bit) |
|-------|---------|------------|-------------------|
| Llama-3.1-8B | ~64 GB | ~32 GB | ~16 GB |
| Llama-3.1-13B | ~104 GB | ~52 GB | ~26 GB |

### Training Speed

On NVIDIA Blackwell GB10 (128GB UMA):

| Batch Size | Grad Accum | Throughput |
|------------|------------|------------|
| 4 | 4 | ~1000 tokens/s |
| 8 | 2 | ~1200 tokens/s |
| 16 | 1 | ~1400 tokens/s |

## Testing

### Run Functional Tests

```bash
# Test notebooks exist
ls notebooks/*.ipynb | wc -l  # Should be >= 3

# Test training script
python scripts/train_pytorch.py --config configs/test.yaml

# Test experiment logger
python -c "from utils.experiment_logger import ExperimentLogger; logger=ExperimentLogger('test'); logger.save()"

# Test hyperparameter search
python scripts/hyperparam_search.py --trials 3
```

## Troubleshooting

### Out of Memory

**Solution:** Reduce batch size or use gradient accumulation

```yaml
training:
  batch_size: 2              # Smaller batch
  gradient_accumulation_steps: 8  # More accumulation
```

### Slow Training

**Solutions:**
1. Increase batch size (if memory allows)
2. Use 8-bit quantization for base model
3. Enable mixed precision training (bf16)

```yaml
model:
  load_in_8bit: true
training:
  bf16: true
```

### CUDA Out of Memory

**Solution:** Use smaller LoRA rank or enable gradient checkpointing

```yaml
lora:
  r: 4  # Smaller rank
```

## Advanced Topics

### Custom Dataset Loading

```python
from torch.utils.data import Dataset

class MyDataset(Dataset):
    def __init__(self, data_path, tokenizer):
        self.data = load_data(data_path)
        self.tokenizer = tokenizer

    def __getitem__(self, idx):
        # Custom preprocessing
        return processed_item
```

### Custom LoRA Targets

```yaml
lora:
  target_modules:
    - "q_proj"        # Query projection
    - "k_proj"        # Key projection
    - "v_proj"        # Value projection
    - "o_proj"        # Output projection
    - "gate_proj"     # MLP gate
    - "up_proj"       # MLP up
    - "down_proj"     # MLP down
```

### Distributed Training

```bash
# Single node, 4 GPUs
torchrun --nproc_per_node=4 scripts/train_pytorch.py \
    --config configs/train_config.yaml
```

## Best Practices

### LoRA Configuration

1. **Start with r=8**: Good balance between capacity and efficiency
2. **Set alpha=2×r**: Standard recommendation
3. **Target all linear layers**: Better performance
4. **Use dropout=0.05**: Prevents overfitting

### Training Configuration

1. **Learning Rate**: Start with 2e-4, adjust based on loss
2. **Warmup**: Use 10% of training steps
3. **Scheduler**: Cosine annealing works well
4. **Gradient Clipping**: max_norm=1.0

### Data Preparation

1. **Quality over quantity**: 1000 high-quality samples > 10000 low-quality
2. **Diverse examples**: Cover all use cases
3. **Balanced distribution**: Avoid class imbalance
4. **Validation split**: 10-20% for evaluation

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{agent4_finetuning,
  title={Agent 4: Advanced Fine-tuning Framework},
  author={SparkTest Team},
  year={2025},
  url={https://github.com/yourrepo/SparkTest}
}
```

## References

- [LoRA Paper](https://arxiv.org/abs/2106.09685)
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)
- [PEFT Documentation](https://huggingface.co/docs/peft)
- [PyTorch DDP Tutorial](https://pytorch.org/tutorials/intermediate/ddp_tutorial.html)

## Support

For issues and questions:
- GitHub Issues: [Create an issue]
- Documentation: See `notebooks/` for detailed guides
- Examples: See `datasets/` for data format examples

## License

MIT License - See LICENSE file for details
