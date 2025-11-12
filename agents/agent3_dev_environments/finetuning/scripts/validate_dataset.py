#!/usr/bin/env python3
"""
Dataset Validator for LLaMA Factory Fine-tuning
Validates student datasets for chat, classification, and code tasks
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class DatasetType(Enum):
    """Dataset types"""
    CHAT = "chat"
    CLASSIFICATION = "classification"
    CODE = "code"
    GENERIC = "generic"


@dataclass
class ValidationResult:
    """Validation result"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, any]


def validate_chat_dataset(data: List[Dict]) -> Tuple[List[str], List[str], Dict]:
    """
    Validate chat fine-tuning dataset

    Format: [{"instruction": "...", "input": "...", "output": "..."}]

    Args:
        data: List of dataset samples

    Returns:
        Tuple of (errors, warnings, stats)
    """
    errors = []
    warnings = []
    stats = {
        "total_samples": len(data),
        "avg_output_length": 0,
        "min_output_length": float('inf'),
        "max_output_length": 0,
        "samples_with_input": 0,
        "samples_without_input": 0
    }

    output_lengths = []

    for i, sample in enumerate(data):
        # Required fields
        if "instruction" not in sample:
            errors.append(f"Sample {i}: Missing required field 'instruction'")
        elif not sample["instruction"] or not sample["instruction"].strip():
            errors.append(f"Sample {i}: 'instruction' is empty")
        elif len(sample["instruction"]) < 5:
            warnings.append(f"Sample {i}: 'instruction' is very short (< 5 chars)")

        if "output" not in sample:
            errors.append(f"Sample {i}: Missing required field 'output'")
        elif not sample["output"] or not sample["output"].strip():
            errors.append(f"Sample {i}: 'output' is empty")
        else:
            output_len = len(sample["output"])
            output_lengths.append(output_len)

            if output_len < 10:
                warnings.append(f"Sample {i}: 'output' is very short (< 10 chars)")
            elif output_len > 4096:
                warnings.append(f"Sample {i}: 'output' is very long (> 4096 chars)")

        # Optional input field
        if "input" in sample and sample["input"]:
            stats["samples_with_input"] += 1
        else:
            stats["samples_without_input"] += 1

        # Check for unexpected fields
        expected_fields = {"instruction", "input", "output", "system", "history"}
        unexpected = set(sample.keys()) - expected_fields
        if unexpected:
            warnings.append(f"Sample {i}: Unexpected fields: {unexpected}")

    # Calculate stats
    if output_lengths:
        stats["avg_output_length"] = sum(output_lengths) / len(output_lengths)
        stats["min_output_length"] = min(output_lengths)
        stats["max_output_length"] = max(output_lengths)

    return errors, warnings, stats


def validate_classification_dataset(data: List[Dict]) -> Tuple[List[str], List[str], Dict]:
    """
    Validate classification dataset

    Args:
        data: List of dataset samples

    Returns:
        Tuple of (errors, warnings, stats)
    """
    errors = []
    warnings = []
    labels = set()
    stats = {
        "total_samples": len(data),
        "unique_labels": 0,
        "label_distribution": {}
    }

    for i, sample in enumerate(data):
        if "output" not in sample:
            errors.append(f"Sample {i}: Missing 'output' (label)")
            continue

        label = sample["output"].strip()
        if not label:
            errors.append(f"Sample {i}: Empty label")
            continue

        labels.add(label)
        stats["label_distribution"][label] = stats["label_distribution"].get(label, 0) + 1

        # Check label format
        if len(label.split()) > 3:
            warnings.append(f"Sample {i}: Label is multi-word, consider single-word labels")

        # Check for instruction
        if "instruction" not in sample or not sample["instruction"]:
            warnings.append(f"Sample {i}: Missing or empty 'instruction'")

        # Check for input text
        if "input" not in sample or not sample["input"]:
            errors.append(f"Sample {i}: Missing or empty 'input' (text to classify)")

    stats["unique_labels"] = len(labels)

    # Check label balance
    if labels:
        label_counts = list(stats["label_distribution"].values())
        max_count = max(label_counts)
        min_count = min(label_counts)
        if max_count > min_count * 3:
            warnings.append(
                f"Label imbalance detected: "
                f"max={max_count}, min={min_count}. "
                f"Consider balancing your dataset."
            )

    return errors, warnings, stats


def validate_code_dataset(data: List[Dict]) -> Tuple[List[str], List[str], Dict]:
    """
    Validate code generation dataset

    Args:
        data: List of dataset samples

    Returns:
        Tuple of (errors, warnings, stats)
    """
    errors = []
    warnings = []
    stats = {
        "total_samples": len(data),
        "avg_code_length": 0,
        "samples_with_input": 0,
        "code_languages": set()
    }

    code_lengths = []

    for i, sample in enumerate(data):
        if "output" not in sample or not sample["output"]:
            errors.append(f"Sample {i}: Missing or empty code 'output'")
            continue

        code = sample["output"]
        code_len = len(code)
        code_lengths.append(code_len)

        # Check code length
        if code_len < 20:
            warnings.append(f"Sample {i}: Code is very short (< 20 chars)")
        elif code_len > 8192:
            warnings.append(f"Sample {i}: Code is very long (> 8192 chars)")

        # Detect language (simple heuristics)
        if "def " in code or "import " in code:
            stats["code_languages"].add("Python")
        elif "function " in code or "const " in code or "let " in code:
            stats["code_languages"].add("JavaScript")
        elif "public class" in code or "private " in code:
            stats["code_languages"].add("Java")
        elif "#include" in code or "int main" in code:
            stats["code_languages"].add("C/C++")

        # Check for instruction
        if "instruction" not in sample or not sample["instruction"]:
            errors.append(f"Sample {i}: Missing or empty 'instruction'")

        # Check for input (optional for code)
        if "input" in sample and sample["input"]:
            stats["samples_with_input"] += 1

    if code_lengths:
        stats["avg_code_length"] = sum(code_lengths) / len(code_lengths)

    stats["code_languages"] = list(stats["code_languages"])

    return errors, warnings, stats


def detect_dataset_type(data: List[Dict]) -> DatasetType:
    """
    Auto-detect dataset type based on content

    Args:
        data: Dataset samples

    Returns:
        Detected dataset type
    """
    if not data:
        return DatasetType.GENERIC

    # Sample first few entries
    sample_size = min(10, len(data))
    samples = data[:sample_size]

    # Check for classification patterns
    labels = set()
    for sample in samples:
        if "output" in sample:
            output = sample["output"].strip()
            if output and len(output.split()) <= 2:  # Short outputs = likely labels
                labels.add(output)

    if len(labels) <= 10 and len(labels) >= 2:  # Limited unique short outputs
        return DatasetType.CLASSIFICATION

    # Check for code patterns
    code_keywords = ["def ", "function ", "class ", "import ", "#include", "public ", "private "]
    code_count = 0
    for sample in samples:
        if "output" in sample:
            output = sample["output"]
            if any(kw in output for kw in code_keywords):
                code_count += 1

    if code_count >= sample_size * 0.5:  # 50%+ contain code
        return DatasetType.CODE

    # Default to chat
    return DatasetType.CHAT


def validate_dataset(
    file_path: str,
    dataset_type: Optional[DatasetType] = None,
    auto_detect: bool = True
) -> ValidationResult:
    """
    Validate a dataset file

    Args:
        file_path: Path to dataset JSON file
        dataset_type: Type of dataset (auto-detected if None)
        auto_detect: Auto-detect dataset type

    Returns:
        ValidationResult object
    """
    # Load dataset
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        return ValidationResult(
            is_valid=False,
            errors=[f"File not found: {file_path}"],
            warnings=[],
            stats={}
        )
    except json.JSONDecodeError as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"Invalid JSON: {e}"],
            warnings=[],
            stats={}
        )

    # Check basic structure
    if not isinstance(data, list):
        return ValidationResult(
            is_valid=False,
            errors=["Dataset must be a JSON array"],
            warnings=[],
            stats={}
        )

    if len(data) == 0:
        return ValidationResult(
            is_valid=False,
            errors=["Dataset is empty"],
            warnings=[],
            stats={}
        )

    # Auto-detect type if needed
    if dataset_type is None and auto_detect:
        dataset_type = detect_dataset_type(data)
    elif dataset_type is None:
        dataset_type = DatasetType.GENERIC

    # Validate based on type
    if dataset_type == DatasetType.CHAT:
        errors, warnings, stats = validate_chat_dataset(data)
    elif dataset_type == DatasetType.CLASSIFICATION:
        errors, warnings, stats = validate_classification_dataset(data)
    elif dataset_type == DatasetType.CODE:
        errors, warnings, stats = validate_code_dataset(data)
    else:
        errors, warnings, stats = validate_chat_dataset(data)  # Default

    stats["dataset_type"] = dataset_type.value

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        stats=stats
    )


def print_validation_result(result: ValidationResult, verbose: bool = True):
    """Print validation result in a readable format"""

    print("\n" + "="*60)
    print("DATASET VALIDATION REPORT")
    print("="*60)

    # Status
    if result.is_valid:
        print("✅ Status: VALID")
    else:
        print("❌ Status: INVALID")

    # Stats
    print("\n📊 Statistics:")
    for key, value in result.stats.items():
        if key == "label_distribution" and isinstance(value, dict):
            print(f"  {key}:")
            for label, count in sorted(value.items(), key=lambda x: -x[1]):
                print(f"    - {label}: {count}")
        else:
            print(f"  {key}: {value}")

    # Errors
    if result.errors:
        print(f"\n❌ Errors ({len(result.errors)}):")
        for error in result.errors[:10]:  # Show first 10
            print(f"  - {error}")
        if len(result.errors) > 10:
            print(f"  ... and {len(result.errors) - 10} more errors")

    # Warnings
    if result.warnings and verbose:
        print(f"\n⚠️  Warnings ({len(result.warnings)}):")
        for warning in result.warnings[:10]:  # Show first 10
            print(f"  - {warning}")
        if len(result.warnings) > 10:
            print(f"  ... and {len(result.warnings) - 10} more warnings")

    print("\n" + "="*60 + "\n")


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate LLaMA Factory datasets for fine-tuning"
    )
    parser.add_argument(
        "file_path",
        help="Path to dataset JSON file"
    )
    parser.add_argument(
        "--type",
        choices=["chat", "classification", "code"],
        help="Dataset type (auto-detected if not specified)"
    )
    parser.add_argument(
        "--no-auto-detect",
        action="store_true",
        help="Disable auto-detection of dataset type"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only show errors, not warnings"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    args = parser.parse_args()

    # Map type string to enum
    type_map = {
        "chat": DatasetType.CHAT,
        "classification": DatasetType.CLASSIFICATION,
        "code": DatasetType.CODE
    }
    dataset_type = type_map.get(args.type) if args.type else None

    # Validate
    result = validate_dataset(
        args.file_path,
        dataset_type=dataset_type,
        auto_detect=not args.no_auto_detect
    )

    # Output
    if args.json:
        import json
        output = {
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "stats": result.stats
        }
        print(json.dumps(output, indent=2))
    else:
        print_validation_result(result, verbose=not args.quiet)

    # Exit code
    sys.exit(0 if result.is_valid else 1)


if __name__ == "__main__":
    main()
