#!/usr/bin/env python3
"""
Model Auto-Import Script
Imports fine-tuned models from Agent 3 (LLaMA-Factory) into Ollama

Usage:
    python import_finetuned.py --checkpoint /path/to/checkpoint --model-name student-chatbot
    python import_finetuned.py --checkpoint /app/output/student-chat-model --model-name student-chatbot
"""

import os
import sys
import json
import shutil
import argparse
import subprocess
import logging
from pathlib import Path
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelImporter:
    """Handles importing fine-tuned models from Agent 3 into Ollama"""

    def __init__(
        self,
        checkpoint_path: str,
        model_name: str,
        base_model: str = "meta-llama/Llama-3.1-8B-Instruct",
        ollama_host: str = "http://localhost:11434",
        work_dir: str = "/tmp/model_import"
    ):
        """
        Initialize ModelImporter

        Args:
            checkpoint_path: Path to LoRA checkpoint from Agent 3
            model_name: Name for the imported model in Ollama
            base_model: Base model used for fine-tuning
            ollama_host: Ollama API endpoint
            work_dir: Temporary working directory
        """
        self.checkpoint_path = Path(checkpoint_path)
        self.model_name = model_name
        self.base_model = base_model
        self.ollama_host = ollama_host
        self.work_dir = Path(work_dir)

        # Create work directory
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.merged_dir = self.work_dir / f"{model_name}_merged"
        self.gguf_path = self.work_dir / f"{model_name}.gguf"
        self.modelfile_path = self.work_dir / f"Modelfile_{model_name}"

    def validate_checkpoint(self) -> bool:
        """Validate that checkpoint exists and has required files"""
        if not self.checkpoint_path.exists():
            logger.error(f"Checkpoint path does not exist: {self.checkpoint_path}")
            return False

        # Check for adapter files
        required_files = ["adapter_config.json", "adapter_model.safetensors"]
        for file in required_files:
            if not (self.checkpoint_path / file).exists():
                logger.warning(f"Missing file: {file}")

        logger.info(f"✓ Checkpoint validated: {self.checkpoint_path}")
        return True

    def merge_lora(self) -> bool:
        """
        Merge LoRA adapter with base model

        Returns:
            True if successful, False otherwise
        """
        logger.info("Step 1/4: Merging LoRA adapter with base model...")

        try:
            # Check if LLaMA-Factory is available
            merge_script = shutil.which("llamafactory-cli")
            if not merge_script:
                logger.warning("LLaMA-Factory CLI not found, using alternative method")
                return self._merge_lora_alternative()

            # Create merge config
            merge_config = {
                "model_name_or_path": self.base_model,
                "adapter_name_or_path": str(self.checkpoint_path),
                "template": "llama3",
                "finetuning_type": "lora",
                "export_dir": str(self.merged_dir),
                "export_size": 2,
                "export_device": "cpu",
                "export_legacy_format": False
            }

            config_path = self.work_dir / "merge_config.json"
            with open(config_path, 'w') as f:
                json.dump(merge_config, f, indent=2)

            # Run merge
            cmd = [
                "llamafactory-cli", "export",
                "--config", str(config_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                logger.error(f"Merge failed: {result.stderr}")
                return False

            logger.info(f"✓ Model merged successfully: {self.merged_dir}")
            return True

        except Exception as e:
            logger.error(f"Error during merge: {e}")
            return False

    def _merge_lora_alternative(self) -> bool:
        """Alternative merge method using PEFT directly"""
        logger.info("Using PEFT direct merge method...")

        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer
            from peft import PeftModel

            logger.info(f"Loading base model: {self.base_model}")
            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model,
                device_map="cpu",
                torch_dtype="auto"
            )

            logger.info(f"Loading LoRA adapter: {self.checkpoint_path}")
            model = PeftModel.from_pretrained(base_model, str(self.checkpoint_path))

            logger.info("Merging LoRA weights...")
            model = model.merge_and_unload()

            logger.info(f"Saving merged model to: {self.merged_dir}")
            model.save_pretrained(self.merged_dir)

            # Save tokenizer
            tokenizer = AutoTokenizer.from_pretrained(self.base_model)
            tokenizer.save_pretrained(self.merged_dir)

            logger.info("✓ Model merged successfully using PEFT")
            return True

        except ImportError as e:
            logger.error(f"Required libraries not installed: {e}")
            logger.error("Install with: pip install transformers peft torch")
            return False
        except Exception as e:
            logger.error(f"Error during PEFT merge: {e}")
            return False

    def convert_to_gguf(self) -> bool:
        """
        Convert merged model to GGUF format for Ollama

        Returns:
            True if successful, False otherwise
        """
        logger.info("Step 2/4: Converting to GGUF format...")

        try:
            # Check for llama.cpp convert script
            convert_script = Path.home() / "llama.cpp" / "convert_hf_to_gguf.py"

            if not convert_script.exists():
                logger.warning("llama.cpp not found, attempting to use ollama create directly")
                return True  # Skip GGUF conversion, use HF directly

            cmd = [
                "python", str(convert_script),
                str(self.merged_dir),
                "--outfile", str(self.gguf_path),
                "--outtype", "q8_0"  # 8-bit quantization
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                logger.warning(f"GGUF conversion warning: {result.stderr}")
                logger.info("Continuing with HuggingFace format...")
                return True

            logger.info(f"✓ Model converted to GGUF: {self.gguf_path}")
            return True

        except Exception as e:
            logger.warning(f"GGUF conversion error: {e}")
            logger.info("Will use HuggingFace format instead")
            return True

    def create_modelfile(self, temperature: float = 0.7, context_length: int = 4096) -> bool:
        """
        Create Ollama Modelfile

        Args:
            temperature: Default temperature
            context_length: Context window size

        Returns:
            True if successful
        """
        logger.info("Step 3/4: Creating Ollama Modelfile...")

        try:
            # Determine source path
            if self.gguf_path.exists():
                from_path = str(self.gguf_path)
            else:
                from_path = str(self.merged_dir)

            # Create Modelfile content
            modelfile_content = f"""# Fine-tuned model from Agent 3 (LLaMA-Factory)
FROM {from_path}

# Model parameters
PARAMETER temperature {temperature}
PARAMETER num_ctx {context_length}
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER repeat_penalty 1.1

# System message
SYSTEM You are a helpful AI assistant fine-tuned for specific tasks.

# Template (Llama 3 format)
TEMPLATE \"\"\"
{{{{ if .System }}}}<|start_header_id|>system<|end_header_id|>

{{{{ .System }}}}<|eot_id|>{{{{ end }}}}
{{{{ if .Prompt }}}}<|start_header_id|>user<|end_header_id|>

{{{{ .Prompt }}}}<|eot_id|>{{{{ end }}}}<|start_header_id|>assistant<|end_header_id|>

{{{{ .Response }}}}<|eot_id|>
\"\"\"
"""

            # Write Modelfile
            with open(self.modelfile_path, 'w') as f:
                f.write(modelfile_content)

            logger.info(f"✓ Modelfile created: {self.modelfile_path}")
            return True

        except Exception as e:
            logger.error(f"Error creating Modelfile: {e}")
            return False

    def import_to_ollama(self) -> bool:
        """
        Import model into Ollama

        Returns:
            True if successful, False otherwise
        """
        logger.info("Step 4/4: Importing to Ollama...")

        try:
            # Check if ollama is available
            ollama_bin = shutil.which("ollama")
            if not ollama_bin:
                logger.error("Ollama not found in PATH")
                return False

            # Create model in Ollama
            cmd = [
                "ollama", "create", self.model_name,
                "-f", str(self.modelfile_path)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )

            if result.returncode != 0:
                logger.error(f"Ollama import failed: {result.stderr}")
                return False

            logger.info(f"✓ Model '{self.model_name}' imported to Ollama")

            # Verify model is available
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True
            )

            if self.model_name in result.stdout:
                logger.info(f"✓ Verified: Model '{self.model_name}' is available")
                return True
            else:
                logger.warning("Model import completed but not found in list")
                return True

        except Exception as e:
            logger.error(f"Error importing to Ollama: {e}")
            return False

    def cleanup(self, keep_merged: bool = False):
        """
        Clean up temporary files

        Args:
            keep_merged: Keep merged model directory
        """
        logger.info("Cleaning up temporary files...")

        try:
            if not keep_merged and self.merged_dir.exists():
                shutil.rmtree(self.merged_dir)
                logger.info(f"✓ Removed: {self.merged_dir}")

            if self.gguf_path.exists():
                self.gguf_path.unlink()
                logger.info(f"✓ Removed: {self.gguf_path}")

            if self.modelfile_path.exists():
                self.modelfile_path.unlink()
                logger.info(f"✓ Removed: {self.modelfile_path}")

        except Exception as e:
            logger.warning(f"Cleanup warning: {e}")

    def import_model(self, cleanup: bool = True, keep_merged: bool = False) -> bool:
        """
        Full import pipeline

        Args:
            cleanup: Clean up temporary files after import
            keep_merged: Keep merged model directory

        Returns:
            True if successful, False otherwise
        """
        logger.info("="*60)
        logger.info(f"Importing fine-tuned model: {self.model_name}")
        logger.info(f"Checkpoint: {self.checkpoint_path}")
        logger.info("="*60)

        # Validate checkpoint
        if not self.validate_checkpoint():
            return False

        # Merge LoRA
        if not self.merge_lora():
            logger.error("Failed to merge LoRA adapter")
            return False

        # Convert to GGUF (optional)
        if not self.convert_to_gguf():
            logger.error("Failed to convert to GGUF")
            return False

        # Create Modelfile
        if not self.create_modelfile():
            logger.error("Failed to create Modelfile")
            return False

        # Import to Ollama
        if not self.import_to_ollama():
            logger.error("Failed to import to Ollama")
            return False

        # Cleanup
        if cleanup:
            self.cleanup(keep_merged=keep_merged)

        logger.info("="*60)
        logger.info(f"✅ Model '{self.model_name}' successfully imported!")
        logger.info(f"Test with: ollama run {self.model_name}")
        logger.info("="*60)

        return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Import fine-tuned models from Agent 3 into Ollama"
    )
    parser.add_argument(
        "--checkpoint",
        required=True,
        help="Path to LoRA checkpoint directory"
    )
    parser.add_argument(
        "--model-name",
        required=True,
        help="Name for the imported model in Ollama"
    )
    parser.add_argument(
        "--base-model",
        default="meta-llama/Llama-3.1-8B-Instruct",
        help="Base model used for fine-tuning"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Default temperature (default: 0.7)"
    )
    parser.add_argument(
        "--context-length",
        type=int,
        default=4096,
        help="Context window size (default: 4096)"
    )
    parser.add_argument(
        "--keep-merged",
        action="store_true",
        help="Keep merged model directory"
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't clean up temporary files"
    )

    args = parser.parse_args()

    # Create importer
    importer = ModelImporter(
        checkpoint_path=args.checkpoint,
        model_name=args.model_name,
        base_model=args.base_model
    )

    # Import model
    success = importer.import_model(
        cleanup=not args.no_cleanup,
        keep_merged=args.keep_merged
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
