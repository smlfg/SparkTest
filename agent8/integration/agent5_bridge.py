"""
Integration bridge with Agent 5 (Model Serving)
Imports base models and exports quantized models
"""

import os
import sys
from pathlib import Path
from typing import Dict, Optional, List, Any
import json

# Configuration
BASE_MODELS_DIR = os.getenv("BASE_MODELS_DIR", "/workspace/models")
QUANTIZED_MODELS_DIR = os.getenv("QUANTIZED_MODELS_DIR", "/workspace/models/quantized")


class Agent5Bridge:
    """
    Bridge for integrating with Agent 5
    Handles model import/export between agents
    """

    def __init__(self):
        self.base_models_dir = Path(BASE_MODELS_DIR)
        self.quantized_models_dir = Path(QUANTIZED_MODELS_DIR)

        # Ensure directories exist
        self.base_models_dir.mkdir(parents=True, exist_ok=True)
        self.quantized_models_dir.mkdir(parents=True, exist_ok=True)

    def import_from_agent5(self, model_name: str) -> Dict[str, Any]:
        """
        Import base model from Agent 5

        Args:
            model_name: Name of model to import

        Returns:
            Model information dictionary
        """
        model_path = self.base_models_dir / model_name

        if not model_path.exists():
            print(f"⚠ Model {model_name} not found in Agent 5 models directory")
            print(f"   Expected path: {model_path}")
            print(f"   Will use default configuration")
            return {
                "model_name": model_name,
                "source": "agent5",
                "path": str(model_path),
                "exists": False,
                "status": "not_found"
            }

        # Load model metadata from Agent 5
        metadata_path = model_path / "model_info.json"
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        return {
            "model_name": model_name,
            "source": "agent5",
            "path": str(model_path),
            "exists": True,
            "metadata": metadata,
            "status": "imported"
        }

    def export_to_agent5(
        self,
        quantized_model_name: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Export quantized model for use by Agent 5

        Args:
            quantized_model_name: Name of quantized model
            metadata: Model metadata

        Returns:
            Export status
        """
        # Create symlink or copy to Agent 5 models directory
        quantized_path = self.quantized_models_dir / quantized_model_name
        export_path = self.base_models_dir / quantized_model_name

        if not quantized_path.exists():
            return {
                "status": "error",
                "message": f"Quantized model not found: {quantized_path}"
            }

        # Create symlink for efficient access
        try:
            if not export_path.exists():
                os.symlink(quantized_path, export_path)

            # Export metadata
            metadata_path = export_path / "quantization_info.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)

            return {
                "status": "exported",
                "quantized_path": str(quantized_path),
                "export_path": str(export_path),
                "accessible_to_agent5": True
            }

        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def list_base_models(self) -> List[str]:
        """
        List available base models from Agent 5

        Returns:
            List of model names
        """
        if not self.base_models_dir.exists():
            return []

        models = []
        for item in self.base_models_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                models.append(item.name)

        return models

    def list_quantized_models(self) -> List[str]:
        """
        List quantized models available to Agent 5

        Returns:
            List of quantized model names
        """
        if not self.quantized_models_dir.exists():
            return []

        models = []
        for item in self.quantized_models_dir.iterdir():
            if item.is_dir() or item.suffix in ['.gguf', '.bin']:
                models.append(item.name)

        return models

    def verify_integration(self) -> Dict[str, Any]:
        """
        Verify integration with Agent 5

        Returns:
            Integration status
        """
        status = {
            "base_models_dir": str(self.base_models_dir),
            "base_models_dir_exists": self.base_models_dir.exists(),
            "quantized_models_dir": str(self.quantized_models_dir),
            "quantized_models_dir_exists": self.quantized_models_dir.exists(),
            "base_models_count": len(self.list_base_models()),
            "quantized_models_count": len(self.list_quantized_models()),
            "integration_healthy": True
        }

        # Check if directories are accessible
        try:
            self.base_models_dir.mkdir(parents=True, exist_ok=True)
            self.quantized_models_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            status["integration_healthy"] = False
            status["error"] = str(e)

        return status


def setup_integration():
    """
    Setup integration with Agent 5
    Creates necessary directories and exports configuration
    """
    bridge = Agent5Bridge()

    print("Setting up Agent 8 <-> Agent 5 integration...")
    print(f"Base models directory:      {bridge.base_models_dir}")
    print(f"Quantized models directory: {bridge.quantized_models_dir}")

    # Verify integration
    status = bridge.verify_integration()

    print(f"\nIntegration Status:")
    print(f"  Base models:      {status['base_models_count']} available")
    print(f"  Quantized models: {status['quantized_models_count']} available")
    print(f"  Health:           {'✓ OK' if status['integration_healthy'] else '✗ ERROR'}")

    # Export environment variables
    env_config = {
        "BASE_MODELS_DIR": str(bridge.base_models_dir),
        "QUANTIZED_MODELS_DIR": str(bridge.quantized_models_dir)
    }

    env_file = Path("agent8_integration.env")
    with open(env_file, 'w') as f:
        for key, value in env_config.items():
            f.write(f'export {key}="{value}"\n')

    print(f"\n✓ Integration configuration saved to: {env_file}")
    print(f"  Source it with: source {env_file}")

    return status


if __name__ == "__main__":
    setup_integration()
