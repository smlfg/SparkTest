#!/usr/bin/env python3
"""
Agent 7 Quick Start Example
Demonstrates basic fine-tuning with Unsloth QLoRA
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent7_lora_api import Agent7LoRAAPI


def main():
    print("=" * 70)
    print("Agent 7 Quick Start Example")
    print("=" * 70)

    # Initialize API
    api = Agent7LoRAAPI(workspace_dir="./workspace")

    # Show current registry status
    print("\n[1] Registry Status:")
    api.print_registry_info()

    # Example 1: Create Unsloth pipeline
    print("\n[2] Creating Unsloth QLoRA Pipeline:")
    print("-" * 70)
    pipeline = api.create_unsloth_pipeline(
        model_name="unsloth/llama-3-8b-bnb-4bit",
        lora_r=16,
        lora_alpha=16
    )
    print(f"✓ Pipeline created")
    print(f"  Model: {pipeline.model_name}")
    print(f"  LoRA r: {pipeline.lora_r}")
    print(f"  LoRA alpha: {pipeline.lora_alpha}")
    print(f"  Target modules: {pipeline.target_modules}")

    # Example 2: List adapters
    print("\n[3] Listing Adapters:")
    print("-" * 70)
    adapters = api.list_adapters()
    if adapters:
        for adapter in adapters:
            print(f"  • {adapter['name']}")
            print(f"    Base Model: {adapter['base_model']}")
            print(f"    Tags: {', '.join(adapter.get('tags', []))}")
    else:
        print("  No adapters registered yet.")

    # Example 3: Quick training (commented out - requires dataset)
    print("\n[4] Quick Training Example (commented out):")
    print("-" * 70)
    print("""
    To train a model, prepare your dataset and run:

    api.quick_train_unsloth(
        dataset_path="./data/train.json",
        model_name="unsloth/llama-3-8b-bnb-4bit",
        adapter_name="my_adapter",
        num_epochs=3,
        learning_rate=2e-4
    )

    Dataset format (Alpaca):
    [
        {
            "instruction": "Write a poem about AI",
            "input": "",
            "output": "Silicon dreams in neural streams..."
        }
    ]
    """)

    # Example 4: VLM pipeline
    print("\n[5] Creating VLM Pipeline:")
    print("-" * 70)
    print("Creating LLaVA fine-tuning pipeline...")
    vlm = api.create_vlm_pipeline(
        model_name="llava-hf/llava-1.5-7b-hf",
        model_type="llava",
        lora_r=8
    )
    print(f"✓ VLM Pipeline created")
    print(f"  Model: {vlm.model_name}")
    print(f"  Type: {vlm.vision_model_type}")
    print(f"  LoRA r: {vlm.lora_r}")

    # Example 5: Registry operations
    print("\n[6] Registry Operations:")
    print("-" * 70)
    print("Available operations:")
    print("  • api.list_adapters() - List all adapters")
    print("  • api.get_adapter(name) - Get adapter info")
    print("  • api.search_adapters(query) - Search adapters")
    print("  • api.load_adapter(name) - Load an adapter")
    print("  • api.merge_adapter(name, base, output) - Merge adapter")
    print("  • api.delete_adapter(name, confirm=True) - Delete adapter")

    # Example 6: Configuration
    print("\n[7] Current Configuration:")
    print("-" * 70)
    config = api.get_config()
    print(f"  Workspace: {config['workspace_dir']}")
    print(f"  LoRA Directory: {config['lora_dir']}")
    print(f"  Total Adapters: {config['total_adapters']}")
    print(f"  UI Endpoint: {config['registry']['ui_endpoint']}")

    # Next steps
    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("""
1. Launch LLaMA Factory UI:
   python agent7_lora_api.py ui

2. Quick train with Unsloth:
   from agent7_lora_api import quick_unsloth_train
   quick_unsloth_train(dataset_path="./data/train.json")

3. Fine-tune VLM:
   vlm = api.create_vlm_pipeline("llava-hf/llava-1.5-7b-hf", "llava")
   vlm.setup_model()
   # ... prepare dataset and train

4. Merge adapter:
   python agent7_lora/scripts/merge_lora_to_base.py \\
     --base-model meta-llama/Llama-3-8B \\
     --adapter ./workspace/loras/my_adapter \\
     --output ./merged_model

For more examples, see README.md
    """)


if __name__ == "__main__":
    main()
