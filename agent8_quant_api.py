"""
Agent 8: Model Optimization API
Quantization and Compression Interface
"""

from typing import Dict, List, Optional, Union
from pathlib import Path
import json

# Quantized Models Registry
QUANTIZED_MODELS = {
    "fp4_models": ["llama-70b-fp4", "mistral-7b-fp4"],
    "quant_script": "quantize_to_fp4.sh"
}


class QuantizationEngine:
    """
    FP4 Quantization Engine for LLMs
    Supports 4-bit floating-point quantization with optimized memory usage
    """

    def __init__(self, precision: str = "fp4", device: str = "cuda"):
        """
        Initialize quantization engine

        Args:
            precision: Quantization precision ('fp4', 'nf4', 'int4')
            device: Target device ('cuda', 'cpu')
        """
        self.precision = precision
        self.device = device
        self.registry_path = Path("models/registry.json")

    def quantize(
        self,
        model_name: str,
        model_path: Optional[str] = None,
        output_path: Optional[str] = None,
        compute_dtype: str = "float16",
        double_quant: bool = True
    ) -> Dict[str, any]:
        """
        Quantize a model to FP4 precision

        Args:
            model_name: Name of the model to quantize
            model_path: Path to the original model
            output_path: Path to save quantized model
            compute_dtype: Computation data type
            double_quant: Enable double quantization for better compression

        Returns:
            Dictionary with quantization results and metadata
        """
        from agent8.quantization.quantizer import FP4Quantizer

        quantizer = FP4Quantizer(
            precision=self.precision,
            device=self.device,
            compute_dtype=compute_dtype,
            double_quant=double_quant
        )

        result = quantizer.quantize_model(
            model_name=model_name,
            model_path=model_path,
            output_path=output_path
        )

        # Register the quantized model
        self._register_model(result)

        return result

    def _register_model(self, model_info: Dict):
        """Register quantized model in the registry"""
        from agent8.registry.model_registry import ModelRegistry

        registry = ModelRegistry(registry_path=str(self.registry_path))
        registry.register(model_info)

    def list_models(self) -> List[Dict]:
        """List all quantized models in registry"""
        from agent8.registry.model_registry import ModelRegistry

        registry = ModelRegistry(registry_path=str(self.registry_path))
        return registry.list_all()

    def benchmark(self, model_name: str) -> Dict[str, float]:
        """
        Benchmark a quantized model

        Args:
            model_name: Name of the model to benchmark

        Returns:
            Dictionary with performance metrics
        """
        from agent8.benchmarks.compression_bench import CompressionBenchmark

        benchmark = CompressionBenchmark()
        return benchmark.run(model_name)


class MultiModalInference:
    """
    Multi-Modal Inference Engine
    Supports image + text inference with quantized models
    """

    def __init__(self, model_name: str, quantized: bool = True):
        """
        Initialize multi-modal inference engine

        Args:
            model_name: Name of the model to use
            quantized: Whether to use quantized version
        """
        self.model_name = model_name
        self.quantized = quantized
        self._load_model()

    def _load_model(self):
        """Load the model for inference"""
        from agent8.inference.multimodal import MultiModalEngine

        self.engine = MultiModalEngine(
            model_name=self.model_name,
            quantized=self.quantized
        )

    def infer(
        self,
        text: Optional[str] = None,
        image: Optional[Union[str, Path]] = None,
        **kwargs
    ) -> Dict[str, any]:
        """
        Run multi-modal inference

        Args:
            text: Text input
            image: Image path or URL
            **kwargs: Additional inference parameters

        Returns:
            Dictionary with inference results
        """
        return self.engine.generate(text=text, image=image, **kwargs)

    def batch_infer(
        self,
        inputs: List[Dict[str, any]],
        batch_size: int = 8
    ) -> List[Dict[str, any]]:
        """
        Run batch multi-modal inference

        Args:
            inputs: List of input dictionaries with 'text' and/or 'image'
            batch_size: Batch size for processing

        Returns:
            List of inference results
        """
        return self.engine.batch_generate(inputs, batch_size=batch_size)


def get_quantization_config(precision: str = "fp4") -> Dict:
    """
    Get recommended quantization configuration

    Args:
        precision: Quantization precision level

    Returns:
        Configuration dictionary
    """
    configs = {
        "fp4": {
            "bits": 4,
            "quant_type": "fp4",
            "compute_dtype": "float16",
            "double_quant": True,
            "compression_ratio": 4.0,
            "recommended_for": ["llama", "mistral", "falcon"]
        },
        "nf4": {
            "bits": 4,
            "quant_type": "nf4",
            "compute_dtype": "bfloat16",
            "double_quant": True,
            "compression_ratio": 4.0,
            "recommended_for": ["llama", "mistral"]
        },
        "int4": {
            "bits": 4,
            "quant_type": "int4",
            "compute_dtype": "int8",
            "double_quant": False,
            "compression_ratio": 4.0,
            "recommended_for": ["bert", "roberta"]
        }
    }

    return configs.get(precision, configs["fp4"])


# Convenience functions
def quantize_model(model_name: str, **kwargs) -> Dict:
    """Quick model quantization"""
    engine = QuantizationEngine()
    return engine.quantize(model_name, **kwargs)


def run_multimodal_inference(model_name: str, text: str = None, image: str = None) -> Dict:
    """Quick multi-modal inference"""
    inference = MultiModalInference(model_name)
    return inference.infer(text=text, image=image)


if __name__ == "__main__":
    # Example usage
    print("Agent 8: Model Optimization API")
    print(f"Available FP4 Models: {QUANTIZED_MODELS['fp4_models']}")
    print(f"Quantization Script: {QUANTIZED_MODELS['quant_script']}")

    # Get FP4 config
    config = get_quantization_config("fp4")
    print(f"\nFP4 Configuration: {json.dumps(config, indent=2)}")
