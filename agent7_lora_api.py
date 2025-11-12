"""
Agent 7: Fine-tuning - Unsloth/LLaMA Factory
LoRA Fine-tuning API and Management Interface

Provides unified access to:
- Unsloth QLoRA pipeline (memory-efficient fine-tuning)
- LLaMA Factory web UI (all-in-one GUI)
- VLM fine-tuning (Vision-Language Models)
- LoRA adapter registry and management
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add agent7_lora to path
sys.path.insert(0, str(Path(__file__).parent / "agent7_lora"))

from pipelines.unsloth_qlora import UnslothQLoRAPipeline, create_training_config
from ui.llama_factory_launcher import LLaMAFactoryUI, quick_launch
from vlm.vlm_finetuning import VLMFineTuner, LLaVAFineTuner, QwenVLFineTuner
from adapters.lora_manager import LoRARegistry, LoRALoader, print_adapter_info


# ============================================================================
# LORA REGISTRY CONFIGURATION
# ============================================================================

LORA_REGISTRY = {
    "adapters": "/workspace/loras",
    "merge_script": "agent7_lora/scripts/merge_lora_to_base.py",
    "ui_endpoint": "http://localhost:7860"
}


# ============================================================================
# MAIN API CLASS
# ============================================================================

class Agent7LoRAAPI:
    """
    Main API interface for Agent 7 fine-tuning capabilities.
    """

    def __init__(self, workspace_dir: str = "./workspace"):
        """
        Initialize Agent 7 LoRA API.

        Args:
            workspace_dir: Root workspace directory
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.lora_dir = self.workspace_dir / "loras"
        self.lora_dir.mkdir(parents=True, exist_ok=True)

        self.registry = LoRARegistry(registry_dir=str(self.lora_dir))
        self.loader = LoRALoader()

        # Update global registry
        LORA_REGISTRY["adapters"] = str(self.lora_dir)

    # ========================================================================
    # Unsloth QLoRA Methods
    # ========================================================================

    def create_unsloth_pipeline(
        self,
        model_name: str = "unsloth/llama-3-8b-bnb-4bit",
        lora_r: int = 16,
        lora_alpha: int = 16,
        **kwargs
    ) -> UnslothQLoRAPipeline:
        """
        Create an Unsloth QLoRA fine-tuning pipeline.

        Args:
            model_name: Base model name
            lora_r: LoRA rank
            lora_alpha: LoRA alpha
            **kwargs: Additional pipeline parameters

        Returns:
            Configured UnslothQLoRAPipeline instance
        """
        pipeline = UnslothQLoRAPipeline(
            model_name=model_name,
            lora_r=lora_r,
            lora_alpha=lora_alpha,
            **kwargs
        )
        return pipeline

    def quick_train_unsloth(
        self,
        dataset_path: str,
        model_name: str = "unsloth/llama-3-8b-bnb-4bit",
        adapter_name: str = "my_adapter",
        num_epochs: int = 3,
        learning_rate: float = 2e-4,
        **kwargs
    ):
        """
        Quick training with Unsloth (simplified interface).

        Args:
            dataset_path: Path to training dataset
            model_name: Base model name
            adapter_name: Name for output adapter
            num_epochs: Number of training epochs
            learning_rate: Learning rate
            **kwargs: Additional training parameters

        Returns:
            Trained pipeline
        """
        print("\n" + "=" * 70)
        print("Unsloth QLoRA Quick Training")
        print("=" * 70)

        # Create pipeline
        pipeline = self.create_unsloth_pipeline(model_name=model_name)

        # Setup model
        if not pipeline.setup_model():
            print("Failed to setup model")
            return None

        # Prepare dataset
        dataset = pipeline.prepare_dataset(dataset_path)
        if dataset is None:
            print("Failed to prepare dataset")
            return None

        # Train
        output_dir = self.lora_dir / adapter_name
        trainer = pipeline.train(
            dataset=dataset,
            output_dir=str(output_dir),
            num_train_epochs=num_epochs,
            learning_rate=learning_rate,
            **kwargs
        )

        # Save adapter
        pipeline.save_lora_adapter(str(output_dir), adapter_name=adapter_name)

        # Register adapter
        self.registry.register_adapter(
            adapter_path=str(output_dir),
            adapter_name=adapter_name,
            base_model=model_name,
            description=f"Fine-tuned with Unsloth QLoRA",
            tags=["unsloth", "qlora"],
            metadata={
                "num_epochs": num_epochs,
                "learning_rate": learning_rate,
                "lora_r": pipeline.lora_r,
                "lora_alpha": pipeline.lora_alpha
            }
        )

        print(f"\n✓ Training complete! Adapter saved as '{adapter_name}'")
        return pipeline

    # ========================================================================
    # LLaMA Factory UI Methods
    # ========================================================================

    def launch_llama_factory(self, port: int = 7860, share: bool = False):
        """
        Launch LLaMA Factory web UI.

        Args:
            port: Port for web interface
            share: Create public share link
        """
        ui = LLaMAFactoryUI(
            workspace_dir=str(self.workspace_dir),
            lora_output_dir=str(self.lora_dir),
            port=port,
            share=share
        )

        LORA_REGISTRY["ui_endpoint"] = f"http://localhost:{port}"

        print("\n" + "=" * 70)
        print("LLaMA Factory Web UI")
        print("=" * 70)
        print(f"\nEndpoint: {LORA_REGISTRY['ui_endpoint']}")
        print(f"LoRA Directory: {self.lora_dir}")
        print("\n")

        ui.launch_ui()

    # ========================================================================
    # VLM Fine-tuning Methods
    # ========================================================================

    def create_vlm_pipeline(
        self,
        model_name: str,
        model_type: str = "llava",
        lora_r: int = 8,
        **kwargs
    ) -> VLMFineTuner:
        """
        Create a Vision-Language Model fine-tuning pipeline.

        Args:
            model_name: Base VLM model name
            model_type: Type of VLM (llava, qwen-vl, etc.)
            lora_r: LoRA rank
            **kwargs: Additional parameters

        Returns:
            Configured VLMFineTuner instance
        """
        if "llava" in model_type.lower():
            pipeline = LLaVAFineTuner(model_name=model_name, lora_r=lora_r, **kwargs)
        elif "qwen" in model_type.lower():
            pipeline = QwenVLFineTuner(model_name=model_name, lora_r=lora_r, **kwargs)
        else:
            pipeline = VLMFineTuner(
                model_name=model_name,
                vision_model_type=model_type,
                lora_r=lora_r,
                **kwargs
            )

        return pipeline

    # ========================================================================
    # LoRA Adapter Management Methods
    # ========================================================================

    def list_adapters(self, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List all registered LoRA adapters.

        Args:
            tags: Filter by tags

        Returns:
            List of adapter information
        """
        return self.registry.list_adapters(tags=tags)

    def get_adapter(self, adapter_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific adapter."""
        return self.registry.get_adapter(adapter_name)

    def load_adapter(self, adapter_name: str, base_model=None):
        """
        Load a LoRA adapter.

        Args:
            adapter_name: Name of registered adapter
            base_model: Optional base model to apply adapter to

        Returns:
            Loaded adapter or model with adapter
        """
        adapter_path = self.registry.get_adapter_path(adapter_name)
        if adapter_path is None:
            print(f"Error: Adapter '{adapter_name}' not found in registry")
            return None

        return self.loader.load_adapter(adapter_path, base_model=base_model)

    def merge_adapter(
        self,
        adapter_name: str,
        base_model_path: str,
        output_path: str,
        device: str = "cuda"
    ):
        """
        Merge a LoRA adapter with its base model.

        Args:
            adapter_name: Name of registered adapter
            base_model_path: Path to base model
            output_path: Output path for merged model
            device: Device for merging

        Returns:
            True if successful
        """
        adapter_path = self.registry.get_adapter_path(adapter_name)
        if adapter_path is None:
            print(f"Error: Adapter '{adapter_name}' not found in registry")
            return False

        return self.loader.merge_adapter(
            base_model_path=base_model_path,
            adapter_path=adapter_path,
            output_path=output_path,
            device=device
        )

    def search_adapters(self, query: str) -> List[Dict[str, Any]]:
        """Search adapters by name, description, or tags."""
        return self.registry.search_adapters(query)

    def delete_adapter(self, adapter_name: str, confirm: bool = False):
        """Delete an adapter from registry."""
        return self.registry.delete_adapter(adapter_name, confirm=confirm)

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def print_registry_info(self):
        """Print information about the LoRA registry."""
        print("\n" + "=" * 70)
        print("Agent 7 - LoRA Registry")
        print("=" * 70)
        print(f"\nRegistry Directory: {self.lora_dir}")
        print(f"Merge Script: {LORA_REGISTRY['merge_script']}")
        print(f"UI Endpoint: {LORA_REGISTRY['ui_endpoint']}")

        adapters = self.list_adapters()
        print(f"\nTotal Adapters: {len(adapters)}")

        if adapters:
            print("\nRegistered Adapters:")
            for adapter in adapters:
                print(f"\n  • {adapter['name']}")
                print(f"    Base Model: {adapter['base_model']}")
                print(f"    Tags: {', '.join(adapter.get('tags', []))}")
                print(f"    Path: {adapter['path']}")
        else:
            print("\nNo adapters registered yet.")

        print("\n" + "=" * 70)

    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return {
            "workspace_dir": str(self.workspace_dir),
            "lora_dir": str(self.lora_dir),
            "registry": LORA_REGISTRY,
            "total_adapters": len(self.list_adapters())
        }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_api(workspace_dir: str = "./workspace") -> Agent7LoRAAPI:
    """Get Agent 7 API instance."""
    return Agent7LoRAAPI(workspace_dir=workspace_dir)


def quick_unsloth_train(
    dataset_path: str,
    model_name: str = "unsloth/llama-3-8b-bnb-4bit",
    adapter_name: str = "my_adapter",
    **kwargs
):
    """Quick Unsloth training (convenience function)."""
    api = get_api()
    return api.quick_train_unsloth(
        dataset_path=dataset_path,
        model_name=model_name,
        adapter_name=adapter_name,
        **kwargs
    )


def launch_ui(port: int = 7860, share: bool = False):
    """Launch LLaMA Factory UI (convenience function)."""
    api = get_api()
    api.launch_llama_factory(port=port, share=share)


# ============================================================================
# MAIN / CLI
# ============================================================================

def main():
    """Main CLI interface."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Agent 7: LoRA Fine-tuning API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch LLaMA Factory UI
  python agent7_lora_api.py ui

  # List all adapters
  python agent7_lora_api.py list

  # Show registry info
  python agent7_lora_api.py info

  # Search adapters
  python agent7_lora_api.py search "llama"
        """
    )

    parser.add_argument(
        "command",
        choices=["ui", "list", "info", "search"],
        help="Command to execute"
    )
    parser.add_argument(
        "args",
        nargs="*",
        help="Additional arguments for command"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=7860,
        help="Port for UI (default: 7860)"
    )
    parser.add_argument(
        "--share",
        action="store_true",
        help="Create public share link for UI"
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default="./workspace",
        help="Workspace directory"
    )

    args = parser.parse_args()

    # Initialize API
    api = Agent7LoRAAPI(workspace_dir=args.workspace)

    # Execute command
    if args.command == "ui":
        api.launch_llama_factory(port=args.port, share=args.share)

    elif args.command == "list":
        adapters = api.list_adapters()
        if adapters:
            print(f"\nFound {len(adapters)} adapter(s):\n")
            for adapter in adapters:
                print(f"  • {adapter['name']}")
                print(f"    Base: {adapter['base_model']}")
                print(f"    Tags: {', '.join(adapter.get('tags', []))}")
                print()
        else:
            print("\nNo adapters found.")

    elif args.command == "info":
        api.print_registry_info()

    elif args.command == "search":
        if not args.args:
            print("Error: Please provide a search query")
            return

        query = " ".join(args.args)
        results = api.search_adapters(query)

        if results:
            print(f"\nFound {len(results)} matching adapter(s):\n")
            for adapter in results:
                print_adapter_info(adapter)
        else:
            print(f"\nNo adapters found matching '{query}'")


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║              Agent 7: LoRA Fine-tuning System                 ║
    ║                                                               ║
    ║  • Unsloth QLoRA Pipeline (Memory-Efficient)                  ║
    ║  • LLaMA Factory Web UI (All-in-One GUI)                      ║
    ║  • VLM Fine-tuning (Vision-Language Models)                   ║
    ║  • LoRA Adapter Registry & Management                         ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """)

    # If no arguments, show info
    if len(sys.argv) == 1:
        api = Agent7LoRAAPI()
        api.print_registry_info()
        print("\nUsage: python agent7_lora_api.py [command]")
        print("Commands: ui, list, info, search")
        print("\nFor full help: python agent7_lora_api.py --help")
    else:
        main()
