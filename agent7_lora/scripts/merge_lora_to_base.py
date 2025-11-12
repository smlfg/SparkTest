#!/usr/bin/env python3
"""
Merge LoRA Adapter to Base Model
Standalone script for merging LoRA adapters with base models
"""

import argparse
import sys
from pathlib import Path
import torch
from typing import Optional


def merge_lora_to_base(
    base_model_path: str,
    adapter_path: str,
    output_path: str,
    device: str = "auto",
    max_shard_size: str = "5GB",
    safe_serialization: bool = True
):
    """
    Merge LoRA adapter with base model.

    Args:
        base_model_path: Path or HuggingFace model name for base model
        adapter_path: Path to LoRA adapter directory
        output_path: Path to save merged model
        device: Device to use ('cuda', 'cpu', or 'auto')
        max_shard_size: Maximum shard size for model files
        safe_serialization: Use safe tensors format
    """
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel, PeftConfig
    except ImportError:
        print("Error: Required packages not installed")
        print("Install with: pip install transformers peft accelerate")
        sys.exit(1)

    print("=" * 70)
    print("LoRA Merge Utility")
    print("=" * 70)

    # Load adapter config first to get base model info
    print(f"\n[1/5] Loading adapter configuration...")
    try:
        adapter_config = PeftConfig.from_pretrained(adapter_path)
        print(f"✓ Adapter loaded from: {adapter_path}")
        print(f"  Base model: {adapter_config.base_model_name_or_path}")
        print(f"  Task type: {adapter_config.task_type}")
        print(f"  LoRA r: {adapter_config.r}")
        print(f"  LoRA alpha: {adapter_config.lora_alpha}")
    except Exception as e:
        print(f"✗ Error loading adapter config: {e}")
        sys.exit(1)

    # Load base model
    print(f"\n[2/5] Loading base model: {base_model_path}")
    try:
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_path,
            torch_dtype=torch.float16,
            device_map=device,
            trust_remote_code=True
        )
        print(f"✓ Base model loaded")
        print(f"  Parameters: {base_model.num_parameters():,}")
        print(f"  Memory footprint: {base_model.get_memory_footprint() / 1e9:.2f} GB")
    except Exception as e:
        print(f"✗ Error loading base model: {e}")
        sys.exit(1)

    # Load LoRA adapter
    print(f"\n[3/5] Loading LoRA adapter...")
    try:
        model = PeftModel.from_pretrained(base_model, adapter_path)
        print(f"✓ LoRA adapter loaded and applied")

        # Print trainable parameters
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        all_params = sum(p.numel() for p in model.parameters())
        print(f"  Trainable params: {trainable_params:,} ({100 * trainable_params / all_params:.2f}%)")
    except Exception as e:
        print(f"✗ Error loading adapter: {e}")
        sys.exit(1)

    # Merge adapter
    print(f"\n[4/5] Merging adapter with base model...")
    try:
        merged_model = model.merge_and_unload()
        print(f"✓ Adapter merged successfully")
    except Exception as e:
        print(f"✗ Error merging adapter: {e}")
        sys.exit(1)

    # Save merged model
    print(f"\n[5/5] Saving merged model to: {output_path}")
    try:
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        merged_model.save_pretrained(
            output_path,
            max_shard_size=max_shard_size,
            safe_serialization=safe_serialization
        )
        print(f"✓ Model saved")

        # Save tokenizer
        print(f"  Saving tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(base_model_path, trust_remote_code=True)
        tokenizer.save_pretrained(output_path)
        print(f"✓ Tokenizer saved")

        # Print output info
        total_size = sum(f.stat().st_size for f in output_path.rglob("*") if f.is_file())
        print(f"\n  Total size: {total_size / 1e9:.2f} GB")
        print(f"  Files: {len(list(output_path.rglob('*')))}")

    except Exception as e:
        print(f"✗ Error saving model: {e}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("✓ Merge completed successfully!")
    print("=" * 70)
    print(f"\nMerged model saved to: {output_path}")
    print("\nTo use the merged model:")
    print(f"  from transformers import AutoModelForCausalLM")
    print(f"  model = AutoModelForCausalLM.from_pretrained('{output_path}')")


def verify_paths(base_model: str, adapter_path: str, output_path: str) -> bool:
    """Verify that paths are valid."""
    adapter_path = Path(adapter_path)

    # Check adapter path exists
    if not adapter_path.exists():
        print(f"Error: Adapter path does not exist: {adapter_path}")
        return False

    # Check for adapter config
    if not (adapter_path / "adapter_config.json").exists():
        print(f"Error: No adapter_config.json found in {adapter_path}")
        return False

    # Check output path doesn't exist (or confirm overwrite)
    output_path = Path(output_path)
    if output_path.exists():
        response = input(f"Output path {output_path} exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Merge cancelled")
            return False

    return True


def main():
    parser = argparse.ArgumentParser(
        description="Merge LoRA adapter with base model",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Merge with local base model
  python merge_lora_to_base.py \\
    --base-model /path/to/base/model \\
    --adapter /path/to/lora/adapter \\
    --output /path/to/merged/model

  # Merge with HuggingFace model
  python merge_lora_to_base.py \\
    --base-model meta-llama/Llama-3-8B \\
    --adapter ./my_adapter \\
    --output ./merged_model

  # Merge with specific device
  python merge_lora_to_base.py \\
    --base-model meta-llama/Llama-3-8B \\
    --adapter ./my_adapter \\
    --output ./merged_model \\
    --device cuda:0
        """
    )

    parser.add_argument(
        "--base-model",
        type=str,
        required=True,
        help="Path to base model or HuggingFace model name"
    )
    parser.add_argument(
        "--adapter",
        type=str,
        required=True,
        help="Path to LoRA adapter directory"
    )
    parser.add_argument(
        "--output",
        type=str,
        required=True,
        help="Path to save merged model"
    )
    parser.add_argument(
        "--device",
        type=str,
        default="auto",
        help="Device to use for merging (cuda, cpu, or auto)"
    )
    parser.add_argument(
        "--max-shard-size",
        type=str,
        default="5GB",
        help="Maximum size for model shards"
    )
    parser.add_argument(
        "--no-safe-serialization",
        action="store_true",
        help="Disable safe tensors format"
    )
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip path verification"
    )

    args = parser.parse_args()

    # Verify paths
    if not args.skip_verification:
        if not verify_paths(args.base_model, args.adapter, args.output):
            sys.exit(1)

    # Perform merge
    merge_lora_to_base(
        base_model_path=args.base_model,
        adapter_path=args.adapter,
        output_path=args.output,
        device=args.device,
        max_shard_size=args.max_shard_size,
        safe_serialization=not args.no_safe_serialization
    )


if __name__ == "__main__":
    main()
