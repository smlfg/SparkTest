"""
LoRA Adapter Management System
Registry, loading, merging, and version control for LoRA adapters
"""

import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import hashlib


class LoRARegistry:
    """
    Central registry for managing LoRA adapters.
    Tracks metadata, versions, and provides easy access to adapters.
    """

    def __init__(self, registry_dir: str = "./workspace/loras"):
        """
        Initialize LoRA registry.

        Args:
            registry_dir: Directory to store LoRA adapters
        """
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)

        self.registry_file = self.registry_dir / "registry.json"
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from disk."""
        if self.registry_file.exists():
            with open(self.registry_file, "r") as f:
                return json.load(f)
        return {"adapters": {}, "metadata": {"created": datetime.now().isoformat()}}

    def _save_registry(self):
        """Save registry to disk."""
        self.registry["metadata"]["last_updated"] = datetime.now().isoformat()
        with open(self.registry_file, "w") as f:
            json.dump(self.registry, f, indent=2)

    def register_adapter(
        self,
        adapter_path: str,
        adapter_name: str,
        base_model: str,
        description: str = "",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register a new LoRA adapter.

        Args:
            adapter_path: Path to adapter directory
            adapter_name: Unique name for the adapter
            base_model: Base model the adapter was trained on
            description: Description of the adapter
            tags: List of tags for categorization
            metadata: Additional metadata

        Returns:
            True if registration successful
        """
        adapter_path = Path(adapter_path)

        if not adapter_path.exists():
            print(f"Error: Adapter path does not exist: {adapter_path}")
            return False

        # Check if already registered
        if adapter_name in self.registry["adapters"]:
            print(f"Warning: Adapter '{adapter_name}' already registered. Use update_adapter() to modify.")
            return False

        # Copy adapter to registry
        dest_path = self.registry_dir / adapter_name
        if dest_path.exists():
            shutil.rmtree(dest_path)

        shutil.copytree(adapter_path, dest_path)

        # Calculate checksum
        checksum = self._calculate_checksum(dest_path)

        # Register adapter
        self.registry["adapters"][adapter_name] = {
            "name": adapter_name,
            "path": str(dest_path),
            "base_model": base_model,
            "description": description,
            "tags": tags or [],
            "checksum": checksum,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "versions": []
        }

        self._save_registry()
        print(f"✓ Adapter '{adapter_name}' registered successfully")
        return True

    def _calculate_checksum(self, adapter_path: Path) -> str:
        """Calculate checksum for adapter directory."""
        hasher = hashlib.sha256()

        for file in sorted(adapter_path.rglob("*")):
            if file.is_file():
                with open(file, "rb") as f:
                    hasher.update(f.read())

        return hasher.hexdigest()[:16]

    def list_adapters(self, tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List all registered adapters.

        Args:
            tags: Filter by tags (returns adapters with ANY of the tags)

        Returns:
            List of adapter info dictionaries
        """
        adapters = list(self.registry["adapters"].values())

        if tags:
            adapters = [
                a for a in adapters
                if any(tag in a.get("tags", []) for tag in tags)
            ]

        return adapters

    def get_adapter(self, adapter_name: str) -> Optional[Dict[str, Any]]:
        """Get adapter information."""
        return self.registry["adapters"].get(adapter_name)

    def get_adapter_path(self, adapter_name: str) -> Optional[str]:
        """Get path to adapter."""
        adapter = self.get_adapter(adapter_name)
        return adapter["path"] if adapter else None

    def delete_adapter(self, adapter_name: str, confirm: bool = False) -> bool:
        """
        Delete an adapter from registry.

        Args:
            adapter_name: Name of adapter to delete
            confirm: Confirmation flag (safety check)

        Returns:
            True if deletion successful
        """
        if not confirm:
            print("Error: Must set confirm=True to delete adapter")
            return False

        if adapter_name not in self.registry["adapters"]:
            print(f"Error: Adapter '{adapter_name}' not found")
            return False

        # Get adapter path and delete
        adapter_path = Path(self.registry["adapters"][adapter_name]["path"])
        if adapter_path.exists():
            shutil.rmtree(adapter_path)

        # Remove from registry
        del self.registry["adapters"][adapter_name]
        self._save_registry()

        print(f"✓ Adapter '{adapter_name}' deleted")
        return True

    def update_adapter(
        self,
        adapter_name: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update adapter metadata."""
        if adapter_name not in self.registry["adapters"]:
            print(f"Error: Adapter '{adapter_name}' not found")
            return False

        adapter = self.registry["adapters"][adapter_name]

        if description is not None:
            adapter["description"] = description
        if tags is not None:
            adapter["tags"] = tags
        if metadata is not None:
            adapter["metadata"].update(metadata)

        adapter["updated_at"] = datetime.now().isoformat()

        self._save_registry()
        print(f"✓ Adapter '{adapter_name}' updated")
        return True

    def search_adapters(self, query: str) -> List[Dict[str, Any]]:
        """Search adapters by name, description, or tags."""
        query = query.lower()
        results = []

        for adapter in self.registry["adapters"].values():
            if (
                query in adapter["name"].lower()
                or query in adapter.get("description", "").lower()
                or any(query in tag.lower() for tag in adapter.get("tags", []))
            ):
                results.append(adapter)

        return results

    def export_registry(self, output_path: str):
        """Export registry to a JSON file."""
        with open(output_path, "w") as f:
            json.dump(self.registry, f, indent=2)
        print(f"✓ Registry exported to {output_path}")

    def import_adapter(self, adapter_archive: str):
        """Import adapter from archive (future implementation)."""
        # TODO: Implement archive import
        pass


class LoRALoader:
    """Load and apply LoRA adapters to models."""

    @staticmethod
    def load_adapter(adapter_path: str, base_model=None):
        """
        Load a LoRA adapter.

        Args:
            adapter_path: Path to adapter
            base_model: Optional base model to apply adapter to

        Returns:
            Loaded adapter or model with adapter
        """
        from peft import PeftModel, PeftConfig

        try:
            adapter_path = Path(adapter_path)

            if base_model is None:
                # Just load config
                config = PeftConfig.from_pretrained(adapter_path)
                print(f"✓ Adapter config loaded from {adapter_path}")
                return config
            else:
                # Apply to model
                model = PeftModel.from_pretrained(base_model, adapter_path)
                print(f"✓ Adapter applied to model from {adapter_path}")
                return model

        except Exception as e:
            print(f"Error loading adapter: {e}")
            return None

    @staticmethod
    def merge_adapter(
        base_model_path: str,
        adapter_path: str,
        output_path: str,
        device: str = "cuda"
    ):
        """
        Merge LoRA adapter with base model.

        Args:
            base_model_path: Path to base model
            adapter_path: Path to LoRA adapter
            output_path: Path to save merged model
            device: Device to use for merging
        """
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from peft import PeftModel

        try:
            print(f"Loading base model: {base_model_path}")
            base_model = AutoModelForCausalLM.from_pretrained(
                base_model_path,
                torch_dtype="auto",
                device_map=device
            )

            print(f"Loading adapter: {adapter_path}")
            model = PeftModel.from_pretrained(base_model, adapter_path)

            print("Merging adapter with base model...")
            merged_model = model.merge_and_unload()

            print(f"Saving merged model to: {output_path}")
            merged_model.save_pretrained(output_path)

            # Save tokenizer
            tokenizer = AutoTokenizer.from_pretrained(base_model_path)
            tokenizer.save_pretrained(output_path)

            print("✓ Model merged successfully!")
            return True

        except Exception as e:
            print(f"Error merging adapter: {e}")
            return False


def print_adapter_info(adapter: Dict[str, Any]):
    """Pretty print adapter information."""
    print("\n" + "=" * 60)
    print(f"Adapter: {adapter['name']}")
    print("=" * 60)
    print(f"Base Model:   {adapter['base_model']}")
    print(f"Description:  {adapter.get('description', 'N/A')}")
    print(f"Tags:         {', '.join(adapter.get('tags', []))}")
    print(f"Path:         {adapter['path']}")
    print(f"Checksum:     {adapter.get('checksum', 'N/A')}")
    print(f"Created:      {adapter.get('created_at', 'N/A')}")

    if adapter.get("metadata"):
        print("\nMetadata:")
        for key, value in adapter["metadata"].items():
            print(f"  {key}: {value}")
    print("=" * 60)


if __name__ == "__main__":
    # Example usage
    print("LoRA Adapter Management System")
    print("=" * 60)

    # Initialize registry
    registry = LoRARegistry()

    # List all adapters
    adapters = registry.list_adapters()
    print(f"\nTotal adapters: {len(adapters)}")

    if adapters:
        print("\nRegistered adapters:")
        for adapter in adapters:
            print(f"  - {adapter['name']} ({adapter['base_model']})")
    else:
        print("\nNo adapters registered yet.")
        print("\nTo register an adapter:")
        print("  registry.register_adapter(")
        print("      adapter_path='/path/to/adapter',")
        print("      adapter_name='my-adapter',")
        print("      base_model='meta-llama/Llama-3-8B',")
        print("      description='My fine-tuned adapter'")
        print("  )")
