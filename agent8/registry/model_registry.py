"""
Quantized Model Registry
Centralized tracking and management of quantized models
"""

import json
import time
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ModelInfo:
    """Information about a quantized model"""
    model_name: str
    quantized_name: str
    precision: str
    bits: int
    original_size_gb: float
    quantized_size_gb: float
    compression_ratio: float
    output_path: str
    created_at: str
    status: str
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ModelRegistry:
    """
    Registry for managing quantized models
    Provides CRUD operations and search capabilities
    """

    def __init__(self, registry_path: str = "models/registry.json"):
        """
        Initialize model registry

        Args:
            registry_path: Path to registry JSON file
        """
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing registry or create new one
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from disk"""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        else:
            return {
                "version": "1.0",
                "created_at": datetime.now().isoformat(),
                "models": {}
            }

    def _save_registry(self):
        """Save registry to disk"""
        with open(self.registry_path, 'w') as f:
            json.dump(self.registry, f, indent=2)

    def register(self, model_info: Dict[str, Any]) -> str:
        """
        Register a new quantized model

        Args:
            model_info: Model information dictionary

        Returns:
            Model ID
        """
        # Generate model ID
        model_id = f"{model_info['quantized_name']}_{int(time.time())}"

        # Add timestamp if not present
        if 'created_at' not in model_info:
            model_info['created_at'] = datetime.now().isoformat()

        # Store in registry
        self.registry["models"][model_id] = model_info
        self.registry["last_updated"] = datetime.now().isoformat()

        # Save to disk
        self._save_registry()

        print(f"✓ Registered model: {model_info['quantized_name']} (ID: {model_id})")

        return model_id

    def get(self, model_id: str) -> Optional[Dict[str, Any]]:
        """
        Get model information by ID

        Args:
            model_id: Model ID

        Returns:
            Model information or None
        """
        return self.registry["models"].get(model_id)

    def find_by_name(self, model_name: str) -> List[Dict[str, Any]]:
        """
        Find models by name

        Args:
            model_name: Model name to search for

        Returns:
            List of matching models
        """
        results = []
        for model_id, model_info in self.registry["models"].items():
            if (model_name in model_info.get("model_name", "") or
                model_name in model_info.get("quantized_name", "")):
                results.append({
                    "id": model_id,
                    **model_info
                })
        return results

    def list_all(self) -> List[Dict[str, Any]]:
        """
        List all registered models

        Returns:
            List of all models
        """
        return [
            {"id": model_id, **model_info}
            for model_id, model_info in self.registry["models"].items()
        ]

    def filter_by_precision(self, precision: str) -> List[Dict[str, Any]]:
        """
        Filter models by precision

        Args:
            precision: Precision type (e.g., 'fp4', 'nf4')

        Returns:
            List of matching models
        """
        results = []
        for model_id, model_info in self.registry["models"].items():
            if model_info.get("precision") == precision:
                results.append({
                    "id": model_id,
                    **model_info
                })
        return results

    def delete(self, model_id: str) -> bool:
        """
        Remove a model from registry

        Args:
            model_id: Model ID to delete

        Returns:
            True if deleted, False if not found
        """
        if model_id in self.registry["models"]:
            del self.registry["models"][model_id]
            self.registry["last_updated"] = datetime.now().isoformat()
            self._save_registry()
            print(f"✓ Deleted model: {model_id}")
            return True
        return False

    def update(self, model_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update model information

        Args:
            model_id: Model ID
            updates: Dictionary of fields to update

        Returns:
            True if updated, False if not found
        """
        if model_id in self.registry["models"]:
            self.registry["models"][model_id].update(updates)
            self.registry["models"][model_id]["updated_at"] = datetime.now().isoformat()
            self.registry["last_updated"] = datetime.now().isoformat()
            self._save_registry()
            print(f"✓ Updated model: {model_id}")
            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get registry statistics

        Returns:
            Statistics dictionary
        """
        models = list(self.registry["models"].values())

        if not models:
            return {
                "total_models": 0,
                "total_original_size_gb": 0,
                "total_quantized_size_gb": 0,
                "total_savings_gb": 0
            }

        total_original = sum(m.get("original_size_gb", 0) for m in models)
        total_quantized = sum(m.get("quantized_size_gb", 0) for m in models)

        # Count by precision
        precision_counts = {}
        for model in models:
            precision = model.get("precision", "unknown")
            precision_counts[precision] = precision_counts.get(precision, 0) + 1

        return {
            "total_models": len(models),
            "total_original_size_gb": total_original,
            "total_quantized_size_gb": total_quantized,
            "total_savings_gb": total_original - total_quantized,
            "average_compression_ratio": sum(m.get("compression_ratio", 0) for m in models) / len(models),
            "precision_distribution": precision_counts,
            "registry_version": self.registry["version"],
            "created_at": self.registry["created_at"]
        }

    def export_to_json(self, output_path: str):
        """
        Export registry to JSON file

        Args:
            output_path: Output file path
        """
        with open(output_path, 'w') as f:
            json.dump(self.registry, f, indent=2)
        print(f"✓ Registry exported to: {output_path}")

    def import_from_json(self, input_path: str):
        """
        Import registry from JSON file

        Args:
            input_path: Input file path
        """
        with open(input_path, 'r') as f:
            imported_registry = json.load(f)

        # Merge with existing registry
        for model_id, model_info in imported_registry.get("models", {}).items():
            self.registry["models"][model_id] = model_info

        self.registry["last_updated"] = datetime.now().isoformat()
        self._save_registry()
        print(f"✓ Registry imported from: {input_path}")

    def print_summary(self):
        """Print a summary of the registry"""
        stats = self.get_statistics()

        print(f"\n{'='*60}")
        print("MODEL REGISTRY SUMMARY")
        print(f"{'='*60}\n")

        print(f"Total Models:       {stats['total_models']}")
        print(f"Original Size:      {stats['total_original_size_gb']:.2f} GB")
        print(f"Quantized Size:     {stats['total_quantized_size_gb']:.2f} GB")
        print(f"Total Savings:      {stats['total_savings_gb']:.2f} GB")
        print(f"Avg Compression:    {stats.get('average_compression_ratio', 0):.2f}x")

        print(f"\nPrecision Distribution:")
        for precision, count in stats.get('precision_distribution', {}).items():
            print(f"  {precision}: {count}")

        print(f"\nRegistry Path:      {self.registry_path}")
        print(f"{'='*60}\n")
