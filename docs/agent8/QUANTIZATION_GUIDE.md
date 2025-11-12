# Agent 8: Quantization Guide

## Overview

This guide covers model quantization using Agent 8's optimization system. We support multiple quantization formats optimized for different use cases.

## Supported Quantization Formats

### FP4 (4-bit Floating Point)
- **Compression**: 4x reduction
- **Accuracy**: ~95-97% of original
- **Speedup**: 1.5-1.8x vs FP16
- **Best for**: Large language models (70B+)

### INT8 (8-bit Integer)
- **Compression**: 2x reduction
- **Accuracy**: ~98-99% of original
- **Speedup**: 1.3-1.5x vs FP16
- **Best for**: Production deployments requiring high accuracy

### NF4 (4-bit NormalFloat)
- **Compression**: 4x reduction
- **Accuracy**: ~96-98% of original
- **Speedup**: 1.6-1.9x vs FP16
- **Best for**: Models with normally distributed weights

## Quick Start

### 1. Quantize a Model to FP4

```bash
./scripts/quantize_fp4.sh llama3.1:8b
```

**Output:**
```
✓ Quantized model created
Model:                llama3.1:8b
Output:               /workspace/models/quantized/llama3.1-8b-fp4.gguf
Compression Ratio:    4.00x
Memory Reduction:     75.0%
```

### 2. Evaluate Quantized Model

```bash
python scripts/eval_quantized.py llama3.1-fp4
```

**Expected:**
```
✓ accuracy_loss < 3%
Perplexity Increase:  4.8%
Threshold:            ✓ PASS
```

### 3. Benchmark Performance

```bash
python scripts/benchmark_quantized.py
```

**Expected:**
```
✓ speedup > 1.5x vs FP16
FP4 Speedup:          1.60x ✓ PASS
INT8 Speedup:         1.33x ✓ PASS
```

## Detailed Usage

### Using Python API

```python
from agent8_quant_api import QuantizationEngine

# Initialize engine
engine = QuantizationEngine(precision="fp4")

# Quantize model
result = engine.quantize(
    model_name="llama3.1:8b",
    output_path="/workspace/models/quantized"
)

print(f"Compression: {result['compression_ratio']:.2f}x")
print(f"Size: {result['quantized_size_gb']:.2f} GB")
```

### Using Command Line

```bash
# FP4 Quantization
agent8-quantize llama3.1:8b -p fp4 -o /workspace/models/quantized

# INT8 Quantization
agent8-quantize llama3.1:8b -p int8 -o /workspace/models/quantized

# Custom configuration
./scripts/quantize_fp4.sh llama3.1:8b \
    --output-dir /custom/path \
    --compute-dtype float16 \
    --double-quant
```

## Quantization Methods

### NVIDIA FP4 Quantization

The default quantization method using NVIDIA's FP4 format:

**Features:**
- Block-wise quantization (default: 64 elements per block)
- Double quantization for scales
- Optimized CUDA kernels
- GGUF output format

**Configuration:**
```python
{
    "bits": 4,
    "quant_type": "fp4",
    "compute_dtype": "float16",
    "double_quant": True,
    "block_size": 64
}
```

### INT8 Quantization

Standard 8-bit integer quantization:

**Features:**
- Symmetric or asymmetric quantization
- Per-channel or per-tensor
- Dynamic or static quantization
- Compatible with ONNX Runtime

**Configuration:**
```python
{
    "bits": 8,
    "quant_type": "int8",
    "symmetric": True,
    "per_channel": True
}
```

## Output Formats

### GGUF (GPT-Generated Unified Format)

The default output format for quantized models.

**Features:**
- ✓ Model architecture preserved
- ✓ Tokenizer preserved
- ✓ Generation config preserved
- ✓ Cross-platform compatibility
- ✓ Efficient loading

**File Structure:**
```
llama3.1-8b-fp4.gguf         # Main model file
llama3.1-8b-fp4.gguf.meta.json  # Metadata
```

### Safetensors

Alternative format for PyTorch compatibility:

```bash
export OUTPUT_FORMAT=safetensors
./scripts/quantize_fp4.sh llama3.1:8b
```

## Performance Optimization

### Quantization Time

**Target**: < 10 minutes for 8B models

**Optimization tips:**
1. Use GPU acceleration
2. Enable double quantization
3. Use appropriate block size
4. Pre-download models

**Example:**
```bash
# Fast quantization
CUDA_VISIBLE_DEVICES=0 ./scripts/quantize_fp4.sh llama3.1:8b

# Expected time: 5-8 minutes for 8B model
```

### Memory Requirements

| Model Size | FP16 RAM | FP4 RAM | INT8 RAM |
|------------|----------|---------|----------|
| 7B         | 14 GB    | 3.5 GB  | 7 GB     |
| 13B        | 26 GB    | 6.5 GB  | 13 GB    |
| 70B        | 140 GB   | 35 GB   | 70 GB    |

## Accuracy Preservation

### Perplexity Metrics

**Target**: Max 5% increase in perplexity

**Typical results:**
- FP4: 4-5% increase
- INT8: 2-3% increase
- NF4: 3-4% increase

### Validation Process

1. **Quantize model**
```bash
./scripts/quantize_fp4.sh llama3.1:8b
```

2. **Evaluate perplexity**
```bash
python scripts/eval_quantized.py llama3.1-fp4 \
    --baseline llama3.1-fp16 \
    --num-samples 1000
```

3. **Check results**
```
Perplexity Increase: 4.8% ✓ PASS (< 5%)
```

## Troubleshooting

### Out of Memory

**Problem**: Quantization fails due to OOM

**Solution**:
```bash
# Use smaller batch size
export BATCH_SIZE=1
./scripts/quantize_fp4.sh llama3.1:8b

# Or use CPU
export CUDA_VISIBLE_DEVICES=""
./scripts/quantize_fp4.sh llama3.1:8b
```

### Accuracy Loss Too High

**Problem**: Perplexity increase > 5%

**Solutions**:
1. Try INT8 instead of FP4
2. Use NF4 for normally distributed weights
3. Increase block size
4. Disable double quantization

```bash
# Try INT8
agent8-quantize llama3.1:8b -p int8

# Or adjust FP4 settings
export BLOCK_SIZE=128
export DOUBLE_QUANT=false
./scripts/quantize_fp4.sh llama3.1:8b
```

### Slow Quantization

**Problem**: Taking > 10 minutes for 8B model

**Solutions**:
1. Check GPU utilization
2. Use faster storage (NVMe)
3. Increase block size
4. Pre-download model

```bash
# Check GPU
nvidia-smi

# Optimize
export BLOCK_SIZE=128
CUDA_VISIBLE_DEVICES=0 ./scripts/quantize_fp4.sh llama3.1:8b
```

## Best Practices

### 1. Choose Right Precision

- **70B+ models**: Use FP4
- **Production systems**: Use INT8
- **Research/development**: Use FP16

### 2. Validate Accuracy

Always run evaluation after quantization:

```bash
python scripts/eval_quantized.py <model> --num-samples 1000
```

### 3. Benchmark Performance

Compare precisions before deployment:

```bash
python scripts/benchmark_quantized.py --model llama3.1:8b
```

### 4. Monitor Memory

Track memory usage during quantization:

```bash
watch -n 1 nvidia-smi
```

### 5. Version Control

Keep track of quantization configs:

```bash
# Save config
./scripts/quantize_fp4.sh llama3.1:8b | tee quantization.log

# Track in git
git add quantization.log
git commit -m "Quantized llama3.1:8b to FP4"
```

## Integration with Agent 5

### Import Base Models

```python
from agent5.models import load_model

# Load base model from Agent 5
base_model = load_model("llama3.1:8b")

# Quantize with Agent 8
from agent8_quant_api import QuantizationEngine
engine = QuantizationEngine()
quantized = engine.quantize(base_model)
```

### Export Quantized Models

```bash
# Set export directory
export QUANTIZED_MODELS_DIR="/workspace/models/quantized"

# Quantize and export
./scripts/quantize_fp4.sh llama3.1:8b

# Models automatically available to other agents
```

## Advanced Topics

### Custom Quantization

Implement custom quantization logic:

```python
from agent8.quantization import FP4Quantizer

class CustomQuantizer(FP4Quantizer):
    def quantize_weights(self, weights):
        # Custom quantization logic
        return super().quantize_weights(weights)
```

### Distributed Quantization

Quantize multiple models in parallel:

```bash
# Create job array
for model in llama3.1:8b mistral:7b falcon:7b; do
    ./scripts/quantize_fp4.sh $model &
done
wait
```

### Fine-tuning After Quantization

```python
from agent8.quantization import FP4Quantizer
from agent8.training import QLoRA

# Quantize
quantizer = FP4Quantizer()
quantized_model = quantizer.quantize(model)

# Fine-tune with QLoRA
trainer = QLoRA(quantized_model)
trainer.train(dataset)
```

## References

- [BitsAndBytes Documentation](https://github.com/TimDettmers/bitsandbytes)
- [GGUF Format Specification](https://github.com/ggerganov/ggml/blob/master/docs/gguf.md)
- [Quantization Research Paper](https://arxiv.org/abs/2208.07339)

## Support

For issues or questions:
- GitHub Issues: https://github.com/smlfg/SparkTest/issues
- Documentation: `/docs/agent8/`
- API Reference: `http://localhost:8888/docs`
