"""
Unit tests for inference module
"""

import pytest
from agent8.inference import MultiModalEngine, InferenceConfig
from agent8_quant_api import MultiModalInference


class TestMultiModalInference:
    """Test multi-modal inference"""

    def test_text_inference(self):
        """Test text-only inference"""
        inference = MultiModalInference("test-model")
        result = inference.infer(text="Test prompt")

        assert result["mode"] == "text_only"
        assert "output" in result
        assert result["inference_time"] > 0

    def test_inference_config(self):
        """Test inference configuration"""
        config = InferenceConfig(max_length=256, temperature=0.8)
        assert config.max_length == 256
        assert config.temperature == 0.8

    def test_batch_inference(self):
        """Test batch inference"""
        inference = MultiModalInference("test-model")
        inputs = [
            {"text": "Prompt 1"},
            {"text": "Prompt 2"}
        ]
        results = inference.batch_infer(inputs)

        assert len(results) == 2
        assert all("output" in r for r in results)


class TestMultiModalEngine:
    """Test multi-modal engine"""

    def test_engine_initialization(self):
        """Test engine initialization"""
        engine = MultiModalEngine("test-model", quantized=True)
        assert engine.model_name == "test-model"
        assert engine.quantized == True

    def test_model_info(self):
        """Test model info retrieval"""
        engine = MultiModalEngine("test-model")
        info = engine.get_model_info()

        assert info["model_name"] == "test-model"
        assert "capabilities" in info
        assert info["capabilities"]["multimodal"] == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
