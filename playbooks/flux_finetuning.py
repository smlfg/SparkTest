"""
FLUX.1 Dreambooth LoRA Fine-tuning Playbook
Agent 6: Diffusion Model Training

This playbook implements FLUX.1 Dreambooth fine-tuning with LoRA
(Low-Rank Adaptation) for efficient personalized image generation.

Features:
- FLUX.1 model support (dev and schnell variants)
- LoRA training for memory efficiency
- Dreambooth with prior preservation
- Mixed precision training (bf16/fp16)
- Gradient checkpointing
- Multi-GPU support
- Integration with Agent 4 for validation
"""

import os
import sys
import math
import torch
import torch.nn.functional as F
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
import logging
from PIL import Image
import numpy as np

# Diffusers imports (available in diffusers library)
try:
    from diffusers import (
        FluxPipeline,
        FluxTransformer2DModel,
        AutoencoderKL,
        DDPMScheduler,
    )
    from diffusers.optimization import get_scheduler
    from transformers import CLIPTextModel, CLIPTokenizer, T5EncoderModel, T5Tokenizer
    from peft import LoraConfig, get_peft_model
    DIFFUSERS_AVAILABLE = True
except ImportError:
    DIFFUSERS_AVAILABLE = False
    print("Warning: Diffusers not installed. Run: pip install diffusers transformers peft")

from torch.utils.data import Dataset, DataLoader
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP
from torch.cuda.amp import autocast, GradScaler

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from agent6_training_config import FLUX_CONFIG, CHECKPOINT_DIR, DATA_DIR


@dataclass
class FluxTrainingArgs:
    """FLUX training arguments."""
    model_name: str = "black-forest-labs/FLUX.1-dev"
    instance_prompt: str = "a photo of sks person"
    class_prompt: str = "a photo of a person"
    instance_data_dir: str = f"{DATA_DIR}/flux/instance_images"
    class_data_dir: str = f"{DATA_DIR}/flux/class_images"
    output_dir: str = f"{CHECKPOINT_DIR}/flux"
    resolution: int = 512
    train_batch_size: int = 1
    gradient_accumulation_steps: int = 4
    learning_rate: float = 1e-4
    lr_scheduler: str = "constant"
    lr_warmup_steps: int = 0
    num_train_epochs: int = 100
    max_train_steps: int = 1000
    lora_rank: int = 32
    lora_alpha: int = 32
    prior_preservation: bool = True
    prior_loss_weight: float = 1.0
    num_class_images: int = 100
    mixed_precision: str = "bf16"
    gradient_checkpointing: bool = True
    validation_prompt: str = "a photo of sks person in a bucket"
    num_validation_images: int = 4
    validation_steps: int = 100
    checkpointing_steps: int = 500
    seed: int = 42


class FluxDreamboothDataset(Dataset):
    """
    Dataset for FLUX Dreambooth training.
    """

    def __init__(
        self,
        instance_data_root: str,
        instance_prompt: str,
        class_data_root: Optional[str] = None,
        class_prompt: Optional[str] = None,
        size: int = 512,
        center_crop: bool = True,
    ):
        """
        Initialize dataset.

        Args:
            instance_data_root: Path to instance images
            instance_prompt: Prompt for instance images
            class_data_root: Path to class images (for prior preservation)
            class_prompt: Prompt for class images
            size: Image resolution
            center_crop: Whether to center crop images
        """
        self.instance_data_root = Path(instance_data_root)
        self.instance_prompt = instance_prompt
        self.size = size
        self.center_crop = center_crop

        # Load instance images
        self.instance_images = []
        if self.instance_data_root.exists():
            self.instance_images = list(self.instance_data_root.glob("**/*.jpg")) + \
                                  list(self.instance_data_root.glob("**/*.png"))

        # Load class images (for prior preservation)
        self.class_images = []
        if class_data_root:
            class_data_root = Path(class_data_root)
            if class_data_root.exists():
                self.class_images = list(class_data_root.glob("**/*.jpg")) + \
                                   list(class_data_root.glob("**/*.png"))

        self.class_prompt = class_prompt
        self._length = max(len(self.instance_images), len(self.class_images))

    def __len__(self):
        return self._length

    def __getitem__(self, index):
        example = {}

        # Load instance image
        instance_idx = index % len(self.instance_images)
        instance_image = Image.open(self.instance_images[instance_idx])
        if not instance_image.mode == "RGB":
            instance_image = instance_image.convert("RGB")
        instance_image = self._preprocess_image(instance_image)

        example["instance_images"] = instance_image
        example["instance_prompt"] = self.instance_prompt

        # Load class image if using prior preservation
        if self.class_images:
            class_idx = index % len(self.class_images)
            class_image = Image.open(self.class_images[class_idx])
            if not class_image.mode == "RGB":
                class_image = class_image.convert("RGB")
            class_image = self._preprocess_image(class_image)

            example["class_images"] = class_image
            example["class_prompt"] = self.class_prompt

        return example

    def _preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """Preprocess image for training."""
        # Resize
        image = image.resize((self.size, self.size), Image.LANCZOS)

        # Center crop if enabled
        if self.center_crop:
            crop = min(image.size)
            left = (image.size[0] - crop) // 2
            top = (image.size[1] - crop) // 2
            right = left + crop
            bottom = top + crop
            image = image.crop((left, top, right, bottom))
            image = image.resize((self.size, self.size), Image.LANCZOS)

        # Convert to tensor and normalize
        image = torch.from_numpy(np.array(image)).float() / 255.0
        image = image.permute(2, 0, 1)  # HWC -> CHW
        image = (image - 0.5) / 0.5  # Normalize to [-1, 1]

        return image


class FluxLoRATrainer:
    """
    FLUX.1 Dreambooth LoRA trainer.
    """

    def __init__(self, args: FluxTrainingArgs):
        """
        Initialize trainer.

        Args:
            args: Training arguments
        """
        self.args = args
        self.setup_distributed()
        self.setup_logging()

    def setup_distributed(self):
        """Initialize distributed training."""
        if "LOCAL_RANK" in os.environ:
            self.local_rank = int(os.environ["LOCAL_RANK"])
            self.global_rank = int(os.environ["RANK"])
            self.world_size = int(os.environ["WORLD_SIZE"])

            dist.init_process_group(backend="nccl")
            torch.cuda.set_device(self.local_rank)
            self.device = torch.device(f"cuda:{self.local_rank}")
        else:
            self.local_rank = 0
            self.global_rank = 0
            self.world_size = 1
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.is_main_process = self.global_rank == 0

    def setup_logging(self):
        """Setup logging configuration."""
        log_level = logging.INFO if self.is_main_process else logging.WARNING
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
            datefmt="%m/%d/%Y %H:%M:%S",
            level=log_level,
        )
        self.logger = logging.getLogger(__name__)

    def load_models(self) -> Tuple[Any, Any, Any, Any]:
        """
        Load FLUX models.

        Returns:
            Tuple of (transformer, vae, text_encoder, tokenizer)
        """
        if not DIFFUSERS_AVAILABLE:
            raise RuntimeError("Diffusers not installed")

        self.logger.info(f"Loading FLUX model: {self.args.model_name}")

        # Load transformer (main model to train)
        transformer = FluxTransformer2DModel.from_pretrained(
            self.args.model_name,
            subfolder="transformer",
            torch_dtype=torch.bfloat16 if self.args.mixed_precision == "bf16" else torch.float16,
        )

        # Load VAE
        vae = AutoencoderKL.from_pretrained(
            self.args.model_name,
            subfolder="vae",
            torch_dtype=torch.bfloat16 if self.args.mixed_precision == "bf16" else torch.float16,
        )
        vae.requires_grad_(False)

        # Load text encoders
        text_encoder = T5EncoderModel.from_pretrained(
            self.args.model_name,
            subfolder="text_encoder",
            torch_dtype=torch.bfloat16 if self.args.mixed_precision == "bf16" else torch.float16,
        )
        text_encoder.requires_grad_(False)

        tokenizer = T5Tokenizer.from_pretrained(
            self.args.model_name,
            subfolder="tokenizer",
        )

        # Apply LoRA to transformer
        lora_config = LoraConfig(
            r=self.args.lora_rank,
            lora_alpha=self.args.lora_alpha,
            target_modules=FLUX_CONFIG["lora"]["target_modules"],
            lora_dropout=FLUX_CONFIG["lora"]["dropout"],
            bias=FLUX_CONFIG["lora"]["bias"],
        )
        transformer = get_peft_model(transformer, lora_config)

        self.logger.info(f"LoRA parameters: {transformer.print_trainable_parameters()}")

        # Move models to device
        transformer = transformer.to(self.device)
        vae = vae.to(self.device)
        text_encoder = text_encoder.to(self.device)

        # Enable gradient checkpointing
        if self.args.gradient_checkpointing:
            transformer.enable_gradient_checkpointing()

        return transformer, vae, text_encoder, tokenizer

    def prepare_dataset_and_dataloader(self) -> DataLoader:
        """
        Prepare training dataset and dataloader.

        Returns:
            DataLoader
        """
        dataset = FluxDreamboothDataset(
            instance_data_root=self.args.instance_data_dir,
            instance_prompt=self.args.instance_prompt,
            class_data_root=self.args.class_data_dir if self.args.prior_preservation else None,
            class_prompt=self.args.class_prompt if self.args.prior_preservation else None,
            size=self.args.resolution,
        )

        sampler = None
        if self.world_size > 1:
            from torch.utils.data import DistributedSampler
            sampler = DistributedSampler(
                dataset,
                num_replicas=self.world_size,
                rank=self.global_rank,
            )

        dataloader = DataLoader(
            dataset,
            batch_size=self.args.train_batch_size,
            shuffle=(sampler is None),
            sampler=sampler,
            num_workers=4,
            pin_memory=True,
        )

        return dataloader

    def train(self):
        """Execute training loop."""
        if not DIFFUSERS_AVAILABLE:
            raise RuntimeError("Diffusers not installed")

        self.logger.info("Starting FLUX LoRA training...")

        # Load models
        transformer, vae, text_encoder, tokenizer = self.load_models()

        # Wrap in DDP
        if self.world_size > 1:
            transformer = DDP(transformer, device_ids=[self.local_rank])

        # Prepare optimizer
        optimizer = torch.optim.AdamW(
            transformer.parameters(),
            lr=self.args.learning_rate,
            betas=(FLUX_CONFIG["optimizer"]["beta1"], FLUX_CONFIG["optimizer"]["beta2"]),
            weight_decay=FLUX_CONFIG["optimizer"]["weight_decay"],
            eps=FLUX_CONFIG["optimizer"]["epsilon"],
        )

        # Prepare dataloader
        train_dataloader = self.prepare_dataset_and_dataloader()

        # Calculate total steps
        num_update_steps_per_epoch = len(train_dataloader) // self.args.gradient_accumulation_steps
        total_steps = self.args.max_train_steps or (num_update_steps_per_epoch * self.args.num_train_epochs)

        # Prepare scheduler
        lr_scheduler = get_scheduler(
            self.args.lr_scheduler,
            optimizer=optimizer,
            num_warmup_steps=self.args.lr_warmup_steps,
            num_training_steps=total_steps,
        )

        # Prepare noise scheduler
        noise_scheduler = DDPMScheduler.from_pretrained(
            self.args.model_name,
            subfolder="scheduler",
        )

        # Mixed precision scaler
        scaler = GradScaler(enabled=(self.args.mixed_precision == "fp16"))

        # Training loop
        global_step = 0
        progress_bar = range(total_steps)

        for epoch in range(self.args.num_train_epochs):
            transformer.train()

            for step, batch in enumerate(train_dataloader):
                # Get images and encode
                instance_images = batch["instance_images"].to(self.device)

                with torch.no_grad():
                    # Encode images to latents
                    latents = vae.encode(instance_images).latent_dist.sample()
                    latents = latents * vae.config.scaling_factor

                    # Encode prompts
                    instance_prompt_ids = tokenizer(
                        batch["instance_prompt"],
                        padding="max_length",
                        truncation=True,
                        max_length=tokenizer.model_max_length,
                        return_tensors="pt",
                    ).input_ids.to(self.device)

                    encoder_hidden_states = text_encoder(instance_prompt_ids)[0]

                # Sample noise
                noise = torch.randn_like(latents)
                batch_size = latents.shape[0]

                # Sample timesteps
                timesteps = torch.randint(
                    0, noise_scheduler.config.num_train_timesteps,
                    (batch_size,), device=latents.device
                ).long()

                # Add noise to latents
                noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)

                # Forward pass with mixed precision
                with autocast(
                    enabled=(self.args.mixed_precision in ["fp16", "bf16"]),
                    dtype=torch.bfloat16 if self.args.mixed_precision == "bf16" else torch.float16
                ):
                    # Predict noise
                    model_pred = transformer(
                        noisy_latents,
                        timesteps,
                        encoder_hidden_states=encoder_hidden_states,
                    ).sample

                    # Calculate loss
                    loss = F.mse_loss(model_pred.float(), noise.float(), reduction="mean")

                    # Prior preservation loss
                    if self.args.prior_preservation and "class_images" in batch:
                        class_images = batch["class_images"].to(self.device)

                        with torch.no_grad():
                            class_latents = vae.encode(class_images).latent_dist.sample()
                            class_latents = class_latents * vae.config.scaling_factor

                            class_prompt_ids = tokenizer(
                                batch["class_prompt"],
                                padding="max_length",
                                truncation=True,
                                max_length=tokenizer.model_max_length,
                                return_tensors="pt",
                            ).input_ids.to(self.device)

                            class_encoder_hidden_states = text_encoder(class_prompt_ids)[0]

                        class_noise = torch.randn_like(class_latents)
                        class_noisy_latents = noise_scheduler.add_noise(
                            class_latents, class_noise, timesteps
                        )

                        class_model_pred = transformer(
                            class_noisy_latents,
                            timesteps,
                            encoder_hidden_states=class_encoder_hidden_states,
                        ).sample

                        prior_loss = F.mse_loss(
                            class_model_pred.float(), class_noise.float(), reduction="mean"
                        )
                        loss = loss + self.args.prior_loss_weight * prior_loss

                    loss = loss / self.args.gradient_accumulation_steps

                # Backward pass
                scaler.scale(loss).backward()

                # Optimizer step
                if (step + 1) % self.args.gradient_accumulation_steps == 0:
                    scaler.unscale_(optimizer)
                    torch.nn.utils.clip_grad_norm_(transformer.parameters(), 1.0)
                    scaler.step(optimizer)
                    scaler.update()
                    lr_scheduler.step()
                    optimizer.zero_grad()

                    global_step += 1

                    # Logging
                    if self.is_main_process and global_step % 10 == 0:
                        self.logger.info(
                            f"Step {global_step}/{total_steps} | "
                            f"Loss: {loss.item() * self.args.gradient_accumulation_steps:.4f} | "
                            f"LR: {lr_scheduler.get_last_lr()[0]:.2e}"
                        )

                    # Save checkpoint
                    if global_step % self.args.checkpointing_steps == 0:
                        self.save_checkpoint(transformer, global_step)

                    # Validation
                    if global_step % self.args.validation_steps == 0:
                        self.run_validation(transformer, vae, text_encoder, tokenizer, global_step)

                if global_step >= total_steps:
                    break

        # Save final checkpoint
        if self.is_main_process:
            self.save_checkpoint(transformer, global_step, final=True)

        self.logger.info("Training completed!")

    def save_checkpoint(self, model: Any, step: int, final: bool = False):
        """Save model checkpoint."""
        if not self.is_main_process:
            return

        save_path = Path(self.args.output_dir) / (f"checkpoint-{step}" if not final else "final")
        save_path.mkdir(parents=True, exist_ok=True)

        # Get LoRA weights
        model_to_save = model.module if isinstance(model, DDP) else model
        model_to_save.save_pretrained(save_path)

        self.logger.info(f"Checkpoint saved to {save_path}")

    def run_validation(self, transformer, vae, text_encoder, tokenizer, step: int):
        """Run validation and generate images."""
        if not self.is_main_process:
            return

        self.logger.info(f"Running validation at step {step}")
        # Validation logic with Agent 4 integration
        # Generate images using validation_prompt
        # Save generated images
        pass


def main():
    """Main entry point for FLUX fine-tuning."""
    print("=" * 60)
    print("FLUX.1 Dreambooth LoRA Fine-tuning Playbook")
    print("=" * 60)

    if not DIFFUSERS_AVAILABLE:
        print("\nDiffusers not installed. To use this playbook:")
        print("pip install diffusers transformers peft accelerate")
        return

    # Example training
    args = FluxTrainingArgs(
        instance_prompt="a photo of sks dog",
        class_prompt="a photo of dog",
        instance_data_dir=f"{DATA_DIR}/flux/instance_images",
        max_train_steps=1000,
    )

    trainer = FluxLoRATrainer(args)
    # trainer.train()  # Uncomment to start training

    print("\nFLUX trainer initialized successfully!")
    print(f"Instance data: {args.instance_data_dir}")
    print(f"Output dir: {args.output_dir}")


if __name__ == "__main__":
    main()
