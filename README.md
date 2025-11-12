# Agent 8: Model Optimization

A comprehensive model optimization system featuring FP4 quantization, multi-modal inference, and model compression benchmarking.

## Features

- **FP4 Quantization Pipeline**: Advanced 4-bit floating-point quantization for LLMs
- **Multi-Modal Inference Engine**: Support for both image and text inputs
- **Model Compression Benchmarks**: Performance and size metrics for quantized models
- **Quantized Model Registry**: Centralized registry for tracking optimized models

## Architecture

```
agent8/
├── quantization/       # FP4 quantization implementation
├── inference/          # Multi-modal inference engine
├── benchmarks/         # Compression and performance benchmarks
├── registry/           # Quantized model registry
└── playbooks/          # Automation scripts
```

## Supported Models

- Llama 70B (FP4)
- Mistral 7B (FP4)
- Custom models via extensible API

## Dependencies

- **Agent 4**: Base inference engine
- **Agent 5**: Model serving infrastructure

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Quantize a model to FP4
./playbooks/quantize_to_fp4.sh llama-70b

# Run multi-modal inference
python -m agent8.inference.multimodal --image input.jpg --text "Describe this image"

# Benchmark quantized models
python -m agent8.benchmarks.run --model llama-70b-fp4
```

## API Usage

```python
from agent8_quant_api import QUANTIZED_MODELS, QuantizationEngine

# Access available models
models = QUANTIZED_MODELS["fp4_models"]

# Initialize quantization engine
engine = QuantizationEngine(precision="fp4")

# Quantize a model
engine.quantize("llama-70b", output_path="models/llama-70b-fp4")
```

## Performance

| Model | Original Size | FP4 Size | Compression Ratio | Latency Impact |
|-------|--------------|----------|-------------------|----------------|
| Llama 70B | 140GB | 35GB | 4x | +5% |
| Mistral 7B | 14GB | 3.5GB | 4x | +3% |

## License

MIT License
