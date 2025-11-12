"""
Vision-Language Model (VLM) Fine-tuning
Support for LLaVA, Qwen-VL, and other multimodal models with LoRA
"""

import torch
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
import json
from PIL import Image


class VLMFineTuner:
    """
    Fine-tuning pipeline for Vision-Language Models.
    Supports models like LLaVA, Qwen-VL, MiniGPT-4, etc.
    """

    def __init__(
        self,
        model_name: str = "llava-hf/llava-1.5-7b-hf",
        vision_model_type: str = "llava",
        lora_r: int = 8,
        lora_alpha: int = 16,
        lora_dropout: float = 0.05,
        target_modules: Optional[List[str]] = None,
        load_in_4bit: bool = True
    ):
        """
        Initialize VLM fine-tuner.

        Args:
            model_name: HuggingFace model name
            vision_model_type: Type of VLM (llava, qwen-vl, etc.)
            lora_r: LoRA rank
            lora_alpha: LoRA alpha
            lora_dropout: LoRA dropout
            target_modules: Modules to apply LoRA
            load_in_4bit: Use 4-bit quantization
        """
        self.model_name = model_name
        self.vision_model_type = vision_model_type.lower()
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.load_in_4bit = load_in_4bit

        # Default target modules for VLMs
        if target_modules is None:
            if "llava" in self.vision_model_type:
                self.target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
            elif "qwen" in self.vision_model_type:
                self.target_modules = ["c_attn", "c_proj"]
            else:
                self.target_modules = ["q_proj", "v_proj"]
        else:
            self.target_modules = target_modules

        self.model = None
        self.processor = None
        self.tokenizer = None

    def setup_model(self):
        """Load and configure the VLM with LoRA."""
        try:
            from transformers import (
                AutoModelForVision2Seq,
                AutoProcessor,
                BitsAndBytesConfig
            )
            from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

            # Quantization config
            if self.load_in_4bit:
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                )
            else:
                bnb_config = None

            # Load model based on type
            if "llava" in self.vision_model_type:
                from transformers import LlavaForConditionalGeneration
                self.model = LlavaForConditionalGeneration.from_pretrained(
                    self.model_name,
                    quantization_config=bnb_config,
                    device_map="auto",
                    torch_dtype=torch.float16
                )
                self.processor = AutoProcessor.from_pretrained(self.model_name)

            elif "qwen-vl" in self.vision_model_type:
                from transformers import AutoModelForCausalLM
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    quantization_config=bnb_config,
                    device_map="auto",
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                )
                self.processor = AutoProcessor.from_pretrained(
                    self.model_name,
                    trust_remote_code=True
                )

            else:
                # Generic vision-language model
                self.model = AutoModelForVision2Seq.from_pretrained(
                    self.model_name,
                    quantization_config=bnb_config,
                    device_map="auto",
                    torch_dtype=torch.float16
                )
                self.processor = AutoProcessor.from_pretrained(self.model_name)

            # Prepare for training
            if self.load_in_4bit:
                self.model = prepare_model_for_kbit_training(self.model)

            # Add LoRA adapters
            lora_config = LoraConfig(
                r=self.lora_r,
                lora_alpha=self.lora_alpha,
                target_modules=self.target_modules,
                lora_dropout=self.lora_dropout,
                bias="none",
                task_type="CAUSAL_LM"
            )

            self.model = get_peft_model(self.model, lora_config)
            self.model.print_trainable_parameters()

            print(f"✓ VLM loaded: {self.model_name}")
            print(f"✓ LoRA config: r={self.lora_r}, alpha={self.lora_alpha}")
            return True

        except Exception as e:
            print(f"Error loading VLM: {e}")
            return False

    def prepare_dataset(
        self,
        dataset_path: str,
        image_column: str = "image",
        text_column: str = "text",
        split: str = "train"
    ):
        """
        Prepare vision-language dataset.

        Args:
            dataset_path: Path to dataset
            image_column: Column name for images
            text_column: Column name for text
            split: Dataset split

        Returns:
            Processed dataset
        """
        from datasets import load_dataset

        try:
            # Load dataset
            if Path(dataset_path).exists():
                dataset = load_dataset("json", data_files=dataset_path, split=split)
            else:
                dataset = load_dataset(dataset_path, split=split)

            print(f"✓ Dataset loaded: {len(dataset)} examples")
            print(f"  Image column: {image_column}")
            print(f"  Text column: {text_column}")

            # Create processing function
            def process_example(example):
                # Load image
                image_path = example[image_column]
                if isinstance(image_path, str):
                    image = Image.open(image_path).convert("RGB")
                else:
                    image = image_path

                # Get text
                text = example[text_column]

                # Process with model processor
                inputs = self.processor(
                    text=text,
                    images=image,
                    return_tensors="pt",
                    padding=True,
                    truncation=True
                )

                return inputs

            return dataset, process_example

        except Exception as e:
            print(f"Error preparing dataset: {e}")
            return None, None

    def train(
        self,
        dataset,
        collate_fn,
        output_dir: str = "./outputs/vlm_lora",
        num_train_epochs: int = 3,
        per_device_train_batch_size: int = 1,
        gradient_accumulation_steps: int = 8,
        learning_rate: float = 2e-5,
        warmup_steps: int = 100,
        logging_steps: int = 10,
        save_steps: int = 500,
        **kwargs
    ):
        """
        Train the VLM with LoRA.

        Args:
            dataset: Training dataset
            collate_fn: Data collation function
            output_dir: Output directory
            num_train_epochs: Number of epochs
            per_device_train_batch_size: Batch size
            gradient_accumulation_steps: Gradient accumulation steps
            learning_rate: Learning rate
            warmup_steps: Warmup steps
            logging_steps: Logging frequency
            save_steps: Save frequency
            **kwargs: Additional arguments
        """
        from transformers import Trainer, TrainingArguments

        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            save_steps=save_steps,
            fp16=True,
            optim="paged_adamw_8bit",
            remove_unused_columns=False,
            dataloader_pin_memory=False,
            **kwargs
        )

        # Initialize trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset,
            data_collator=collate_fn,
        )

        print("Starting VLM training...")
        trainer.train()

        print(f"✓ Training complete. Saved to {output_dir}")
        return trainer

    def save_adapter(self, output_path: str, adapter_name: Optional[str] = None):
        """Save LoRA adapter for VLM."""
        if self.model is None:
            print("Error: No model loaded")
            return

        Path(output_path).mkdir(parents=True, exist_ok=True)

        # Save adapter
        self.model.save_pretrained(output_path)
        self.processor.save_pretrained(output_path)

        # Save metadata
        metadata = {
            "adapter_name": adapter_name or Path(output_path).name,
            "base_model": self.model_name,
            "model_type": self.vision_model_type,
            "lora_r": self.lora_r,
            "lora_alpha": self.lora_alpha,
            "target_modules": self.target_modules,
        }

        with open(Path(output_path) / "adapter_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"✓ VLM LoRA adapter saved to {output_path}")

    def inference(
        self,
        image: Union[str, Image.Image],
        prompt: str,
        max_new_tokens: int = 256,
        temperature: float = 0.7
    ) -> str:
        """
        Run inference with the fine-tuned VLM.

        Args:
            image: Image path or PIL Image
            prompt: Text prompt
            max_new_tokens: Max tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        self.model.eval()

        # Load image if path
        if isinstance(image, str):
            image = Image.open(image).convert("RGB")

        # Process inputs
        inputs = self.processor(
            text=prompt,
            images=image,
            return_tensors="pt"
        ).to(self.model.device)

        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                do_sample=True
            )

        # Decode
        result = self.processor.decode(outputs[0], skip_special_tokens=True)
        return result


class LLaVAFineTuner(VLMFineTuner):
    """Specialized fine-tuner for LLaVA models."""

    def __init__(self, model_name: str = "llava-hf/llava-1.5-7b-hf", **kwargs):
        super().__init__(model_name=model_name, vision_model_type="llava", **kwargs)

    def format_llava_prompt(self, instruction: str, image_token: str = "<image>"):
        """Format prompt for LLaVA."""
        return f"USER: {image_token}\n{instruction}\nASSISTANT:"


class QwenVLFineTuner(VLMFineTuner):
    """Specialized fine-tuner for Qwen-VL models."""

    def __init__(self, model_name: str = "Qwen/Qwen-VL-Chat", **kwargs):
        super().__init__(model_name=model_name, vision_model_type="qwen-vl", **kwargs)

    def format_qwen_prompt(self, query: str, image_path: str):
        """Format prompt for Qwen-VL."""
        return [
            {"image": image_path},
            {"text": query}
        ]


def create_vlm_config(
    model_name: str,
    model_type: str = "llava",
    dataset_path: str = "./data/vlm_train.json",
    output_dir: str = "./outputs/vlm_lora",
    lora_r: int = 8,
    learning_rate: float = 2e-5,
    num_epochs: int = 3
) -> Dict[str, Any]:
    """Create VLM training configuration."""
    return {
        "model": {
            "name": model_name,
            "type": model_type,
            "load_in_4bit": True,
        },
        "lora": {
            "r": lora_r,
            "alpha": lora_r * 2,
            "dropout": 0.05,
        },
        "training": {
            "dataset_path": dataset_path,
            "output_dir": output_dir,
            "num_train_epochs": num_epochs,
            "per_device_train_batch_size": 1,
            "gradient_accumulation_steps": 8,
            "learning_rate": learning_rate,
            "warmup_steps": 100,
            "logging_steps": 10,
            "save_steps": 500,
        }
    }


if __name__ == "__main__":
    print("VLM Fine-tuning Pipeline - Examples")
    print("=" * 60)

    # LLaVA example
    print("\n1. LLaVA Fine-tuning:")
    print("-" * 40)
    llava = LLaVAFineTuner()
    print(f"   Model: {llava.model_name}")
    print(f"   Target modules: {llava.target_modules}")

    # Qwen-VL example
    print("\n2. Qwen-VL Fine-tuning:")
    print("-" * 40)
    qwen = QwenVLFineTuner()
    print(f"   Model: {qwen.model_name}")
    print(f"   Target modules: {qwen.target_modules}")

    print("\n✓ VLM fine-tuning pipelines ready!")
