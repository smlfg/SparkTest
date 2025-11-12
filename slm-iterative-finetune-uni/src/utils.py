"""
Hilfsfunktionen für iteratives Fine-Tuning & Evaluation
========================================================
"""

import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import torch
import yaml


# ============================================================================
# Logging-Konfiguration
# ============================================================================

def setup_logging(
    log_dir: str = "logs",
    log_file: str = "training.log",
    level: str = "INFO"
) -> logging.Logger:
    """Konfiguriert Logging für das Projekt."""

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Logger erstellen
    logger = logging.getLogger("slm_finetune")
    logger.setLevel(getattr(logging, level.upper()))

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_format)

    # File Handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_format)

    # Handler hinzufügen
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


# ============================================================================
# Konfiguration laden
# ============================================================================

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """Lädt YAML-Konfigurationsdatei."""

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def save_config(config: Dict[str, Any], output_path: str):
    """Speichert Konfiguration als YAML."""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)


# ============================================================================
# Reproduzierbarkeit
# ============================================================================

def set_seed(seed: int = 42):
    """Setzt Random Seeds für Reproduzierbarkeit."""

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)

    # Deterministic Operations (kann Performance beeinträchtigen)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


# ============================================================================
# Daten laden/speichern
# ============================================================================

def load_json(file_path: str) -> Union[Dict, List]:
    """Lädt JSON-Datei."""

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    return data


def save_json(data: Union[Dict, List], file_path: str, indent: int = 2):
    """Speichert Daten als JSON."""

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_jsonl(file_path: str) -> List[Dict]:
    """Lädt JSONL-Datei (eine JSON-Zeile pro Eintrag)."""

    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line.strip()))

    return data


def save_jsonl(data: List[Dict], file_path: str):
    """Speichert Daten als JSONL."""

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


# ============================================================================
# Prompt-Formatierung
# ============================================================================

def format_prompt(
    problem_description: str,
    prompt_template: str,
    **kwargs
) -> str:
    """Formatiert Prompt mit Template."""

    return prompt_template.format(
        problem_description=problem_description,
        **kwargs
    )


def extract_code_from_response(response: str) -> str:
    """
    Extrahiert Python-Code aus Modell-Response.

    Entfernt Markdown-Formatierung, Kommentare, etc.
    """

    # Markdown Code-Blöcke entfernen
    if "```python" in response:
        code = response.split("```python")[1].split("```")[0]
    elif "```" in response:
        code = response.split("```")[1].split("```")[0]
    else:
        code = response

    # Führende/trailing Whitespace entfernen
    code = code.strip()

    return code


# ============================================================================
# GPU-Utilities
# ============================================================================

def get_gpu_info() -> List[Dict[str, Any]]:
    """Gibt Informationen über verfügbare GPUs zurück."""

    if not torch.cuda.is_available():
        return []

    gpu_info = []
    for i in range(torch.cuda.device_count()):
        props = torch.cuda.get_device_properties(i)
        gpu_info.append({
            "id": i,
            "name": props.name,
            "total_memory_gb": props.total_memory / (1024**3),
            "compute_capability": f"{props.major}.{props.minor}"
        })

    return gpu_info


def print_gpu_info():
    """Gibt GPU-Informationen auf der Console aus."""

    gpus = get_gpu_info()

    if not gpus:
        print("❌ Keine GPUs verfügbar")
        return

    print(f"✅ {len(gpus)} GPU(s) verfügbar:")
    for gpu in gpus:
        print(f"   [{gpu['id']}] {gpu['name']} - "
              f"{gpu['total_memory_gb']:.1f} GB - "
              f"Compute {gpu['compute_capability']}")


# ============================================================================
# Checkpoint-Management
# ============================================================================

def get_checkpoint_path(
    checkpoint_dir: str,
    iteration: int,
    checkpoint_type: str = "model"
) -> str:
    """Generiert Pfad für Checkpoint."""

    checkpoint_name = f"iteration_{iteration}_{checkpoint_type}"
    return os.path.join(checkpoint_dir, checkpoint_name)


def list_checkpoints(checkpoint_dir: str) -> List[Dict[str, Any]]:
    """Listet alle verfügbaren Checkpoints auf."""

    if not os.path.exists(checkpoint_dir):
        return []

    checkpoints = []
    for item in os.listdir(checkpoint_dir):
        if item.startswith("iteration_"):
            parts = item.split("_")
            if len(parts) >= 2:
                iteration = int(parts[1])
                checkpoint_type = "_".join(parts[2:]) if len(parts) > 2 else "model"

                checkpoints.append({
                    "iteration": iteration,
                    "type": checkpoint_type,
                    "path": os.path.join(checkpoint_dir, item)
                })

    # Nach Iteration sortieren
    checkpoints.sort(key=lambda x: x["iteration"])

    return checkpoints


# ============================================================================
# Metriken-Berechnung
# ============================================================================

def calculate_token_overlap(generated: str, reference: str) -> float:
    """
    Berechnet Token-Overlap zwischen generiertem und Referenz-Code.

    Returns:
        Anteil übereinstimmender Tokens (0.0 - 1.0)
    """

    gen_tokens = set(generated.split())
    ref_tokens = set(reference.split())

    if not ref_tokens:
        return 0.0

    overlap = len(gen_tokens & ref_tokens)
    return overlap / len(ref_tokens)


def calculate_line_similarity(generated: str, reference: str) -> Dict[str, float]:
    """
    Berechnet Zeilen-basierte Ähnlichkeit.

    Returns:
        Dict mit verschiedenen Metriken
    """

    gen_lines = [l.strip() for l in generated.split('\n') if l.strip()]
    ref_lines = [l.strip() for l in reference.split('\n') if l.strip()]

    # Exakte Übereinstimmungen
    exact_matches = sum(1 for line in gen_lines if line in ref_lines)

    return {
        "gen_lines": len(gen_lines),
        "ref_lines": len(ref_lines),
        "exact_matches": exact_matches,
        "exact_match_rate": exact_matches / len(ref_lines) if ref_lines else 0.0
    }


# ============================================================================
# Fehler-Klassifikation
# ============================================================================

def classify_error(error_message: str, generated_code: str) -> str:
    """
    Klassifiziert Fehlertyp basierend auf Fehlermeldung und generiertem Code.

    Returns:
        Fehlertyp als String
    """

    error_lower = error_message.lower()

    # Syntax-Errors
    if any(keyword in error_lower for keyword in [
        "syntaxerror", "invalid syntax", "unexpected token"
    ]):
        return "syntax_error"

    # Runtime-Errors
    if any(keyword in error_lower for keyword in [
        "nameerror", "typeerror", "attributeerror", "indexerror",
        "keyerror", "valueerror", "zerodivisionerror"
    ]):
        return "runtime_error"

    # Timeout
    if "timeout" in error_lower:
        return "timeout"

    # Leere Antwort
    if not generated_code.strip():
        return "empty_response"

    # Off-Topic (kein Python-Code)
    if "def " not in generated_code and "class " not in generated_code:
        return "off_topic"

    # Logik-Fehler (falls Tests fehlschlagen, aber kein anderer Fehler)
    return "logic_error"


# ============================================================================
# File-System-Utilities
# ============================================================================

def ensure_dir(dir_path: str):
    """Erstellt Verzeichnis, falls nicht vorhanden."""
    os.makedirs(dir_path, exist_ok=True)


def get_iteration_files(
    base_dir: str,
    file_pattern: str = "iteration_{}_*.json"
) -> Dict[int, List[str]]:
    """
    Findet alle Dateien für verschiedene Iterationen.

    Args:
        base_dir: Basis-Verzeichnis
        file_pattern: Pattern mit {} als Platzhalter für Iteration

    Returns:
        Dict: {iteration_num: [file_paths]}
    """

    if not os.path.exists(base_dir):
        return {}

    iteration_files = {}

    for file in os.listdir(base_dir):
        if file.startswith("iteration_"):
            parts = file.split("_")
            if len(parts) >= 2 and parts[1].isdigit():
                iteration = int(parts[1])

                if iteration not in iteration_files:
                    iteration_files[iteration] = []

                iteration_files[iteration].append(os.path.join(base_dir, file))

    return iteration_files


# ============================================================================
# Pretty Printing
# ============================================================================

def print_section(title: str, width: int = 80):
    """Gibt formatierte Sektion-Überschrift aus."""
    print("\n" + "=" * width)
    print(f" {title} ".center(width))
    print("=" * width + "\n")


def print_metrics(metrics: Dict[str, Any], indent: int = 0):
    """Gibt Metriken formatiert aus."""
    prefix = " " * indent

    for key, value in metrics.items():
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_metrics(value, indent + 2)
        elif isinstance(value, float):
            print(f"{prefix}{key}: {value:.4f}")
        else:
            print(f"{prefix}{key}: {value}")
