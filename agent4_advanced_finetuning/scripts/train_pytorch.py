"""
PyTorch Fine-tuning Script for Agent 4
Supports LoRA, full fine-tuning, and various optimization strategies
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, random_split
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    get_scheduler,
    set_seed
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from tqdm import tqdm
import yaml

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from utils.experiment_logger import ExperimentLogger


class InstructionDataset(Dataset):
    """Dataset for instruction-following fine-tuning"""

    def __init__(
        self,
        data_path: str,
        tokenizer,
        max_length: int = 2048,
        template: str = "alpaca"
    ):
        with open(data_path) as f:
            self.data = json.load(f)

        self.tokenizer = tokenizer
        self.max_length = max_length
        self.template = template

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]

        # Format based on template
        if self.template == "alpaca":
            if item.get("input", ""):
                prompt = f"### Instruction:\n{item['instruction']}\n\n### Input:\n{item['input']}\n\n### Response:\n{item['output']}"
            else:
                prompt = f"### Instruction:\n{item['instruction']}\n\n### Response:\n{item['output']}"
        else:
            prompt = f"{item['instruction']}\n{item['output']}"

        # Tokenize
        encoded = self.tokenizer(
            prompt,
            truncation=True,
            max_length=self.max_length,
            padding="max_length",
            return_tensors="pt"
        )

        return {
            "input_ids": encoded["input_ids"].squeeze(),
            "attention_mask": encoded["attention_mask"].squeeze(),
            "labels": encoded["input_ids"].squeeze()
        }


def load_config(config_path: str) -> Dict[str, Any]:
    """Load YAML configuration file"""
    with open(config_path) as f:
        config = yaml.safe_load(f)
    return config


def setup_model_and_tokenizer(config: Dict[str, Any]):
    """
    Load model and tokenizer with optional LoRA

    Returns:
        tuple: (model, tokenizer)
    """
    model_config = config["model"]
    lora_config = config.get("lora", {})

    print(f"Loading model: {model_config['name_or_path']}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        model_config["name_or_path"],
        trust_remote_code=model_config.get("trust_remote_code", False)
    )

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # Load model
    model_kwargs = {
        "trust_remote_code": model_config.get("trust_remote_code", False)
    }

    if model_config.get("load_in_8bit", False):
        model_kwargs["load_in_8bit"] = True
        model_kwargs["device_map"] = model_config.get("device_map", "auto")

    model = AutoModelForCausalLM.from_pretrained(
        model_config["name_or_path"],
        **model_kwargs
    )

    # Apply LoRA if enabled
    if lora_config.get("enabled", False):
        print("Applying LoRA configuration...")

        if model_config.get("load_in_8bit", False):
            model = prepare_model_for_kbit_training(model)

        peft_config = LoraConfig(
            r=lora_config["r"],
            lora_alpha=lora_config["lora_alpha"],
            lora_dropout=lora_config["lora_dropout"],
            target_modules=lora_config["target_modules"],
            bias=lora_config.get("bias", "none"),
            task_type=lora_config.get("task_type", "CAUSAL_LM")
        )

        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()

    return model, tokenizer


def setup_dataloaders(config: Dict[str, Any], tokenizer) -> tuple:
    """
    Create training and validation dataloaders

    Returns:
        tuple: (train_loader, val_loader)
    """
    dataset_config = config["dataset"]

    # Load dataset
    full_dataset = InstructionDataset(
        data_path=dataset_config["path"],
        tokenizer=tokenizer,
        max_length=dataset_config.get("max_seq_length", 2048),
        template=dataset_config.get("preprocessing", {}).get("template", "alpaca")
    )

    # Split into train/val
    train_size = int(len(full_dataset) * dataset_config.get("train_split", 0.9))
    val_size = len(full_dataset) - train_size

    train_dataset, val_dataset = random_split(
        full_dataset,
        [train_size, val_size],
        generator=torch.Generator().manual_seed(config.get("seed", 42))
    )

    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=config["training"]["batch_size"],
        shuffle=True,
        num_workers=config.get("hardware", {}).get("num_workers", 4),
        pin_memory=config.get("hardware", {}).get("pin_memory", True)
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=config["training"]["batch_size"],
        shuffle=False,
        num_workers=config.get("hardware", {}).get("num_workers", 4),
        pin_memory=config.get("hardware", {}).get("pin_memory", True)
    )

    print(f"Dataset loaded: {len(train_dataset)} train, {len(val_dataset)} val samples")

    return train_loader, val_loader


def train_epoch(
    model,
    train_loader,
    optimizer,
    scheduler,
    device,
    gradient_accumulation_steps: int = 1,
    max_grad_norm: float = 1.0
):
    """Train for one epoch"""
    model.train()
    total_loss = 0
    num_batches = 0

    progress_bar = tqdm(train_loader, desc="Training")

    for step, batch in enumerate(progress_bar):
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        labels = batch["labels"].to(device)

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            labels=labels
        )

        loss = outputs.loss / gradient_accumulation_steps
        loss.backward()

        if (step + 1) % gradient_accumulation_steps == 0:
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_grad_norm)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

        total_loss += loss.item() * gradient_accumulation_steps
        num_batches += 1

        progress_bar.set_postfix({"loss": total_loss / num_batches})

    return total_loss / num_batches


def evaluate(model, val_loader, device):
    """Evaluate model on validation set"""
    model.eval()
    total_loss = 0
    num_batches = 0

    with torch.no_grad():
        for batch in tqdm(val_loader, desc="Evaluating"):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["labels"].to(device)

            outputs = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels
            )

            total_loss += outputs.loss.item()
            num_batches += 1

    avg_loss = total_loss / num_batches
    perplexity = torch.exp(torch.tensor(avg_loss)).item()

    return {
        "eval_loss": avg_loss,
        "perplexity": perplexity
    }


def save_checkpoint(model, tokenizer, output_dir: str, epoch: int):
    """Save model checkpoint"""
    checkpoint_dir = Path(output_dir) / f"checkpoint-epoch-{epoch}"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    model.save_pretrained(checkpoint_dir)
    tokenizer.save_pretrained(checkpoint_dir)

    print(f"💾 Checkpoint saved: {checkpoint_dir}")
    return str(checkpoint_dir)


def main():
    parser = argparse.ArgumentParser(description="PyTorch Fine-tuning Script")
    parser.add_argument("--config", type=str, required=True, help="Path to config YAML file")
    parser.add_argument("--dataset", type=str, help="Override dataset path")
    parser.add_argument("--checkpoint_dir", type=str, help="Override checkpoint directory")
    parser.add_argument("--resume", type=str, help="Resume from checkpoint")
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Override config with CLI arguments
    if args.dataset:
        config["dataset"]["path"] = args.dataset
    if args.checkpoint_dir:
        config["checkpointing"]["output_dir"] = args.checkpoint_dir

    # Set seed for reproducibility
    seed = config.get("seed", 42)
    set_seed(seed)

    # Setup device
    device = torch.device("cuda" if torch.cuda.is_available() and config.get("hardware", {}).get("use_cuda", True) else "cpu")
    print(f"Using device: {device}")

    # Initialize experiment logger
    experiment_name = config.get("experiment", {}).get("name", "unnamed-experiment")
    experiment_dir = config.get("experiment", {}).get("output_dir", "/workspace/experiments")
    logger = ExperimentLogger(experiment_name, output_dir=experiment_dir)

    # Log configuration
    logger.log_config(config)

    # Setup model and tokenizer
    model, tokenizer = setup_model_and_tokenizer(config)
    model.to(device)

    # Setup dataloaders
    train_loader, val_loader = setup_dataloaders(config, tokenizer)

    # Log dataset info
    logger.log_dataset_info({
        "path": config["dataset"]["path"],
        "train_samples": len(train_loader.dataset),
        "val_samples": len(val_loader.dataset),
        "max_seq_length": config["dataset"].get("max_seq_length", 2048)
    })

    # Setup optimizer
    training_config = config["training"]
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=training_config["learning_rate"],
        weight_decay=training_config.get("weight_decay", 0.01)
    )

    # Setup learning rate scheduler
    num_training_steps = len(train_loader) * training_config["num_epochs"] // training_config.get("gradient_accumulation_steps", 1)
    num_warmup_steps = int(num_training_steps * training_config.get("warmup_ratio", 0.1))

    scheduler = get_scheduler(
        name=training_config.get("lr_scheduler_type", "cosine"),
        optimizer=optimizer,
        num_warmup_steps=num_warmup_steps,
        num_training_steps=num_training_steps
    )

    print(f"\n🚀 Starting training for {training_config['num_epochs']} epochs...")
    print(f"📊 Total training steps: {num_training_steps}")
    print(f"🔥 Warmup steps: {num_warmup_steps}\n")

    # Training loop
    best_eval_loss = float('inf')

    try:
        for epoch in range(1, training_config["num_epochs"] + 1):
            print(f"\n{'='*70}")
            print(f"Epoch {epoch}/{training_config['num_epochs']}")
            print(f"{'='*70}")

            # Train
            train_loss = train_epoch(
                model=model,
                train_loader=train_loader,
                optimizer=optimizer,
                scheduler=scheduler,
                device=device,
                gradient_accumulation_steps=training_config.get("gradient_accumulation_steps", 1),
                max_grad_norm=training_config.get("max_grad_norm", 1.0)
            )

            # Evaluate
            if config.get("evaluation", {}).get("strategy") != "no":
                eval_metrics = evaluate(model, val_loader, device)
            else:
                eval_metrics = {}

            # Log metrics
            metrics = {
                "train_loss": train_loss,
                "learning_rate": scheduler.get_last_lr()[0],
                **eval_metrics
            }
            logger.log_metric(epoch, metrics)

            # Save checkpoint
            checkpoint_strategy = config.get("checkpointing", {}).get("save_strategy", "epoch")
            if checkpoint_strategy == "epoch":
                checkpoint_path = save_checkpoint(
                    model,
                    tokenizer,
                    config["checkpointing"]["output_dir"],
                    epoch
                )
                logger.log_checkpoint(epoch, checkpoint_path)

            # Track best model
            eval_loss = eval_metrics.get("eval_loss", float('inf'))
            if eval_loss < best_eval_loss:
                best_eval_loss = eval_loss
                print(f"🏆 New best model! eval_loss: {eval_loss:.4f}")

        # Training completed successfully
        logger.finalize("completed")
        print("\n✅ Training completed successfully!")

    except Exception as e:
        logger.log_error(str(e))
        logger.finalize("failed")
        print(f"\n❌ Training failed: {e}")
        raise

    finally:
        # Save experiment log
        logger.save()

    print(f"\n{'='*70}")
    print(f"Best validation loss: {best_eval_loss:.4f}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    main()
