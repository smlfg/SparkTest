"""
Checkpoint Management Utilities
Agent 6: Unified checkpoint management across PyTorch, NeMo, and FLUX

This module provides utilities for managing training checkpoints,
including saving, loading, cleanup, and synchronization across
distributed nodes.

Features:
- Unified interface for PyTorch, NeMo, and FLUX checkpoints
- Automatic cleanup of old checkpoints
- Best model tracking
- Checkpoint synchronization for multi-node training
- Integration with Agent 1 for distributed storage
- Metadata management
"""

import os
import sys
import json
import shutil
import torch
from pathlib import Path
from typing import Optional, Dict, Any, List, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import glob

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from agent6_training_config import CHECKPOINT_CONFIG, CHECKPOINT_DIR


@dataclass
class CheckpointMetadata:
    """Checkpoint metadata structure."""
    checkpoint_id: str
    step: int
    epoch: int
    timestamp: str
    model_type: str  # pytorch, nemo, flux
    metrics: Dict[str, float]
    config: Dict[str, Any]
    best_model: bool = False
    file_path: str = ""
    file_size: int = 0


class CheckpointManager:
    """
    Unified checkpoint management for all training frameworks.
    """

    def __init__(
        self,
        checkpoint_dir: Optional[str] = None,
        keep_last_n: int = 3,
        keep_best_n: int = 1,
        best_metric: str = "val_loss",
        best_mode: str = "min",
    ):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Base checkpoint directory
            keep_last_n: Number of latest checkpoints to keep
            keep_best_n: Number of best checkpoints to keep
            best_metric: Metric to track for best model
            best_mode: 'min' or 'max' for best metric
        """
        self.checkpoint_dir = Path(checkpoint_dir or CHECKPOINT_DIR)
        self.keep_last_n = keep_last_n
        self.keep_best_n = keep_best_n
        self.best_metric = best_metric
        self.best_mode = best_mode

        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.checkpoint_dir / "checkpoints_metadata.json"

        self.logger = logging.getLogger(__name__)
        self._load_metadata()

    def _load_metadata(self):
        """Load checkpoint metadata from disk."""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r") as f:
                data = json.load(f)
                self.checkpoints = [
                    CheckpointMetadata(**ckpt) for ckpt in data.get("checkpoints", [])
                ]
        else:
            self.checkpoints = []

    def _save_metadata(self):
        """Save checkpoint metadata to disk."""
        data = {
            "checkpoints": [asdict(ckpt) for ckpt in self.checkpoints],
            "last_updated": datetime.now().isoformat(),
        }
        with open(self.metadata_file, "w") as f:
            json.dump(data, f, indent=2)

    def save_checkpoint(
        self,
        model: Any,
        step: int,
        epoch: int,
        model_type: str = "pytorch",
        optimizer: Optional[Any] = None,
        scheduler: Optional[Any] = None,
        metrics: Optional[Dict[str, float]] = None,
        config: Optional[Dict[str, Any]] = None,
        checkpoint_name: Optional[str] = None,
    ) -> str:
        """
        Save a checkpoint.

        Args:
            model: Model to save
            step: Training step
            epoch: Training epoch
            model_type: Type of model (pytorch, nemo, flux)
            optimizer: Optimizer state
            scheduler: Scheduler state
            metrics: Training metrics
            config: Training configuration
            checkpoint_name: Custom checkpoint name

        Returns:
            Path to saved checkpoint
        """
        # Generate checkpoint ID
        checkpoint_id = checkpoint_name or f"checkpoint-step-{step}"
        checkpoint_path = self.checkpoint_dir / model_type / checkpoint_id
        checkpoint_path.mkdir(parents=True, exist_ok=True)

        # Save based on model type
        if model_type == "pytorch":
            saved_path = self._save_pytorch_checkpoint(
                checkpoint_path, model, optimizer, scheduler, step, epoch, metrics, config
            )
        elif model_type == "nemo":
            saved_path = self._save_nemo_checkpoint(
                checkpoint_path, model, step, epoch, metrics, config
            )
        elif model_type == "flux":
            saved_path = self._save_flux_checkpoint(
                checkpoint_path, model, step, epoch, metrics, config
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")

        # Create metadata
        file_size = self._get_directory_size(checkpoint_path)
        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            step=step,
            epoch=epoch,
            timestamp=datetime.now().isoformat(),
            model_type=model_type,
            metrics=metrics or {},
            config=config or {},
            file_path=str(checkpoint_path),
            file_size=file_size,
        )

        # Update best model tracking
        if metrics and self.best_metric in metrics:
            metadata.best_model = self._is_best_model(metrics[self.best_metric])

        # Add to checkpoint list
        self.checkpoints.append(metadata)
        self._save_metadata()

        self.logger.info(f"Checkpoint saved: {checkpoint_path}")

        # Cleanup old checkpoints
        self._cleanup_checkpoints(model_type)

        return str(saved_path)

    def _save_pytorch_checkpoint(
        self,
        checkpoint_path: Path,
        model: Any,
        optimizer: Optional[Any],
        scheduler: Optional[Any],
        step: int,
        epoch: int,
        metrics: Optional[Dict[str, float]],
        config: Optional[Dict[str, Any]],
    ) -> Path:
        """Save PyTorch checkpoint."""
        from torch.nn.parallel import DistributedDataParallel as DDP

        # Unwrap DDP if needed
        model_to_save = model.module if isinstance(model, DDP) else model

        checkpoint = {
            "model_state_dict": model_to_save.state_dict(),
            "step": step,
            "epoch": epoch,
            "metrics": metrics,
            "config": config,
        }

        if optimizer is not None:
            checkpoint["optimizer_state_dict"] = optimizer.state_dict()

        if scheduler is not None:
            checkpoint["scheduler_state_dict"] = scheduler.state_dict()

        # Save checkpoint
        model_path = checkpoint_path / "pytorch_model.bin"
        torch.save(checkpoint, model_path)

        # Save config separately
        if config:
            config_path = checkpoint_path / "config.json"
            with open(config_path, "w") as f:
                json.dump(config, f, indent=2)

        return model_path

    def _save_nemo_checkpoint(
        self,
        checkpoint_path: Path,
        model: Any,
        step: int,
        epoch: int,
        metrics: Optional[Dict[str, float]],
        config: Optional[Dict[str, Any]],
    ) -> Path:
        """Save NeMo checkpoint."""
        nemo_path = checkpoint_path / "model.nemo"
        model.save_to(str(nemo_path))

        # Save metadata
        metadata = {
            "step": step,
            "epoch": epoch,
            "metrics": metrics,
            "config": config,
        }
        metadata_path = checkpoint_path / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return nemo_path

    def _save_flux_checkpoint(
        self,
        checkpoint_path: Path,
        model: Any,
        step: int,
        epoch: int,
        metrics: Optional[Dict[str, float]],
        config: Optional[Dict[str, Any]],
    ) -> Path:
        """Save FLUX/LoRA checkpoint."""
        from torch.nn.parallel import DistributedDataParallel as DDP

        # Unwrap DDP if needed
        model_to_save = model.module if isinstance(model, DDP) else model

        # Save LoRA weights
        try:
            # If using PEFT
            model_to_save.save_pretrained(checkpoint_path)
        except AttributeError:
            # Fallback to standard PyTorch save
            torch.save(model_to_save.state_dict(), checkpoint_path / "flux_lora.bin")

        # Save metadata
        metadata = {
            "step": step,
            "epoch": epoch,
            "metrics": metrics,
            "config": config,
        }
        metadata_path = checkpoint_path / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return checkpoint_path

    def load_checkpoint(
        self,
        checkpoint_id: str,
        model: Any,
        optimizer: Optional[Any] = None,
        scheduler: Optional[Any] = None,
        model_type: str = "pytorch",
    ) -> Dict[str, Any]:
        """
        Load a checkpoint.

        Args:
            checkpoint_id: Checkpoint ID or 'latest' or 'best'
            model: Model to load weights into
            optimizer: Optimizer to load state into
            scheduler: Scheduler to load state into
            model_type: Type of model

        Returns:
            Dictionary with loaded checkpoint info
        """
        # Find checkpoint
        if checkpoint_id == "latest":
            checkpoint = self._get_latest_checkpoint(model_type)
        elif checkpoint_id == "best":
            checkpoint = self._get_best_checkpoint(model_type)
        else:
            checkpoint = self._find_checkpoint(checkpoint_id)

        if checkpoint is None:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        checkpoint_path = Path(checkpoint.file_path)

        # Load based on model type
        if model_type == "pytorch":
            return self._load_pytorch_checkpoint(
                checkpoint_path, model, optimizer, scheduler
            )
        elif model_type == "nemo":
            return self._load_nemo_checkpoint(checkpoint_path, model)
        elif model_type == "flux":
            return self._load_flux_checkpoint(checkpoint_path, model)
        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def _load_pytorch_checkpoint(
        self,
        checkpoint_path: Path,
        model: Any,
        optimizer: Optional[Any],
        scheduler: Optional[Any],
    ) -> Dict[str, Any]:
        """Load PyTorch checkpoint."""
        model_file = checkpoint_path / "pytorch_model.bin"
        checkpoint = torch.load(model_file, map_location="cpu")

        # Load model state
        from torch.nn.parallel import DistributedDataParallel as DDP
        model_to_load = model.module if isinstance(model, DDP) else model
        model_to_load.load_state_dict(checkpoint["model_state_dict"])

        # Load optimizer state
        if optimizer is not None and "optimizer_state_dict" in checkpoint:
            optimizer.load_state_dict(checkpoint["optimizer_state_dict"])

        # Load scheduler state
        if scheduler is not None and "scheduler_state_dict" in checkpoint:
            scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

        self.logger.info(f"Loaded PyTorch checkpoint from {checkpoint_path}")

        return {
            "step": checkpoint.get("step", 0),
            "epoch": checkpoint.get("epoch", 0),
            "metrics": checkpoint.get("metrics", {}),
        }

    def _load_nemo_checkpoint(
        self,
        checkpoint_path: Path,
        model: Any,
    ) -> Dict[str, Any]:
        """Load NeMo checkpoint."""
        nemo_file = checkpoint_path / "model.nemo"
        model.restore_from(str(nemo_file))

        # Load metadata
        metadata_file = checkpoint_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {}

        self.logger.info(f"Loaded NeMo checkpoint from {checkpoint_path}")

        return metadata

    def _load_flux_checkpoint(
        self,
        checkpoint_path: Path,
        model: Any,
    ) -> Dict[str, Any]:
        """Load FLUX/LoRA checkpoint."""
        from torch.nn.parallel import DistributedDataParallel as DDP

        model_to_load = model.module if isinstance(model, DDP) else model

        try:
            # If using PEFT
            from peft import PeftModel
            model_to_load = PeftModel.from_pretrained(model_to_load, checkpoint_path)
        except (ImportError, AttributeError):
            # Fallback to standard PyTorch load
            state_dict = torch.load(checkpoint_path / "flux_lora.bin", map_location="cpu")
            model_to_load.load_state_dict(state_dict)

        # Load metadata
        metadata_file = checkpoint_path / "metadata.json"
        if metadata_file.exists():
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {}

        self.logger.info(f"Loaded FLUX checkpoint from {checkpoint_path}")

        return metadata

    def _is_best_model(self, metric_value: float) -> bool:
        """Check if current metric is best."""
        if not self.checkpoints:
            return True

        best_metrics = [
            ckpt.metrics.get(self.best_metric)
            for ckpt in self.checkpoints
            if ckpt.best_model and self.best_metric in ckpt.metrics
        ]

        if not best_metrics:
            return True

        current_best = min(best_metrics) if self.best_mode == "min" else max(best_metrics)

        if self.best_mode == "min":
            return metric_value < current_best
        else:
            return metric_value > current_best

    def _cleanup_checkpoints(self, model_type: str):
        """Remove old checkpoints based on retention policy."""
        # Get checkpoints of this type
        type_checkpoints = [
            ckpt for ckpt in self.checkpoints if ckpt.model_type == model_type
        ]

        # Sort by step
        type_checkpoints.sort(key=lambda x: x.step)

        # Separate best and non-best
        best_checkpoints = [ckpt for ckpt in type_checkpoints if ckpt.best_model]
        regular_checkpoints = [ckpt for ckpt in type_checkpoints if not ckpt.best_model]

        # Remove old regular checkpoints
        if len(regular_checkpoints) > self.keep_last_n:
            to_remove = regular_checkpoints[:-self.keep_last_n]
            for ckpt in to_remove:
                self._remove_checkpoint(ckpt)

        # Remove old best checkpoints
        if len(best_checkpoints) > self.keep_best_n:
            # Sort by metric
            best_checkpoints.sort(
                key=lambda x: x.metrics.get(self.best_metric, float('inf')),
                reverse=(self.best_mode == "max")
            )
            to_remove = best_checkpoints[self.keep_best_n:]
            for ckpt in to_remove:
                self._remove_checkpoint(ckpt)

    def _remove_checkpoint(self, checkpoint: CheckpointMetadata):
        """Remove a checkpoint from disk and metadata."""
        checkpoint_path = Path(checkpoint.file_path)
        if checkpoint_path.exists():
            shutil.rmtree(checkpoint_path)
            self.logger.info(f"Removed checkpoint: {checkpoint_path}")

        self.checkpoints.remove(checkpoint)
        self._save_metadata()

    def _get_latest_checkpoint(self, model_type: str) -> Optional[CheckpointMetadata]:
        """Get the latest checkpoint of a given type."""
        type_checkpoints = [
            ckpt for ckpt in self.checkpoints if ckpt.model_type == model_type
        ]
        if not type_checkpoints:
            return None
        return max(type_checkpoints, key=lambda x: x.step)

    def _get_best_checkpoint(self, model_type: str) -> Optional[CheckpointMetadata]:
        """Get the best checkpoint of a given type."""
        best_checkpoints = [
            ckpt for ckpt in self.checkpoints
            if ckpt.model_type == model_type and ckpt.best_model
        ]
        if not best_checkpoints:
            return None

        return min(best_checkpoints, key=lambda x: x.metrics.get(self.best_metric, float('inf'))) \
            if self.best_mode == "min" else \
            max(best_checkpoints, key=lambda x: x.metrics.get(self.best_metric, float('-inf')))

    def _find_checkpoint(self, checkpoint_id: str) -> Optional[CheckpointMetadata]:
        """Find a checkpoint by ID."""
        for ckpt in self.checkpoints:
            if ckpt.checkpoint_id == checkpoint_id:
                return ckpt
        return None

    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory in bytes."""
        total = 0
        for entry in path.rglob("*"):
            if entry.is_file():
                total += entry.stat().st_size
        return total

    def list_checkpoints(self, model_type: Optional[str] = None) -> List[CheckpointMetadata]:
        """
        List all checkpoints.

        Args:
            model_type: Filter by model type (optional)

        Returns:
            List of checkpoint metadata
        """
        if model_type:
            return [ckpt for ckpt in self.checkpoints if ckpt.model_type == model_type]
        return self.checkpoints

    def get_checkpoint_info(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a checkpoint."""
        checkpoint = self._find_checkpoint(checkpoint_id)
        if checkpoint is None:
            return None
        return asdict(checkpoint)


def main():
    """Example usage of checkpoint manager."""
    print("=" * 60)
    print("Checkpoint Manager")
    print("=" * 60)

    manager = CheckpointManager(
        checkpoint_dir=CHECKPOINT_DIR,
        keep_last_n=3,
        keep_best_n=1,
        best_metric="val_loss",
        best_mode="min",
    )

    print(f"\nCheckpoint directory: {manager.checkpoint_dir}")
    print(f"Keep last N: {manager.keep_last_n}")
    print(f"Keep best N: {manager.keep_best_n}")
    print(f"Best metric: {manager.best_metric} ({manager.best_mode})")

    # List checkpoints
    checkpoints = manager.list_checkpoints()
    print(f"\nTotal checkpoints: {len(checkpoints)}")

    if checkpoints:
        print("\nCheckpoints:")
        for ckpt in checkpoints:
            print(f"  - {ckpt.checkpoint_id} (step {ckpt.step}, {ckpt.model_type})")
            if ckpt.best_model:
                print(f"    BEST MODEL")


if __name__ == "__main__":
    main()
