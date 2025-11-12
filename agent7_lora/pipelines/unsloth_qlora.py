"""
Unsloth QLoRA Pipeline - Memory-Efficient Fine-tuning
Optimized for efficient VRAM usage with 4-bit quantization
"""

import torch
from typing import Optional, Dict, Any, List
import json
from pathlib import Path


class UnslothQLoRAPipeline:
    """
    Memory-efficient fine-tuning pipeline using Unsloth with QLoRA.
    Supports 4-bit quantization and efficient gradient checkpointing.
    """

    def __init__(
        self,
        model_name: str = "unsloth/llama-3-8b-bnb-4bit",
        max_seq_length: int = 2048,
        load_in_4bit: bool = True,
        lora_r: int = 16,
        lora_alpha: int = 16,
        lora_dropout: float = 0.05,
        target_modules: Optional[List[str]] = None
    ):
        """
        Initialize the Unsloth QLoRA pipeline.

        Args:
            model_name: HuggingFace model name or path
            max_seq_length: Maximum sequence length for training
            load_in_4bit: Whether to load model in 4-bit quantization
            lora_r: LoRA rank (lower = more efficient, higher = more capacity)
            lora_alpha: LoRA scaling factor
            lora_dropout: Dropout rate for LoRA layers
            target_modules: List of modules to apply LoRA (None = auto-detect)
        """
        self.model_name = model_name
        self.max_seq_length = max_seq_length
        self.load_in_4bit = load_in_4bit
        self.lora_r = lora_r
        self.lora_alpha = lora_alpha
        self.lora_dropout = lora_dropout
        self.target_modules = target_modules or ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]

        self.model = None
        self.tokenizer = None

    def setup_model(self):
        """Load and configure the model with Unsloth optimizations."""
        try:
            from unsloth import FastLanguageModel

            self.model, self.tokenizer = FastLanguageModel.from_pretrained(
                model_name=self.model_name,
                max_seq_length=self.max_seq_length,
                dtype=None,  # Auto-detect
                load_in_4bit=self.load_in_4bit,
            )

            # Add LoRA adapters
            self.model = FastLanguageModel.get_peft_model(
                self.model,
                r=self.lora_r,
                target_modules=self.target_modules,
                lora_alpha=self.lora_alpha,
                lora_dropout=self.lora_dropout,
                bias="none",
                use_gradient_checkpointing="unsloth",  # Unsloth-optimized checkpointing
                random_state=3407,
                use_rslora=False,
                loftq_config=None,
            )

            print(f"✓ Model loaded: {self.model_name}")
            print(f"✓ LoRA config: r={self.lora_r}, alpha={self.lora_alpha}")
            return True

        except ImportError:
            print("Error: Unsloth not installed. Install with: pip install unsloth")
            return False
        except Exception as e:
            print(f"Error loading model: {e}")
            return False

    def prepare_dataset(
        self,
        dataset_path: str,
        dataset_format: str = "alpaca",
        split: str = "train"
    ):
        """
        Prepare dataset for training.

        Args:
            dataset_path: Path to dataset or HuggingFace dataset name
            dataset_format: Format of dataset (alpaca, sharegpt, etc.)
            split: Dataset split to use

        Returns:
            Processed dataset ready for training
        """
        from datasets import load_dataset

        try:
            # Load dataset
            if Path(dataset_path).exists():
                dataset = load_dataset("json", data_files=dataset_path, split=split)
            else:
                dataset = load_dataset(dataset_path, split=split)

            # Format dataset based on type
            if dataset_format == "alpaca":
                dataset = self._format_alpaca(dataset)
            elif dataset_format == "sharegpt":
                dataset = self._format_sharegpt(dataset)
            else:
                raise ValueError(f"Unsupported format: {dataset_format}")

            print(f"✓ Dataset loaded: {len(dataset)} examples")
            return dataset

        except Exception as e:
            print(f"Error loading dataset: {e}")
            return None

    def _format_alpaca(self, dataset):
        """Format dataset in Alpaca style."""
        alpaca_prompt = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

        def formatting_func(examples):
            instructions = examples.get("instruction", [""] * len(examples["input"]))
            inputs = examples.get("input", [""] * len(examples["instruction"]))
            outputs = examples.get("output", [""] * len(examples["instruction"]))

            texts = []
            for instruction, input_text, output in zip(instructions, inputs, outputs):
                text = alpaca_prompt.format(instruction, input_text, output) + self.tokenizer.eos_token
                texts.append(text)

            return {"text": texts}

        return dataset.map(formatting_func, batched=True)

    def _format_sharegpt(self, dataset):
        """Format dataset in ShareGPT style."""
        def formatting_func(examples):
            conversations = examples["conversations"]
            texts = []

            for convo in conversations:
                text = ""
                for message in convo:
                    role = message.get("from", "human")
                    content = message.get("value", "")

                    if role == "human":
                        text += f"### Human:\n{content}\n\n"
                    elif role == "gpt":
                        text += f"### Assistant:\n{content}\n\n"

                text += self.tokenizer.eos_token
                texts.append(text)

            return {"text": texts}

        return dataset.map(formatting_func, batched=True)

    def train(
        self,
        dataset,
        output_dir: str = "./outputs/unsloth_qlora",
        num_train_epochs: int = 3,
        per_device_train_batch_size: int = 2,
        gradient_accumulation_steps: int = 4,
        learning_rate: float = 2e-4,
        warmup_steps: int = 5,
        logging_steps: int = 10,
        save_steps: int = 100,
        **kwargs
    ):
        """
        Train the model with QLoRA.

        Args:
            dataset: Prepared training dataset
            output_dir: Directory to save checkpoints
            num_train_epochs: Number of training epochs
            per_device_train_batch_size: Batch size per device
            gradient_accumulation_steps: Steps to accumulate gradients
            learning_rate: Learning rate
            warmup_steps: Number of warmup steps
            logging_steps: Log every N steps
            save_steps: Save checkpoint every N steps
            **kwargs: Additional training arguments
        """
        from transformers import TrainingArguments
        from trl import SFTTrainer

        # Setup training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_train_epochs,
            per_device_train_batch_size=per_device_train_batch_size,
            gradient_accumulation_steps=gradient_accumulation_steps,
            learning_rate=learning_rate,
            warmup_steps=warmup_steps,
            logging_steps=logging_steps,
            save_steps=save_steps,
            fp16=not torch.cuda.is_bf16_supported(),
            bf16=torch.cuda.is_bf16_supported(),
            optim="adamw_8bit",
            weight_decay=0.01,
            lr_scheduler_type="cosine",
            seed=3407,
            **kwargs
        )

        # Initialize trainer
        trainer = SFTTrainer(
            model=self.model,
            tokenizer=self.tokenizer,
            train_dataset=dataset,
            dataset_text_field="text",
            max_seq_length=self.max_seq_length,
            dataset_num_proc=2,
            packing=False,
            args=training_args,
        )

        print("Starting training...")
        trainer.train()

        print(f"✓ Training complete. Saved to {output_dir}")
        return trainer

    def save_lora_adapter(self, output_path: str, adapter_name: Optional[str] = None):
        """
        Save only the LoRA adapter weights.

        Args:
            output_path: Path to save adapter
            adapter_name: Optional name for the adapter
        """
        if self.model is None:
            print("Error: No model loaded")
            return

        Path(output_path).mkdir(parents=True, exist_ok=True)

        # Save LoRA adapter
        self.model.save_pretrained(output_path)
        self.tokenizer.save_pretrained(output_path)

        # Save metadata
        metadata = {
            "adapter_name": adapter_name or Path(output_path).name,
            "base_model": self.model_name,
            "lora_r": self.lora_r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "target_modules": self.target_modules,
            "max_seq_length": self.max_seq_length,
        }

        with open(Path(output_path) / "adapter_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        print(f"✓ LoRA adapter saved to {output_path}")

    def inference(self, prompt: str, max_new_tokens: int = 256, temperature: float = 0.7):
        """
        Run inference with the fine-tuned model.

        Args:
            prompt: Input prompt
            max_new_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        from unsloth import FastLanguageModel

        FastLanguageModel.for_inference(self.model)

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            use_cache=True
        )

        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return result


def create_training_config(
    model_name: str = "unsloth/llama-3-8b-bnb-4bit",
    dataset_path: str = "./data/train.json",
    output_dir: str = "./outputs/unsloth_qlora",
    lora_r: int = 16,
    learning_rate: float = 2e-4,
    num_epochs: int = 3,
    batch_size: int = 2
) -> Dict[str, Any]:
    """Create a training configuration dictionary."""
    return {
        "model": {
            "name": model_name,
            "max_seq_length": 2048,
            "load_in_4bit": True,
        },
        "lora": {
            "r": lora_r,
            "alpha": lora_r,
            "dropout": 0.05,
            "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
        },
        "training": {
            "dataset_path": dataset_path,
            "dataset_format": "alpaca",
            "output_dir": output_dir,
            "num_train_epochs": num_epochs,
            "per_device_train_batch_size": batch_size,
            "gradient_accumulation_steps": 4,
            "learning_rate": learning_rate,
            "warmup_steps": 5,
            "logging_steps": 10,
            "save_steps": 100,
        }
    }


if __name__ == "__main__":
    # Example usage
    print("Unsloth QLoRA Pipeline - Example")
    print("=" * 50)

    # Create pipeline
    pipeline = UnslothQLoRAPipeline(
        model_name="unsloth/llama-3-8b-bnb-4bit",
        lora_r=16,
        lora_alpha=16
    )

    # Setup model
    if pipeline.setup_model():
        print("\n✓ Ready for training!")
        print("\nNext steps:")
        print("1. Prepare your dataset")
        print("2. Call pipeline.prepare_dataset()")
        print("3. Call pipeline.train()")
        print("4. Save adapter with pipeline.save_lora_adapter()")
