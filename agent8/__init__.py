"""
Agent 8: Model Optimization
Quantization, Compression, and Multi-Modal Inference
"""

__version__ = "1.0.0"
__author__ = "SparkTest Team"

from agent8_quant_api import (
    QUANTIZED_MODELS,
    QuantizationEngine,
    MultiModalInference,
    get_quantization_config,
    quantize_model,
    run_multimodal_inference
)

__all__ = [
    "QUANTIZED_MODELS",
    "QuantizationEngine",
    "MultiModalInference",
    "get_quantization_config",
    "quantize_model",
    "run_multimodal_inference"
]
