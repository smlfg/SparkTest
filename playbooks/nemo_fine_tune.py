"""
NeMo Fine-tuning Playbook
Agent 6: Multi-GPU Pipeline with NVIDIA NeMo

This playbook implements fine-tuning using NVIDIA NeMo framework
with support for multi-GPU training, model parallelism, and
advanced optimization techniques.

Features:
- Data Parallel, Tensor Parallel, Pipeline Parallel
- Mixed precision training (bf16, fp16)
- Gradient accumulation and checkpointing
- NeMo checkpoint management
- Integration with PyTorch Lightning
- Multi-node training support (via Agent 1)
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml
import logging

# NeMo imports (will be available in NeMo container)
try:
    import nemo
    import nemo.collections.nlp as nemo_nlp
    from nemo.collections.nlp.models.language_modeling.megatron_gpt_model import MegatronGPTModel
    from nemo.collections.nlp.parts.nlp_overrides import NLPDDPStrategy
    from nemo.utils.exp_manager import exp_manager
    import pytorch_lightning as pl
    from pytorch_lightning import Trainer
    from pytorch_lightning.callbacks import ModelCheckpoint
    NEMO_AVAILABLE = True
except ImportError:
    NEMO_AVAILABLE = False
    print("Warning: NeMo not installed. Run: pip install nemo_toolkit[all]")

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from agent6_training_config import NEMO_CONFIG, CHECKPOINT_DIR, LOG_DIR, DATA_DIR


class NeMoFineTuner:
    """
    NeMo multi-GPU fine-tuning orchestrator.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize NeMo fine-tuner.

        Args:
            config: Training configuration (uses NEMO_CONFIG if None)
        """
        self.config = config or NEMO_CONFIG
        self.logger = self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%m/%d/%Y %H:%M:%S",
            level=logging.INFO,
        )
        return logging.getLogger(__name__)

    def create_trainer(
        self,
        devices: Optional[int] = None,
        num_nodes: Optional[int] = None,
        strategy: Optional[str] = None,
        precision: Optional[str] = None,
        max_epochs: Optional[int] = None,
    ) -> pl.Trainer:
        """
        Create PyTorch Lightning trainer with NeMo configuration.

        Args:
            devices: Number of GPUs per node
            num_nodes: Number of nodes
            strategy: Training strategy (ddp, ddp_sharded, fsdp)
            precision: Training precision (bf16-mixed, 16-mixed, 32)
            max_epochs: Maximum number of epochs

        Returns:
            Configured PyTorch Lightning Trainer
        """
        trainer_config = self.config["trainer"].copy()

        # Override with provided arguments
        if devices is not None:
            trainer_config["devices"] = devices
        if num_nodes is not None:
            trainer_config["num_nodes"] = num_nodes
        if strategy is not None:
            trainer_config["strategy"] = strategy
        if precision is not None:
            trainer_config["precision"] = precision
        if max_epochs is not None:
            trainer_config["max_epochs"] = max_epochs

        self.logger.info(f"Creating trainer with config: {trainer_config}")

        trainer = pl.Trainer(**trainer_config)
        return trainer

    def setup_model(
        self,
        model_name: str,
        model_type: str = "gpt",
        restore_from: Optional[str] = None,
    ) -> Any:
        """
        Setup NeMo model for fine-tuning.

        Args:
            model_name: Model name or path
            model_type: Type of model (gpt, bert, t5, etc.)
            restore_from: Path to checkpoint to restore from

        Returns:
            NeMo model instance
        """
        if not NEMO_AVAILABLE:
            raise RuntimeError("NeMo is not installed")

        self.logger.info(f"Setting up {model_type} model: {model_name}")

        # Load or create model based on type
        if model_type == "gpt":
            if restore_from:
                model = MegatronGPTModel.restore_from(restore_from)
            else:
                # Load pre-trained model
                model = MegatronGPTModel.from_pretrained(model_name)
        else:
            raise ValueError(f"Model type {model_type} not supported yet")

        # Configure model with training settings
        model_config = self.config["model"]
        model.cfg.micro_batch_size = model_config["micro_batch_size"]
        model.cfg.global_batch_size = model_config["global_batch_size"]

        # Setup optimizer
        model.cfg.optim = model_config["optim"]

        return model

    def setup_data(
        self,
        train_data: str,
        val_data: Optional[str] = None,
        test_data: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Setup data configuration for NeMo.

        Args:
            train_data: Path to training data
            val_data: Path to validation data
            test_data: Path to test data

        Returns:
            Data configuration dictionary
        """
        data_config = self.config["data"].copy()

        data_config["train_ds"] = {
            "file_path": train_data,
            "num_workers": data_config["num_workers"],
        }

        if val_data:
            data_config["validation_ds"] = {
                "file_path": val_data,
                "num_workers": data_config["num_workers"],
            }

        if test_data:
            data_config["test_ds"] = {
                "file_path": test_data,
                "num_workers": data_config["num_workers"],
            }

        return data_config

    def create_exp_manager_config(
        self,
        exp_name: str,
        exp_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create experiment manager configuration.

        Args:
            exp_name: Experiment name
            exp_dir: Experiment directory

        Returns:
            Experiment manager configuration
        """
        exp_config = self.config["exp_manager"].copy()
        exp_config["name"] = exp_name

        if exp_dir:
            exp_config["exp_dir"] = exp_dir

        return exp_config

    def train(
        self,
        model: Any,
        train_data: str,
        val_data: Optional[str] = None,
        exp_name: str = "nemo_finetuning",
        resume_if_exists: bool = True,
    ):
        """
        Execute fine-tuning training.

        Args:
            model: NeMo model to train
            train_data: Path to training data
            val_data: Path to validation data
            exp_name: Experiment name
            resume_if_exists: Resume from checkpoint if exists
        """
        if not NEMO_AVAILABLE:
            raise RuntimeError("NeMo is not installed")

        self.logger.info(f"Starting training: {exp_name}")

        # Setup data
        data_config = self.setup_data(train_data, val_data)
        model.setup_training_data(data_config["train_ds"])
        if val_data:
            model.setup_validation_data(data_config["validation_ds"])

        # Create trainer
        trainer = self.create_trainer()

        # Setup experiment manager
        exp_config = self.create_exp_manager_config(exp_name)
        exp_config["resume_if_exists"] = resume_if_exists
        exp_manager(trainer, exp_config)

        # Train
        self.logger.info("Starting training loop...")
        trainer.fit(model)

        self.logger.info("Training completed!")

        return trainer, model

    def save_checkpoint(
        self,
        model: Any,
        save_path: str,
        save_format: str = "nemo",
    ):
        """
        Save model checkpoint.

        Args:
            model: Model to save
            save_path: Path to save checkpoint
            save_format: Format (nemo, pytorch)
        """
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        if save_format == "nemo":
            model.save_to(save_path)
            self.logger.info(f"Model saved to {save_path}")
        elif save_format == "pytorch":
            # Save as PyTorch checkpoint
            import torch
            torch.save(model.state_dict(), save_path)
            self.logger.info(f"PyTorch checkpoint saved to {save_path}")
        else:
            raise ValueError(f"Unknown save format: {save_format}")

    def export_config(self, output_path: str):
        """
        Export configuration to YAML file.

        Args:
            output_path: Path to save configuration
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False)

        self.logger.info(f"Configuration exported to {output_path}")


class NeMoMultiNodeTrainer:
    """
    Multi-node NeMo training orchestrator with Agent 1 integration.
    """

    def __init__(
        self,
        num_nodes: int,
        devices_per_node: int,
        master_addr: str = "localhost",
        master_port: int = 12345,
    ):
        """
        Initialize multi-node trainer.

        Args:
            num_nodes: Number of nodes
            devices_per_node: GPUs per node
            master_addr: Master node address
            master_port: Master node port
        """
        self.num_nodes = num_nodes
        self.devices_per_node = devices_per_node
        self.master_addr = master_addr
        self.master_port = master_port
        self.logger = logging.getLogger(__name__)

    def setup_distributed_env(self):
        """Setup environment variables for distributed training."""
        os.environ["MASTER_ADDR"] = self.master_addr
        os.environ["MASTER_PORT"] = str(self.master_port)

        self.logger.info(f"Distributed setup: {self.num_nodes} nodes, "
                        f"{self.devices_per_node} GPUs per node")
        self.logger.info(f"Master: {self.master_addr}:{self.master_port}")

    def create_distributed_trainer(
        self,
        strategy: str = "ddp",
        precision: str = "bf16-mixed",
        **kwargs
    ) -> pl.Trainer:
        """
        Create trainer for multi-node training.

        Args:
            strategy: Training strategy
            precision: Training precision
            **kwargs: Additional trainer arguments

        Returns:
            Configured trainer
        """
        self.setup_distributed_env()

        trainer_config = {
            "devices": self.devices_per_node,
            "num_nodes": self.num_nodes,
            "accelerator": "gpu",
            "strategy": strategy,
            "precision": precision,
            **kwargs
        }

        return pl.Trainer(**trainer_config)


def create_nemo_config_yaml(output_path: str):
    """
    Create NeMo configuration YAML file.

    Args:
        output_path: Path to save YAML config
    """
    config = {
        "name": "nemo_finetuning",
        "trainer": NEMO_CONFIG["trainer"],
        "exp_manager": NEMO_CONFIG["exp_manager"],
        "model": NEMO_CONFIG["model"],
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"NeMo configuration saved to: {output_path}")


def main():
    """Main entry point for NeMo fine-tuning."""
    print("=" * 60)
    print("NeMo Fine-tuning Playbook")
    print("=" * 60)

    # Create NeMo config YAML
    config_path = Path(__file__).parent.parent / "configs" / "nemo_config.yaml"
    create_nemo_config_yaml(str(config_path))

    if not NEMO_AVAILABLE:
        print("\nNeMo is not installed. To use this playbook:")
        print("1. Install NeMo: pip install nemo_toolkit[all]")
        print("2. Or use NVIDIA NeMo container:")
        print("   docker run --gpus all -it nvcr.io/nvidia/nemo:24.01.01")
        return

    # Example: Fine-tune GPT model
    print("\nExample: Fine-tuning GPT model")
    print("-" * 60)

    fine_tuner = NeMoFineTuner()

    # Setup model (example - requires actual model checkpoint)
    # model = fine_tuner.setup_model("megatron-gpt-1.3B", restore_from=None)

    # Setup training
    train_data = f"{DATA_DIR}/nemo/train.jsonl"
    val_data = f"{DATA_DIR}/nemo/val.jsonl"

    print(f"Training data: {train_data}")
    print(f"Validation data: {val_data}")
    print(f"Checkpoint dir: {CHECKPOINT_DIR}/nemo")

    # For actual training, uncomment:
    # trainer, model = fine_tuner.train(
    #     model=model,
    #     train_data=train_data,
    #     val_data=val_data,
    #     exp_name="gpt_finetuning",
    # )

    print("\nConfiguration files created successfully!")
    print(f"NeMo config: {config_path}")


if __name__ == "__main__":
    main()
