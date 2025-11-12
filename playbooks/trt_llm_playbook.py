"""
TensorRT-LLM Playbook - High-Performance Optimized Inference
Build and deploy TensorRT-optimized LLM engines
"""

import os
import json
import subprocess
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrecisionMode(Enum):
    """TensorRT precision modes"""
    FLOAT32 = "float32"
    FLOAT16 = "float16"
    BFLOAT16 = "bfloat16"
    INT8 = "int8"
    FP8 = "fp8"


class QuantizationMode(Enum):
    """Quantization strategies"""
    NONE = "none"
    INT8_WEIGHT_ONLY = "int8_weight_only"
    INT4_WEIGHT_ONLY = "int4_weight_only"
    INT4_AWQ = "int4_awq"
    INT8_SQ = "int8_sq"  # Smooth Quant
    FP8 = "fp8"


@dataclass
class TRTLLMEngineConfig:
    """TensorRT-LLM Engine Build Configuration"""

    # Model configuration
    model_dir: str
    model_type: str = "llama"  # llama, gpt, falcon, etc.
    checkpoint_dir: Optional[str] = None

    # Engine parameters
    max_batch_size: int = 8
    max_input_len: int = 1024
    max_output_len: int = 512
    max_beam_width: int = 1

    # Precision and quantization
    precision: PrecisionMode = PrecisionMode.FLOAT16
    quantization: QuantizationMode = QuantizationMode.NONE

    # Parallelism
    tensor_parallel_size: int = 1
    pipeline_parallel_size: int = 1
    world_size: int = 1

    # Optimization features
    use_gpt_attention_plugin: bool = True
    use_gemm_plugin: bool = True
    use_layernorm_plugin: bool = True
    enable_context_fmha: bool = True  # Fused Multi-Head Attention
    enable_paged_kv_cache: bool = True
    remove_input_padding: bool = True

    # Performance tuning
    max_num_tokens: Optional[int] = None
    use_custom_all_reduce: bool = False
    multi_block_mode: bool = False

    # Output
    output_dir: str = "trt_engines"
    engine_name: str = "model_engine"

    def to_build_args(self) -> List[str]:
        """Convert configuration to build command arguments"""
        args = [
            "--model_dir", self.model_dir,
            "--dtype", self.precision.value,
            "--max_batch_size", str(self.max_batch_size),
            "--max_input_len", str(self.max_input_len),
            "--max_output_len", str(self.max_output_len),
            "--max_beam_width", str(self.max_beam_width),
            "--output_dir", self.output_dir,
        ]

        if self.checkpoint_dir:
            args.extend(["--checkpoint_dir", self.checkpoint_dir])

        if self.quantization != QuantizationMode.NONE:
            args.extend(["--use_weight_only", "--weight_only_precision", self.quantization.value])

        if self.tensor_parallel_size > 1:
            args.extend(["--tp_size", str(self.tensor_parallel_size)])

        if self.pipeline_parallel_size > 1:
            args.extend(["--pp_size", str(self.pipeline_parallel_size)])

        # Plugins
        if self.use_gpt_attention_plugin:
            args.append("--use_gpt_attention_plugin")
        if self.use_gemm_plugin:
            args.append("--use_gemm_plugin")
        if self.enable_context_fmha:
            args.append("--enable_context_fmha")
        if self.enable_paged_kv_cache:
            args.append("--paged_kv_cache")
        if self.remove_input_padding:
            args.append("--remove_input_padding")

        return args


@dataclass
class TRTLLMServerConfig:
    """TensorRT-LLM Server Configuration"""

    # Engine configuration
    engine_dir: str
    tokenizer_dir: str

    # Server settings
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "info"

    # Performance
    max_num_sequences: int = 256
    max_tokens_in_paged_kv_cache: Optional[int] = None
    kv_cache_free_gpu_mem_fraction: float = 0.9

    # Batching
    enable_chunked_context: bool = False
    streaming: bool = True

    def to_server_args(self) -> List[str]:
        """Convert configuration to server arguments"""
        args = [
            "--engine_dir", self.engine_dir,
            "--tokenizer_dir", self.tokenizer_dir,
            "--host", self.host,
            "--port", str(self.port),
            "--log_level", self.log_level,
        ]
        return args


class TRTLLMEngineBuilder:
    """TensorRT-LLM Engine Builder"""

    def __init__(self, config: TRTLLMEngineConfig):
        self.config = config
        logger.info("TensorRT-LLM Engine Builder initialized")

    def build_engine(self, dry_run: bool = False) -> bool:
        """
        Build TensorRT engine from model

        Args:
            dry_run: If True, only print the command without executing

        Returns:
            Success status
        """
        logger.info("=" * 70)
        logger.info("Building TensorRT-LLM Engine")
        logger.info("=" * 70)
        logger.info(f"Model: {self.config.model_type}")
        logger.info(f"Precision: {self.config.precision.value}")
        logger.info(f"Quantization: {self.config.quantization.value}")
        logger.info(f"Tensor Parallel: {self.config.tensor_parallel_size}")
        logger.info(f"Output: {self.config.output_dir}")

        try:
            # Create output directory
            os.makedirs(self.config.output_dir, exist_ok=True)

            # Build command
            cmd = ["python", "-m", "tensorrt_llm.commands.build"]
            cmd.extend(self.config.to_build_args())

            logger.info(f"\nBuild command:\n{' '.join(cmd)}\n")

            if dry_run:
                logger.info("Dry run mode - skipping actual build")
                return True

            # Execute build
            logger.info("Starting engine build (this may take several minutes)...")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)

            logger.info("Engine build completed successfully!")
            logger.info(f"Engine saved to: {self.config.output_dir}")

            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Engine build failed: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during build: {e}")
            return False

    def convert_checkpoint(
        self,
        model_path: str,
        output_dir: str,
        tensor_parallel: int = 1
    ) -> bool:
        """
        Convert HuggingFace checkpoint to TRT-LLM format

        Args:
            model_path: Path to HuggingFace model
            output_dir: Output directory for converted checkpoint
            tensor_parallel: Tensor parallelism degree

        Returns:
            Success status
        """
        logger.info("Converting checkpoint to TRT-LLM format...")

        try:
            os.makedirs(output_dir, exist_ok=True)

            cmd = [
                "python", "-m", "tensorrt_llm.commands.convert_checkpoint",
                "--model_dir", model_path,
                "--output_dir", output_dir,
                "--dtype", self.config.precision.value,
                "--tp_size", str(tensor_parallel)
            ]

            logger.info(f"Conversion command: {' '.join(cmd)}")

            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info("Checkpoint conversion completed successfully!")

            return True

        except Exception as e:
            logger.error(f"Checkpoint conversion failed: {e}")
            return False

    def save_config(self, path: str):
        """Save engine configuration"""
        with open(path, 'w') as f:
            json.dump(asdict(self.config), f, indent=2)
        logger.info(f"Configuration saved to {path}")


class TRTLLMDeployment:
    """TensorRT-LLM Server Deployment"""

    def __init__(self, config: TRTLLMServerConfig):
        self.config = config
        self.process = None
        logger.info("TRT-LLM Deployment Manager initialized")

    def deploy(self, background: bool = True) -> bool:
        """
        Deploy TRT-LLM inference server

        Args:
            background: Run server in background

        Returns:
            Success status
        """
        logger.info("Deploying TRT-LLM server...")
        logger.info(f"Engine: {self.config.engine_dir}")
        logger.info(f"Endpoint: http://{self.config.host}:{self.config.port}")

        try:
            cmd = ["python", "-m", "tensorrt_llm.serve"]
            cmd.extend(self.config.to_server_args())

            logger.info(f"Server command: {' '.join(cmd)}")

            if background:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                logger.info(f"TRT-LLM server started (PID: {self.process.pid})")
            else:
                subprocess.run(cmd, check=True)

            return True

        except Exception as e:
            logger.error(f"Failed to deploy TRT-LLM server: {e}")
            return False

    def stop(self):
        """Stop the TRT-LLM server"""
        if self.process:
            logger.info("Stopping TRT-LLM server...")
            self.process.terminate()
            self.process.wait()
            logger.info("TRT-LLM server stopped")


class TRTOptimizer:
    """TensorRT Optimization Utilities"""

    @staticmethod
    def recommend_precision(
        model_size_gb: float,
        target_latency_ms: float,
        gpu_memory_gb: float
    ) -> PrecisionMode:
        """
        Recommend optimal precision mode

        Args:
            model_size_gb: Model size in GB
            target_latency_ms: Target latency in milliseconds
            gpu_memory_gb: Available GPU memory

        Returns:
            Recommended precision mode
        """
        # If model doesn't fit in memory with FP16, use quantization
        if model_size_gb > gpu_memory_gb * 0.8:
            return PrecisionMode.INT8

        # For low latency requirements, use FP16
        if target_latency_ms < 50:
            return PrecisionMode.FLOAT16

        # For extreme performance, use INT8
        if target_latency_ms < 20:
            return PrecisionMode.INT8

        return PrecisionMode.FLOAT16

    @staticmethod
    def recommend_quantization(
        model_size_gb: float,
        quality_requirement: str = "high"
    ) -> QuantizationMode:
        """
        Recommend quantization strategy

        Args:
            model_size_gb: Model size
            quality_requirement: "high", "medium", or "low"

        Returns:
            Recommended quantization mode
        """
        if quality_requirement == "high":
            if model_size_gb < 20:
                return QuantizationMode.NONE
            else:
                return QuantizationMode.INT8_SQ

        elif quality_requirement == "medium":
            return QuantizationMode.INT8_WEIGHT_ONLY

        else:  # low - maximize performance
            return QuantizationMode.INT4_AWQ

    @staticmethod
    def calculate_speedup(
        baseline_ms: float,
        optimized_ms: float
    ) -> Dict[str, float]:
        """Calculate performance improvement"""
        speedup = baseline_ms / optimized_ms
        improvement_pct = ((baseline_ms - optimized_ms) / baseline_ms) * 100

        return {
            "baseline_latency_ms": baseline_ms,
            "optimized_latency_ms": optimized_ms,
            "speedup": speedup,
            "improvement_percent": improvement_pct
        }


def create_build_script(
    config: TRTLLMEngineConfig,
    output_path: str = "deployment/scripts/build_trt_engine.sh"
):
    """Create engine build script"""
    script_content = f"""#!/bin/bash
# TensorRT-LLM Engine Build Script
# Generated for Agent 4 Inference Engine

set -e

echo "=========================================="
echo "Building TensorRT-LLM Engine"
echo "=========================================="

MODEL_DIR="{config.model_dir}"
OUTPUT_DIR="{config.output_dir}"
PRECISION="{config.precision.value}"
TP_SIZE={config.tensor_parallel_size}

echo "Model: $MODEL_DIR"
echo "Output: $OUTPUT_DIR"
echo "Precision: $PRECISION"
echo "Tensor Parallel: $TP_SIZE"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Build engine
python -m tensorrt_llm.commands.build \\
    --model_dir "$MODEL_DIR" \\
    --dtype "$PRECISION" \\
    --max_batch_size {config.max_batch_size} \\
    --max_input_len {config.max_input_len} \\
    --max_output_len {config.max_output_len} \\
    --tp_size $TP_SIZE \\
    --output_dir "$OUTPUT_DIR" \\
    {"--use_gpt_attention_plugin \\" if config.use_gpt_attention_plugin else ""}
    {"--enable_context_fmha \\" if config.enable_context_fmha else ""}
    {"--paged_kv_cache \\" if config.enable_paged_kv_cache else ""}

echo ""
echo "Engine build completed!"
echo "Engine location: $OUTPUT_DIR"
"""

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write(script_content)
    os.chmod(output_path, 0o755)
    logger.info(f"Build script created: {output_path}")


def main():
    """Example usage of TRT-LLM playbook"""
    print("=" * 70)
    print("TensorRT-LLM Playbook - Optimized Inference")
    print("=" * 70)

    # Engine configuration
    engine_config = TRTLLMEngineConfig(
        model_dir="/models/llama-2-7b",
        model_type="llama",
        max_batch_size=8,
        max_input_len=1024,
        max_output_len=512,
        precision=PrecisionMode.FLOAT16,
        quantization=QuantizationMode.NONE,
        tensor_parallel_size=1,
        use_gpt_attention_plugin=True,
        enable_context_fmha=True,
        enable_paged_kv_cache=True,
        output_dir="trt_engines/llama-2-7b"
    )

    print("\n1. Engine Configuration:")
    print(json.dumps(asdict(engine_config), indent=2, default=str))

    # Optimization recommendations
    print("\n2. Optimization Recommendations:")
    optimizer = TRTOptimizer()

    precision = optimizer.recommend_precision(
        model_size_gb=13.0,
        target_latency_ms=30.0,
        gpu_memory_gb=24.0
    )
    print(f"Recommended Precision: {precision.value}")

    quantization = optimizer.recommend_quantization(
        model_size_gb=13.0,
        quality_requirement="high"
    )
    print(f"Recommended Quantization: {quantization.value}")

    # Performance calculation
    print("\n3. Expected Performance Improvement:")
    speedup = optimizer.calculate_speedup(
        baseline_ms=100.0,  # vLLM baseline
        optimized_ms=35.0   # TRT-LLM optimized
    )
    print(json.dumps(speedup, indent=2))

    # Create builder
    print("\n4. Engine Builder:")
    builder = TRTLLMEngineBuilder(engine_config)
    builder.save_config("configs/trt_engine_config.json")

    # Generate build script
    print("\n5. Generating Build Script:")
    create_build_script(engine_config)

    print("\n" + "=" * 70)
    print("TRT-LLM Playbook execution completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
