#!/usr/bin/env python3
"""
Iteratives Fine-Tuning mit Unsloth
====================================

Trainiert ein Small Language Model schrittweise auf Python-Code-Generierung.
"""

import argparse
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

import torch
from datasets import Dataset, load_dataset
from transformers import TrainingArguments, TrainerCallback

# Unsloth imports
try:
    from unsloth import FastLanguageModel
    from unsloth import is_bfloat16_supported
    UNSLOTH_AVAILABLE = True
except ImportError:
    print("⚠️  Unsloth not available - falling back to standard Transformers")
    UNSLOTH_AVAILABLE = False
    from transformers import AutoModelForCausalLM, AutoTokenizer

from trl import SFTTrainer

# Eigene Module
from utils import (
    load_config, save_config, save_json,
    setup_logging, set_seed, print_gpu_info,
    get_checkpoint_path, ensure_dir
)


# ============================================================================
# Callback für detailliertes Logging (didaktisch)
# ============================================================================

class DetailedLoggingCallback(TrainerCallback):
    """
    Callback für ausführliches Logging während des Trainings.
    Erklärt Studierenden, was in jeder Phase passiert.
    """

    def __init__(self, logger, iteration: int):
        self.logger = logger
        self.iteration = iteration
        self.start_time = None
        self.epoch_start_time = None

    def on_train_begin(self, args, state, control, **kwargs):
        self.logger.info("=" * 80)
        self.logger.info(f"🎓 Training startet - Iteration {self.iteration}")
        self.logger.info("=" * 80)
        self.logger.info(f"Anzahl Epochs: {args.num_train_epochs}")
        self.logger.info(f"Batch Size pro Device: {args.per_device_train_batch_size}")
        self.logger.info(f"Gradient Accumulation Steps: {args.gradient_accumulation_steps}")
        self.logger.info(f"Effektive Batch Size: {args.per_device_train_batch_size * args.gradient_accumulation_steps * args.world_size}")
        self.logger.info(f"Learning Rate: {args.learning_rate}")
        self.start_time = time.time()

    def on_epoch_begin(self, args, state, control, **kwargs):
        self.epoch_start_time = time.time()
        self.logger.info(f"\n📚 Epoch {int(state.epoch) + 1}/{int(args.num_train_epochs)} beginnt...")

    def on_epoch_end(self, args, state, control, **kwargs):
        epoch_time = time.time() - self.epoch_start_time
        self.logger.info(f"✅ Epoch {int(state.epoch)}/{int(args.num_train_epochs)} abgeschlossen in {epoch_time:.2f}s")

        if state.log_history:
            latest_log = state.log_history[-1]
            if 'loss' in latest_log:
                self.logger.info(f"   Loss: {latest_log['loss']:.4f}")

    def on_train_end(self, args, state, control, **kwargs):
        total_time = time.time() - self.start_time
        self.logger.info("\n" + "=" * 80)
        self.logger.info(f"🎉 Training abgeschlossen in {total_time:.2f}s ({total_time/60:.2f} min)")
        self.logger.info("=" * 80)


# ============================================================================
# Daten laden und vorbereiten
# ============================================================================

def load_training_data(
    data_path: str,
    prompt_template: str,
    tokenizer
) -> Dataset:
    """
    Lädt Trainingsdaten und formatiert sie.

    Args:
        data_path: Pfad zur JSON/JSONL-Datei
        prompt_template: Template für Prompts
        tokenizer: Tokenizer

    Returns:
        HuggingFace Dataset
    """

    # Daten laden
    if data_path.endswith('.jsonl'):
        dataset = load_dataset('json', data_files=data_path, split='train')
    elif data_path.endswith('.json'):
        dataset = load_dataset('json', data_files=data_path, split='train')
    else:
        raise ValueError(f"Unsupported file format: {data_path}")

    def format_sample(example):
        """Formatiert einzelnes Training-Sample."""

        # Prompt erstellen
        prompt = prompt_template.format(
            problem_description=example.get('prompt', example.get('instruction', ''))
        )

        # Mit Lösung kombinieren
        completion = example.get('canonical_solution', example.get('output', ''))

        # Vollständiger Text
        text = prompt + completion + tokenizer.eos_token

        return {"text": text}

    # Dataset formatieren
    formatted_dataset = dataset.map(format_sample, remove_columns=dataset.column_names)

    return formatted_dataset


# ============================================================================
# Modell laden (mit Unsloth)
# ============================================================================

def load_model_unsloth(
    config: Dict[str, Any],
    checkpoint_path: str = None
):
    """
    Lädt Modell mit Unsloth für schnelles Fine-Tuning.

    Args:
        config: Konfigurations-Dict
        checkpoint_path: Pfad zu Checkpoint (optional)

    Returns:
        (model, tokenizer)
    """

    model_config = config['model']
    training_config = config['training']

    # Modell-Name
    model_name = checkpoint_path if checkpoint_path else model_config['base_model']

    # Unsloth Modell laden
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_name,
        max_seq_length=2048,
        dtype=None,  # Auto-detect
        load_in_4bit=True,  # 4-bit quantization für Speicher-Effizienz
    )

    # LoRA-Adapter hinzufügen
    model = FastLanguageModel.get_peft_model(
        model,
        r=model_config['lora']['r'],
        target_modules=model_config['lora']['target_modules'],
        lora_alpha=model_config['lora']['lora_alpha'],
        lora_dropout=model_config['lora']['lora_dropout'],
        bias=model_config['lora']['bias'],
        use_gradient_checkpointing="unsloth",  # Unsloth-optimiert
        random_state=config.get('seed', 42),
    )

    return model, tokenizer


def load_model_standard(
    config: Dict[str, Any],
    checkpoint_path: str = None
):
    """
    Lädt Modell mit Standard-Transformers (Fallback).
    """

    model_config = config['model']
    model_name = checkpoint_path if checkpoint_path else model_config['base_model']

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16 if is_bfloat16_supported() else torch.float16,
        device_map="auto"
    )

    return model, tokenizer


# ============================================================================
# Training durchführen
# ============================================================================

def train_iteration(
    config: Dict[str, Any],
    iteration: int,
    train_data_path: str,
    previous_checkpoint: str = None,
    logger=None
) -> Dict[str, Any]:
    """
    Führt eine Trainings-Iteration durch.

    Args:
        config: Konfiguration
        iteration: Iterations-Nummer
        train_data_path: Pfad zu Trainingsdaten
        previous_checkpoint: Checkpoint der vorherigen Iteration
        logger: Logger

    Returns:
        Dict mit Training-Statistiken
    """

    if logger is None:
        logger = setup_logging()

    logger.info(f"\n{'='*80}")
    logger.info(f"Iteration {iteration}: Fine-Tuning beginnt")
    logger.info(f"{'='*80}\n")

    # GPU-Info
    print_gpu_info()

    # Modell laden
    logger.info("📦 Modell wird geladen...")

    if UNSLOTH_AVAILABLE and config['training']['backend'] == 'unsloth':
        model, tokenizer = load_model_unsloth(config, previous_checkpoint)
        logger.info("✅ Modell mit Unsloth geladen (schnelles Training)")
    else:
        model, tokenizer = load_model_standard(config, previous_checkpoint)
        logger.info("✅ Modell mit Standard-Transformers geladen")

    # Trainingsdaten laden
    logger.info(f"📚 Lade Trainingsdaten: {train_data_path}")
    train_dataset = load_training_data(
        train_data_path,
        config['data']['prompt_template'],
        tokenizer
    )
    logger.info(f"✅ {len(train_dataset)} Training-Samples geladen")

    # Output-Verzeichnis
    output_dir = get_checkpoint_path(
        config['model']['checkpoint_dir'],
        iteration,
        "model"
    )
    ensure_dir(output_dir)

    # Training Arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=config['training']['per_device_train_batch_size'],
        gradient_accumulation_steps=config['training']['gradient_accumulation_steps'],
        warmup_steps=config['training']['warmup_steps'],
        num_train_epochs=config['training']['num_train_epochs'],
        learning_rate=config['training']['learning_rate'],
        fp16=not is_bfloat16_supported(),
        bf16=is_bfloat16_supported(),
        logging_steps=config['training']['logging_steps'],
        save_steps=config['training']['save_steps'],
        save_total_limit=config['training']['save_total_limit'],
        optim="adamw_8bit",  # Speicher-effizient
        weight_decay=0.01,
        lr_scheduler_type="linear",
        seed=config.get('seed', 42),
        report_to=config['training'].get('report_to', []),
    )

    # Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=train_dataset,
        dataset_text_field="text",
        max_seq_length=2048,
        args=training_args,
        callbacks=[DetailedLoggingCallback(logger, iteration)]
    )

    # Training starten
    logger.info("🚀 Training startet...\n")
    start_time = time.time()

    train_result = trainer.train()

    training_time = time.time() - start_time

    # Modell speichern
    logger.info(f"\n💾 Speichere Modell nach {output_dir}")
    trainer.save_model(output_dir)

    # Statistiken sammeln
    stats = {
        "iteration": iteration,
        "training_time_seconds": training_time,
        "training_time_minutes": training_time / 60,
        "num_train_samples": len(train_dataset),
        "final_loss": train_result.training_loss,
        "num_epochs": config['training']['num_train_epochs'],
        "checkpoint_path": output_dir,
        "timestamp": datetime.now().isoformat()
    }

    # Statistiken speichern
    stats_path = get_checkpoint_path(
        config['model']['checkpoint_dir'],
        iteration,
        "stats.json"
    )
    save_json(stats, stats_path)

    logger.info("\n" + "="*80)
    logger.info("✅ Training erfolgreich abgeschlossen!")
    logger.info(f"   Zeit: {training_time/60:.2f} Minuten")
    logger.info(f"   Final Loss: {train_result.training_loss:.4f}")
    logger.info(f"   Checkpoint: {output_dir}")
    logger.info("="*80 + "\n")

    return stats


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Iteratives Fine-Tuning für Python Code-Generierung"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config.yaml",
        help="Pfad zur Konfigurationsdatei"
    )

    parser.add_argument(
        "--iteration",
        type=int,
        required=True,
        help="Iterations-Nummer"
    )

    parser.add_argument(
        "--train-data",
        type=str,
        required=True,
        help="Pfad zu Trainingsdaten (JSON/JSONL)"
    )

    parser.add_argument(
        "--previous-checkpoint",
        type=str,
        default=None,
        help="Checkpoint der vorherigen Iteration (optional)"
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random Seed (überschreibt config.yaml)"
    )

    args = parser.parse_args()

    # Konfiguration laden
    config = load_config(args.config)

    # Seed setzen
    seed = args.seed if args.seed is not None else config.get('seed', 42)
    set_seed(seed)

    # Logger einrichten
    logger = setup_logging(
        log_dir=config['logging']['log_dir'],
        log_file=f"train_iteration_{args.iteration}.log",
        level=config['logging']['level']
    )

    # Verzeichnisse erstellen
    ensure_dir(config['model']['checkpoint_dir'])
    ensure_dir(config['logging']['log_dir'])

    # Training durchführen
    try:
        stats = train_iteration(
            config=config,
            iteration=args.iteration,
            train_data_path=args.train_data,
            previous_checkpoint=args.previous_checkpoint,
            logger=logger
        )

        logger.info("✅ Alles erfolgreich!")
        return 0

    except Exception as e:
        logger.error(f"❌ Fehler beim Training: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
