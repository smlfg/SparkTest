"""
Agent 6: Fine-tuning with PyTorch/NeMo
NVIDIA Frameworks Training Pipeline

Main agent module providing unified interface for:
- PyTorch distributed training
- NeMo multi-GPU pipelines
- FLUX.1 LoRA fine-tuning
- Checkpoint management
- Integration with Agent 1 (multi-node) and Agent 4 (inference validation)
"""

from pathlib import Path
import sys

# Add paths for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import configuration
from agent6_training_config import (
    TRAINING_PIPELINE,
    PYTORCH_CONFIG,
    NEMO_CONFIG,
    FLUX_CONFIG,
    CHECKPOINT_CONFIG,
    AGENT_INTEGRATION,
    get_pytorch_launch_command,
    validate_training_environment,
)

# Import playbooks
from playbooks.pytorch_fine_tune import PyTorchDistributedTrainer, TrainingArgs
from playbooks.nemo_fine_tune import NeMoFineTuner, NeMoMultiNodeTrainer
from playbooks.flux_finetuning import FluxLoRATrainer, FluxTrainingArgs

# Import utilities
from utils.checkpoint_manager import CheckpointManager, CheckpointMetadata

__version__ = "1.0.0"
__author__ = "Agent 6 Team"

__all__ = [
    # Configuration
    "TRAINING_PIPELINE",
    "PYTORCH_CONFIG",
    "NEMO_CONFIG",
    "FLUX_CONFIG",
    "CHECKPOINT_CONFIG",
    "AGENT_INTEGRATION",
    # Functions
    "get_pytorch_launch_command",
    "validate_training_environment",
    # PyTorch
    "PyTorchDistributedTrainer",
    "TrainingArgs",
    # NeMo
    "NeMoFineTuner",
    "NeMoMultiNodeTrainer",
    # FLUX
    "FluxLoRATrainer",
    "FluxTrainingArgs",
    # Checkpoint Management
    "CheckpointManager",
    "CheckpointMetadata",
]


def get_agent_info():
    """Get Agent 6 information."""
    return {
        "name": "Agent 6",
        "version": __version__,
        "description": "Fine-tuning with PyTorch/NeMo",
        "frameworks": ["PyTorch", "NeMo", "FLUX.1"],
        "capabilities": [
            "PyTorch distributed training",
            "NeMo multi-GPU pipeline",
            "FLUX.1 LoRA training",
            "Checkpoint management",
            "Multi-node orchestration",
            "Inference validation",
        ],
        "dependencies": {
            "agent1": "Multi-node orchestration",
            "agent4": "Inference validation",
        }
    }


def print_agent_info():
    """Print Agent 6 information."""
    info = get_agent_info()
    print("=" * 60)
    print(f"{info['name']} v{info['version']}")
    print("=" * 60)
    print(f"\n{info['description']}")
    print(f"\nFrameworks:")
    for framework in info['frameworks']:
        print(f"  - {framework}")
    print(f"\nCapabilities:")
    for capability in info['capabilities']:
        print(f"  - {capability}")
    print(f"\nDependencies:")
    for agent, desc in info['dependencies'].items():
        print(f"  - {agent}: {desc}")
    print("=" * 60)


if __name__ == "__main__":
    print_agent_info()
