"""
PyTorch Fine-tuning Playbook
Agent 6: Distributed Training with PyTorch

This playbook implements distributed fine-tuning using PyTorch's
torchrun launcher for multi-GPU training.

Features:
- Distributed Data Parallel (DDP)
- Mixed precision training
- Gradient accumulation
- Checkpoint management
- Integration with Agent 1 (multi-node) and Agent 4 (validation)
"""

import os
import sys
import torch
import torch.nn as nn
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.utils.data import DataLoader, DistributedSampler
from torch.cuda.amp import autocast, GradScaler
from pathlib import Path
from typing import Optional, Dict, Any
import json
import time
from dataclasses import dataclass
import logging

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from agent6_training_config import PYTORCH_CONFIG, CHECKPOINT_DIR, LOG_DIR


@dataclass
class TrainingArgs:
    """Training arguments configuration."""
    model_name: str
    train_data_path: str
    val_data_path: Optional[str] = None
    output_dir: str = f"{CHECKPOINT_DIR}/pytorch"
    num_epochs: int = 10
    batch_size: int = 32
    learning_rate: float = 5e-5
    mixed_precision: str = "bf16"
    gradient_accumulation_steps: int = 1
    max_grad_norm: float = 1.0
    warmup_steps: int = 100
    logging_steps: int = 10
    save_steps: int = 1000
    eval_steps: int = 500
    seed: int = 42


class PyTorchDistributedTrainer:
    """
    Distributed PyTorch training orchestrator.
    """

    def __init__(self, args: TrainingArgs):
        self.args = args
        self.setup_distributed()
        self.setup_logging()

    def setup_distributed(self):
        """Initialize distributed training."""
        if "LOCAL_RANK" in os.environ:
            self.local_rank = int(os.environ["LOCAL_RANK"])
            self.global_rank = int(os.environ["RANK"])
            self.world_size = int(os.environ["WORLD_SIZE"])

            # Initialize process group
            dist.init_process_group(backend="nccl")
            torch.cuda.set_device(self.local_rank)
            self.device = torch.device(f"cuda:{self.local_rank}")
        else:
            # Single GPU/CPU training
            self.local_rank = 0
            self.global_rank = 0
            self.world_size = 1
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.is_main_process = self.global_rank == 0

    def setup_logging(self):
        """Setup logging configuration."""
        log_level = logging.INFO if self.is_main_process else logging.WARNING
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%m/%d/%Y %H:%M:%S",
            level=log_level,
        )
        self.logger = logging.getLogger(__name__)

    def prepare_model(self, model: nn.Module) -> nn.Module:
        """
        Prepare model for distributed training.

        Args:
            model: PyTorch model

        Returns:
            DDP-wrapped model
        """
        model = model.to(self.device)

        if self.world_size > 1:
            model = DDP(
                model,
                device_ids=[self.local_rank],
                output_device=self.local_rank,
                find_unused_parameters=False,
            )

        return model

    def prepare_dataloader(
        self,
        dataset: torch.utils.data.Dataset,
        batch_size: int,
        shuffle: bool = True,
        drop_last: bool = True,
    ) -> DataLoader:
        """
        Prepare dataloader with distributed sampler.

        Args:
            dataset: PyTorch dataset
            batch_size: Batch size per process
            shuffle: Whether to shuffle data
            drop_last: Whether to drop last incomplete batch

        Returns:
            DataLoader with distributed sampler
        """
        sampler = None
        if self.world_size > 1:
            sampler = DistributedSampler(
                dataset,
                num_replicas=self.world_size,
                rank=self.global_rank,
                shuffle=shuffle,
            )
            shuffle = False  # Sampler handles shuffling

        return DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=shuffle,
            sampler=sampler,
            num_workers=4,
            pin_memory=True,
            drop_last=drop_last,
        )

    def train_epoch(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        optimizer: torch.optim.Optimizer,
        scheduler: Optional[torch.optim.lr_scheduler._LRScheduler],
        scaler: Optional[GradScaler],
        epoch: int,
    ) -> Dict[str, float]:
        """
        Train for one epoch.

        Args:
            model: Training model
            train_loader: Training data loader
            optimizer: Optimizer
            scheduler: Learning rate scheduler
            scaler: Gradient scaler for mixed precision
            epoch: Current epoch number

        Returns:
            Training metrics
        """
        model.train()
        total_loss = 0
        total_steps = 0
        start_time = time.time()

        for step, batch in enumerate(train_loader):
            # Move batch to device
            batch = {k: v.to(self.device) for k, v in batch.items()}

            # Forward pass with mixed precision
            with autocast(
                enabled=(self.args.mixed_precision in ["fp16", "bf16"]),
                dtype=torch.bfloat16 if self.args.mixed_precision == "bf16" else torch.float16
            ):
                outputs = model(**batch)
                loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]
                loss = loss / self.args.gradient_accumulation_steps

            # Backward pass
            if scaler is not None:
                scaler.scale(loss).backward()
            else:
                loss.backward()

            # Optimizer step
            if (step + 1) % self.args.gradient_accumulation_steps == 0:
                if scaler is not None:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(model.parameters(), self.args.max_grad_norm)
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), self.args.max_grad_norm)
                    optimizer.step()

                optimizer.zero_grad()
                if scheduler is not None:
                    scheduler.step()

            total_loss += loss.item() * self.args.gradient_accumulation_steps
            total_steps += 1

            # Logging
            if self.is_main_process and step % self.args.logging_steps == 0:
                avg_loss = total_loss / total_steps
                lr = optimizer.param_groups[0]["lr"]
                elapsed = time.time() - start_time
                throughput = total_steps / elapsed
                self.logger.info(
                    f"Epoch {epoch} | Step {step}/{len(train_loader)} | "
                    f"Loss: {avg_loss:.4f} | LR: {lr:.2e} | "
                    f"Throughput: {throughput:.2f} steps/s"
                )

        avg_loss = total_loss / total_steps
        return {"loss": avg_loss}

    def evaluate(
        self,
        model: nn.Module,
        eval_loader: DataLoader,
    ) -> Dict[str, float]:
        """
        Evaluate model.

        Args:
            model: Model to evaluate
            eval_loader: Evaluation data loader

        Returns:
            Evaluation metrics
        """
        model.eval()
        total_loss = 0
        total_steps = 0

        with torch.no_grad():
            for batch in eval_loader:
                batch = {k: v.to(self.device) for k, v in batch.items()}

                with autocast(
                    enabled=(self.args.mixed_precision in ["fp16", "bf16"]),
                    dtype=torch.bfloat16 if self.args.mixed_precision == "bf16" else torch.float16
                ):
                    outputs = model(**batch)
                    loss = outputs.loss if hasattr(outputs, 'loss') else outputs[0]

                total_loss += loss.item()
                total_steps += 1

        avg_loss = total_loss / total_steps

        # Gather metrics from all processes
        if self.world_size > 1:
            loss_tensor = torch.tensor([avg_loss], device=self.device)
            dist.all_reduce(loss_tensor, op=dist.ReduceOp.AVG)
            avg_loss = loss_tensor.item()

        return {"eval_loss": avg_loss}

    def save_checkpoint(
        self,
        model: nn.Module,
        optimizer: torch.optim.Optimizer,
        scheduler: Optional[torch.optim.lr_scheduler._LRScheduler],
        epoch: int,
        step: int,
        metrics: Optional[Dict[str, float]] = None,
    ):
        """
        Save training checkpoint.

        Args:
            model: Model to save
            optimizer: Optimizer state
            scheduler: Scheduler state
            epoch: Current epoch
            step: Current step
            metrics: Training metrics
        """
        if not self.is_main_process:
            return

        # Create checkpoint directory
        checkpoint_dir = Path(self.args.output_dir) / f"checkpoint-{step}"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Get model state dict (unwrap DDP if needed)
        model_to_save = model.module if isinstance(model, DDP) else model
        state_dict = model_to_save.state_dict()

        # Save checkpoint
        checkpoint = {
            "model_state_dict": state_dict,
            "optimizer_state_dict": optimizer.state_dict(),
            "epoch": epoch,
            "step": step,
            "args": vars(self.args),
        }

        if scheduler is not None:
            checkpoint["scheduler_state_dict"] = scheduler.state_dict()

        if metrics is not None:
            checkpoint["metrics"] = metrics

        torch.save(checkpoint, checkpoint_dir / "pytorch_model.bin")

        # Save config
        with open(checkpoint_dir / "training_args.json", "w") as f:
            json.dump(vars(self.args), f, indent=2)

        self.logger.info(f"Checkpoint saved to {checkpoint_dir}")

        # Keep only last N checkpoints
        self._cleanup_checkpoints()

    def _cleanup_checkpoints(self):
        """Remove old checkpoints, keeping only the last N."""
        checkpoint_dirs = sorted(
            Path(self.args.output_dir).glob("checkpoint-*"),
            key=lambda x: int(x.name.split("-")[1])
        )

        keep_last_n = PYTORCH_CONFIG["checkpoint"]["keep_last_n"]
        for checkpoint_dir in checkpoint_dirs[:-keep_last_n]:
            import shutil
            shutil.rmtree(checkpoint_dir)
            self.logger.info(f"Removed old checkpoint: {checkpoint_dir}")

    def train(
        self,
        model: nn.Module,
        train_dataset: torch.utils.data.Dataset,
        eval_dataset: Optional[torch.utils.data.Dataset] = None,
        optimizer: Optional[torch.optim.Optimizer] = None,
        scheduler: Optional[torch.optim.lr_scheduler._LRScheduler] = None,
    ):
        """
        Main training loop.

        Args:
            model: Model to train
            train_dataset: Training dataset
            eval_dataset: Evaluation dataset
            optimizer: Optimizer (created if None)
            scheduler: LR scheduler (created if None)
        """
        # Prepare model and data
        model = self.prepare_model(model)
        train_loader = self.prepare_dataloader(train_dataset, self.args.batch_size)
        eval_loader = None
        if eval_dataset is not None:
            eval_loader = self.prepare_dataloader(
                eval_dataset, self.args.batch_size, shuffle=False
            )

        # Setup optimizer
        if optimizer is None:
            optimizer = torch.optim.AdamW(
                model.parameters(),
                lr=self.args.learning_rate,
                **PYTORCH_CONFIG["optimizer"],
            )

        # Setup scheduler
        if scheduler is None and self.args.warmup_steps > 0:
            from torch.optim.lr_scheduler import LinearLR, SequentialLR
            warmup_scheduler = LinearLR(
                optimizer,
                start_factor=0.1,
                total_iters=self.args.warmup_steps
            )
            scheduler = warmup_scheduler

        # Setup mixed precision
        scaler = None
        if self.args.mixed_precision in ["fp16", "bf16"]:
            scaler = GradScaler(enabled=(self.args.mixed_precision == "fp16"))

        # Training loop
        global_step = 0
        for epoch in range(self.args.num_epochs):
            if self.is_main_process:
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"Epoch {epoch + 1}/{self.args.num_epochs}")
                self.logger.info(f"{'='*60}")

            # Set epoch for distributed sampler
            if self.world_size > 1 and hasattr(train_loader.sampler, "set_epoch"):
                train_loader.sampler.set_epoch(epoch)

            # Train epoch
            train_metrics = self.train_epoch(
                model, train_loader, optimizer, scheduler, scaler, epoch
            )

            # Evaluate
            if eval_loader is not None:
                eval_metrics = self.evaluate(model, eval_loader)
                if self.is_main_process:
                    self.logger.info(f"Evaluation: {eval_metrics}")
            else:
                eval_metrics = {}

            # Save checkpoint
            global_step += len(train_loader)
            metrics = {**train_metrics, **eval_metrics}
            self.save_checkpoint(model, optimizer, scheduler, epoch, global_step, metrics)

        if self.is_main_process:
            self.logger.info("Training completed!")

        # Cleanup
        if self.world_size > 1:
            dist.destroy_process_group()


def main():
    """Main entry point for PyTorch fine-tuning."""
    # Example usage
    args = TrainingArgs(
        model_name="gpt2",
        train_data_path="/workspace/data/train",
        val_data_path="/workspace/data/val",
        output_dir=f"{CHECKPOINT_DIR}/pytorch/gpt2",
        num_epochs=3,
        batch_size=8,
        learning_rate=5e-5,
    )

    trainer = PyTorchDistributedTrainer(args)

    # Load model (example with HuggingFace)
    try:
        from transformers import AutoModelForCausalLM
        model = AutoModelForCausalLM.from_pretrained(args.model_name)
    except ImportError:
        print("Install transformers: pip install transformers")
        return

    # Create dummy dataset (replace with actual data)
    from torch.utils.data import TensorDataset
    dummy_data = torch.randn(1000, 128)
    dummy_labels = torch.randint(0, 2, (1000,))
    train_dataset = TensorDataset(dummy_data, dummy_labels)
    eval_dataset = TensorDataset(dummy_data[:100], dummy_labels[:100])

    # Train
    trainer.train(model, train_dataset, eval_dataset)


if __name__ == "__main__":
    main()
