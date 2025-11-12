"""
Unit tests for quantization module
"""

import pytest
import torch
from agent8.quantization import FP4Quantizer, QuantizationConfig
from agent8_quant_api import QuantizationEngine


class TestFP4Quantizer:
    """Test FP4 quantization"""

    def test_quantizer_initialization(self):
        """Test quantizer can be initialized"""
        quantizer = FP4Quantizer(precision="fp4")
        assert quantizer.precision == "fp4"
        assert quantizer.double_quant == True

    def test_quantization_config(self):
        """Test quantization config"""
        config = QuantizationConfig(bits=4, quant_type="fp4")
        assert config.bits == 4
        assert config.quant_type == "fp4"

    def test_quantize_weights(self):
        """Test weight quantization"""
        quantizer = FP4Quantizer()
        weights = torch.randn(10, 10)
        quantized = quantizer.quantize_weights(weights)
        assert quantized is not None
        assert quantized.shape == weights.shape

    def test_quantize_model(self):
        """Test full model quantization"""
        engine = QuantizationEngine(precision="fp4")
        result = engine.quantize(model_name="test-model")

        assert result["status"] == "success"
        assert result["compression_ratio"] == 4.0
        assert "output_path" in result


class TestQuantizationEngine:
    """Test quantization engine API"""

    def test_engine_initialization(self):
        """Test engine initialization"""
        engine = QuantizationEngine()
        assert engine.precision == "fp4"

    def test_quantize_llama(self):
        """Test Llama model quantization"""
        engine = QuantizationEngine()
        result = engine.quantize(model_name="llama-7b")

        assert result["model_name"] == "llama-7b"
        assert result["quantized_name"] == "llama-7b-fp4"
        assert result["bits"] == 4

    def test_quantize_mistral(self):
        """Test Mistral model quantization"""
        engine = QuantizationEngine()
        result = engine.quantize(model_name="mistral-7b")

        assert result["model_name"] == "mistral-7b"
        assert result["compression_ratio"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
