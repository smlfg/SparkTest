"""
Agent 6: Fine-tuning Configuration
PyTorch/NeMo Training Pipeline

This module provides the main configuration interface for Agent 6,
supporting PyTorch distributed training, NeMo multi-GPU pipelines,
and FLUX.1 LoRA fine-tuning.

Dependencies:
- Agent 1: Multi-node orchestration
- Agent 4: Inference validation
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

# Base workspace configuration
WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "/workspace")
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", f"{WORKSPACE_ROOT}/checkpoints")
DATA_DIR = os.getenv("DATA_DIR", f"{WORKSPACE_ROOT}/data")
LOG_DIR = os.getenv("LOG_DIR", f"{WORKSPACE_ROOT}/logs")

# Training Pipeline Configuration
TRAINING_PIPELINE = {
    "pytorch_launcher": "torchrun --nproc_per_node=4",
    "nemo_config": "nemo_config.yaml",
    "checkpoint_dir": "/workspace/checkpoints"
}

# PyTorch Distributed Training Configuration
PYTORCH_CONFIG = {
    "launcher": {
        "command": "torchrun",
        "args": {
            "nproc_per_node": 4,  # GPUs per node
            "nnodes": 1,  # Number of nodes (integrates with Agent 1)
            "node_rank": 0,
            "master_addr": "localhost",
            "master_port": 29500,
            "rdzv_backend": "c10d",
            "rdzv_endpoint": "localhost:29500",
        }
    },
    "training": {
        "batch_size": 32,
        "learning_rate": 5e-5,
        "num_epochs": 10,
        "gradient_accumulation_steps": 1,
        "mixed_precision": "bf16",  # or "fp16", "fp32"
        "gradient_checkpointing": False,
        "dataloader_num_workers": 4,
    },
    "optimizer": {
        "type": "AdamW",
        "betas": [0.9, 0.999],
        "weight_decay": 0.01,
        "eps": 1e-8,
    },
    "scheduler": {
        "type": "cosine",
        "warmup_steps": 100,
        "num_training_steps": None,  # Set based on dataset size
    },
    "checkpoint": {
        "save_dir": f"{CHECKPOINT_DIR}/pytorch",
        "save_interval": 1000,  # Save every N steps
        "keep_last_n": 3,
        "save_optimizer_state": True,
    }
}

# NeMo Multi-GPU Configuration
NEMO_CONFIG = {
    "trainer": {
        "devices": 4,
        "num_nodes": 1,  # Integrates with Agent 1 for multi-node
        "accelerator": "gpu",
        "strategy": "ddp",  # or "ddp_sharded", "fsdp"
        "precision": "bf16-mixed",
        "max_epochs": 10,
        "val_check_interval": 1.0,
        "limit_val_batches": 50,
        "log_every_n_steps": 10,
    },
    "exp_manager": {
        "exp_dir": f"{LOG_DIR}/nemo",
        "name": "nemo_finetuning",
        "create_tensorboard_logger": True,
        "create_checkpoint_callback": True,
        "checkpoint_callback_params": {
            "monitor": "val_loss",
            "save_top_k": 3,
            "mode": "min",
            "always_save_nemo": True,
            "save_best_model": True,
            "every_n_epochs": 1,
        },
        "resume_if_exists": True,
        "resume_ignore_no_checkpoint": True,
    },
    "model": {
        "micro_batch_size": 4,
        "global_batch_size": 16,
        "tensor_model_parallel_size": 1,
        "pipeline_model_parallel_size": 1,
        "gradient_as_bucket_view": True,
        "optim": {
            "name": "fused_adam",
            "lr": 5e-5,
            "weight_decay": 0.01,
            "betas": [0.9, 0.999],
            "sched": {
                "name": "CosineAnnealing",
                "warmup_steps": 100,
                "constant_steps": 0,
                "min_lr": 5e-6,
            }
        }
    },
    "data": {
        "data_prefix": f"{DATA_DIR}/nemo",
        "num_workers": 4,
        "dataloader_type": "single",
    }
}

# FLUX.1 Dreambooth LoRA Configuration
FLUX_CONFIG = {
    "model": {
        "pretrained_model_name_or_path": "black-forest-labs/FLUX.1-dev",
        "variant": "fp16",
        "revision": None,
    },
    "lora": {
        "rank": 32,
        "alpha": 32,
        "target_modules": ["to_k", "to_q", "to_v", "to_out.0"],
        "dropout": 0.0,
        "bias": "none",
    },
    "training": {
        "instance_prompt": "a photo of sks dog",
        "class_prompt": "a photo of dog",
        "instance_data_dir": f"{DATA_DIR}/flux/instance_images",
        "class_data_dir": f"{DATA_DIR}/flux/class_images",
        "num_class_images": 100,
        "resolution": 512,
        "center_crop": True,
        "train_batch_size": 1,
        "gradient_accumulation_steps": 4,
        "learning_rate": 1e-4,
        "lr_scheduler": "constant",
        "lr_warmup_steps": 0,
        "num_train_epochs": 100,
        "max_train_steps": 1000,
        "prior_preservation": True,
        "prior_loss_weight": 1.0,
    },
    "optimizer": {
        "type": "AdamW",
        "beta1": 0.9,
        "beta2": 0.999,
        "weight_decay": 1e-2,
        "epsilon": 1e-8,
    },
    "checkpoint": {
        "save_dir": f"{CHECKPOINT_DIR}/flux",
        "checkpointing_steps": 500,
        "resume_from_checkpoint": None,
    },
    "validation": {
        "validation_prompt": "a photo of sks dog in a bucket",
        "num_validation_images": 4,
        "validation_steps": 100,
    },
    "hardware": {
        "mixed_precision": "bf16",
        "gradient_checkpointing": True,
        "use_8bit_adam": False,
        "enable_xformers": True,
    }
}

# Checkpoint Management Configuration
CHECKPOINT_CONFIG = {
    "base_dir": CHECKPOINT_DIR,
    "strategies": {
        "interval": {
            "enabled": True,
            "save_every_n_steps": 1000,
        },
        "best_model": {
            "enabled": True,
            "monitor": "val_loss",
            "mode": "min",
        },
        "latest": {
            "enabled": True,
            "keep_last_n": 3,
        },
    },
    "format": {
        "pytorch": "pt",
        "nemo": "nemo",
        "safetensors": "safetensors",
    },
    "metadata": {
        "include_config": True,
        "include_training_state": True,
        "include_optimizer": True,
    }
}

# Agent Integration Configuration
AGENT_INTEGRATION = {
    "agent1": {
        "enabled": True,
        "multi_node_endpoint": "http://localhost:8001/api/v1/nodes",
        "node_discovery": True,
        "sync_checkpoints": True,
    },
    "agent4": {
        "enabled": True,
        "inference_endpoint": "http://localhost:8004/api/v1/inference",
        "validation_interval": 500,  # Run validation every N steps
        "validation_samples": 10,
    }
}

# Monitoring and Logging
MONITORING_CONFIG = {
    "tensorboard": {
        "enabled": True,
        "log_dir": f"{LOG_DIR}/tensorboard",
    },
    "wandb": {
        "enabled": False,
        "project": "agent6-finetuning",
        "entity": None,
    },
    "mlflow": {
        "enabled": False,
        "tracking_uri": "http://localhost:5000",
    },
    "metrics": {
        "log_interval": 10,
        "track_gpu_memory": True,
        "track_throughput": True,
    }
}


def get_pytorch_launch_command(
    script_path: str,
    nproc_per_node: Optional[int] = None,
    nnodes: Optional[int] = None,
    node_rank: Optional[int] = None,
    master_addr: Optional[str] = None,
    master_port: Optional[int] = None,
    additional_args: Optional[List[str]] = None
) -> str:
    """
    Generate PyTorch distributed training launch command.

    Args:
        script_path: Path to training script
        nproc_per_node: Number of processes per node (GPUs)
        nnodes: Number of nodes
        node_rank: Rank of current node
        master_addr: Master node address
        master_port: Master node port
        additional_args: Additional arguments for the script

    Returns:
        Complete launch command string
    """
    config = PYTORCH_CONFIG["launcher"]["args"].copy()

    if nproc_per_node is not None:
        config["nproc_per_node"] = nproc_per_node
    if nnodes is not None:
        config["nnodes"] = nnodes
    if node_rank is not None:
        config["node_rank"] = node_rank
    if master_addr is not None:
        config["master_addr"] = master_addr
    if master_port is not None:
        config["master_port"] = master_port

    cmd_parts = ["torchrun"]
    for key, value in config.items():
        cmd_parts.append(f"--{key}={value}")

    cmd_parts.append(script_path)

    if additional_args:
        cmd_parts.extend(additional_args)

    return " ".join(cmd_parts)


def get_nemo_config_path(config_name: str = "nemo_config.yaml") -> str:
    """Get path to NeMo configuration file."""
    config_path = Path(__file__).parent / "configs" / config_name
    return str(config_path)


def validate_training_environment() -> Dict[str, Any]:
    """
    Validate the training environment setup.

    Returns:
        Dictionary with validation results
    """
    results = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "info": {}
    }

    # Check if directories exist
    for dir_path in [CHECKPOINT_DIR, DATA_DIR, LOG_DIR]:
        if not os.path.exists(dir_path):
            results["warnings"].append(f"Directory does not exist: {dir_path}")

    # Check GPU availability
    try:
        import torch
        gpu_count = torch.cuda.device_count()
        results["info"]["gpu_count"] = gpu_count
        if gpu_count == 0:
            results["errors"].append("No GPUs detected")
            results["valid"] = False
    except ImportError:
        results["warnings"].append("PyTorch not installed")

    return results


if __name__ == "__main__":
    # Display configuration summary
    print("=" * 60)
    print("Agent 6: Fine-tuning Configuration Summary")
    print("=" * 60)
    print(f"\nWorkspace Root: {WORKSPACE_ROOT}")
    print(f"Checkpoint Directory: {CHECKPOINT_DIR}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Log Directory: {LOG_DIR}")
    print(f"\nPyTorch Launcher: {TRAINING_PIPELINE['pytorch_launcher']}")
    print(f"NeMo Config: {TRAINING_PIPELINE['nemo_config']}")

    # Validate environment
    print("\n" + "=" * 60)
    print("Environment Validation")
    print("=" * 60)
    validation = validate_training_environment()
    print(f"Valid: {validation['valid']}")
    if validation['errors']:
        print(f"Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"Warnings: {validation['warnings']}")
    if validation['info']:
        print(f"Info: {validation['info']}")
