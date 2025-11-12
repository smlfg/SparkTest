"""
LLaMA Factory Web UI Launcher
All-in-one GUI for fine-tuning with automatic setup and management
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json
import time


class LLaMAFactoryUI:
    """
    LLaMA Factory Web UI Manager
    Provides easy setup and launch of the LLaMA Factory Gradio interface
    """

    def __init__(
        self,
        workspace_dir: str = "./workspace",
        lora_output_dir: str = "./workspace/loras",
        port: int = 7860,
        share: bool = False
    ):
        """
        Initialize LLaMA Factory UI manager.

        Args:
            workspace_dir: Working directory for models and datasets
            lora_output_dir: Directory to save LoRA adapters
            port: Port for web UI
            share: Whether to create public share link
        """
        self.workspace_dir = Path(workspace_dir)
        self.lora_output_dir = Path(lora_output_dir)
        self.port = port
        self.share = share

        # Create directories
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.lora_output_dir.mkdir(parents=True, exist_ok=True)

        self.process = None

    def check_installation(self) -> bool:
        """Check if LLaMA Factory is installed."""
        try:
            import llamafactory
            print("✓ LLaMA Factory is installed")
            return True
        except ImportError:
            print("✗ LLaMA Factory not installed")
            return False

    def install(self):
        """Install LLaMA Factory and dependencies."""
        print("Installing LLaMA Factory...")

        try:
            # Install LLaMA Factory
            subprocess.check_call([
                sys.executable, "-m", "pip", "install",
                "llamafactory[torch,metrics]"
            ])

            print("✓ LLaMA Factory installed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Installation failed: {e}")
            return False

    def launch_ui(self, auto_install: bool = True):
        """
        Launch the LLaMA Factory web UI.

        Args:
            auto_install: Automatically install if not present

        Returns:
            True if launched successfully
        """
        # Check installation
        if not self.check_installation():
            if auto_install:
                if not self.install():
                    return False
            else:
                print("Please install LLaMA Factory first: pip install llamafactory[torch,metrics]")
                return False

        print(f"\nLaunching LLaMA Factory UI on port {self.port}...")
        print(f"LoRA adapters will be saved to: {self.lora_output_dir}")

        try:
            # Set environment variables
            env = os.environ.copy()
            env["GRADIO_SERVER_PORT"] = str(self.port)
            env["LLAMAFACTORY_OUTPUT_DIR"] = str(self.lora_output_dir)

            # Launch command
            cmd = [sys.executable, "-m", "llamafactory.cli", "webui"]

            if self.share:
                cmd.append("--share")

            # Start process
            self.process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            # Wait for startup
            print("\nWaiting for UI to start...")
            time.sleep(3)

            if self.process.poll() is None:
                print(f"\n✓ LLaMA Factory UI is running!")
                print(f"\n🌐 Access the UI at: http://localhost:{self.port}")
                if self.share:
                    print("   (Public link will be displayed in logs)")
                print("\nPress Ctrl+C to stop the server")

                # Stream output
                try:
                    for line in self.process.stdout:
                        print(line.rstrip())
                except KeyboardInterrupt:
                    print("\n\nStopping server...")
                    self.stop()

                return True
            else:
                print("✗ Failed to start UI")
                return False

        except Exception as e:
            print(f"✗ Error launching UI: {e}")
            return False

    def stop(self):
        """Stop the running UI server."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                print("✓ Server stopped")
            except subprocess.TimeoutExpired:
                self.process.kill()
                print("✓ Server killed")

    def create_dataset_config(
        self,
        dataset_name: str,
        dataset_path: str,
        dataset_format: str = "alpaca"
    ):
        """
        Create a dataset configuration for LLaMA Factory.

        Args:
            dataset_name: Name of the dataset
            dataset_path: Path to dataset file
            dataset_format: Format (alpaca, sharegpt, etc.)

        Returns:
            Path to the created config file
        """
        config_dir = self.workspace_dir / "datasets"
        config_dir.mkdir(parents=True, exist_ok=True)

        config_file = config_dir / "dataset_info.json"

        # Load existing config or create new
        if config_file.exists():
            with open(config_file, "r") as f:
                dataset_info = json.load(f)
        else:
            dataset_info = {}

        # Add dataset
        dataset_info[dataset_name] = {
            "file_name": dataset_path,
            "formatting": dataset_format
        }

        # Save config
        with open(config_file, "w") as f:
            json.dump(dataset_info, f, indent=2)

        print(f"✓ Dataset config created: {config_file}")
        return str(config_file)

    def create_training_config(
        self,
        config_name: str,
        model_name: str = "meta-llama/Llama-3-8B",
        dataset_name: str = "custom_dataset",
        lora_rank: int = 8,
        learning_rate: float = 5e-5,
        num_epochs: int = 3,
        batch_size: int = 4,
        **kwargs
    ) -> str:
        """
        Create a training configuration file.

        Args:
            config_name: Name for this config
            model_name: Base model name
            dataset_name: Dataset to use
            lora_rank: LoRA rank
            learning_rate: Learning rate
            num_epochs: Number of training epochs
            batch_size: Training batch size
            **kwargs: Additional parameters

        Returns:
            Path to config file
        """
        config_dir = self.workspace_dir / "configs"
        config_dir.mkdir(parents=True, exist_ok=True)

        config = {
            "model_name_or_path": model_name,
            "dataset": dataset_name,
            "finetuning_type": "lora",
            "lora_rank": lora_rank,
            "lora_alpha": lora_rank * 2,
            "lora_dropout": 0.05,
            "lora_target": "all",
            "learning_rate": learning_rate,
            "num_train_epochs": num_epochs,
            "per_device_train_batch_size": batch_size,
            "gradient_accumulation_steps": 4,
            "lr_scheduler_type": "cosine",
            "warmup_ratio": 0.1,
            "fp16": True,
            "logging_steps": 10,
            "save_steps": 500,
            "output_dir": str(self.lora_output_dir / config_name),
            **kwargs
        }

        config_file = config_dir / f"{config_name}.json"
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

        print(f"✓ Training config created: {config_file}")
        return str(config_file)

    def train_cli(self, config_file: str):
        """
        Train a model using LLaMA Factory CLI (without UI).

        Args:
            config_file: Path to training config JSON

        Returns:
            True if training completed successfully
        """
        try:
            cmd = [
                sys.executable, "-m", "llamafactory.cli", "train",
                config_file
            ]

            print(f"Starting training with config: {config_file}")
            subprocess.check_call(cmd)

            print("✓ Training completed successfully")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Training failed: {e}")
            return False

    def export_model(
        self,
        adapter_path: str,
        output_path: str,
        export_format: str = "gguf"
    ):
        """
        Export trained model to different formats.

        Args:
            adapter_path: Path to LoRA adapter
            output_path: Output path for exported model
            export_format: Format (gguf, awq, gptq, etc.)

        Returns:
            True if export successful
        """
        try:
            cmd = [
                sys.executable, "-m", "llamafactory.cli", "export",
                "--adapter_path", adapter_path,
                "--output_path", output_path,
                "--export_format", export_format
            ]

            print(f"Exporting model to {export_format} format...")
            subprocess.check_call(cmd)

            print(f"✓ Model exported to: {output_path}")
            return True

        except subprocess.CalledProcessError as e:
            print(f"✗ Export failed: {e}")
            return False


def quick_launch(port: int = 7860, share: bool = False):
    """Quick launch function for easy startup."""
    ui = LLaMAFactoryUI(port=port, share=share)
    ui.launch_ui()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LLaMA Factory UI Launcher")
    parser.add_argument("--port", type=int, default=7860, help="Port for web UI")
    parser.add_argument("--share", action="store_true", help="Create public share link")
    parser.add_argument("--workspace", type=str, default="./workspace", help="Workspace directory")
    parser.add_argument("--lora-dir", type=str, default="./workspace/loras", help="LoRA output directory")
    parser.add_argument("--install", action="store_true", help="Install LLaMA Factory and exit")

    args = parser.parse_args()

    ui = LLaMAFactoryUI(
        workspace_dir=args.workspace,
        lora_output_dir=args.lora_dir,
        port=args.port,
        share=args.share
    )

    if args.install:
        ui.install()
    else:
        print("=" * 60)
        print("LLaMA Factory Web UI Launcher")
        print("=" * 60)
        ui.launch_ui()
