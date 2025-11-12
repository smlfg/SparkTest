# Agent 8: Architecture Documentation

## Overview

Agent 8 is a comprehensive model optimization system that provides:
- FP4 quantization for large language models
- Multi-modal inference (image + text)
- Performance benchmarking
- Model registry and tracking

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Agent 8 API Layer                     │
│                 (agent8_quant_api.py)                   │
├─────────────────────────────────────────────────────────┤
│  QuantizationEngine  │  MultiModalInference             │
└──────────┬───────────┴──────────┬──────────────────────┘
           │                      │
    ┌──────▼──────┐        ┌─────▼──────┐
    │ Quantization│        │ Inference  │
    │   Module    │        │   Module   │
    └──────┬──────┘        └─────┬──────┘
           │                     │
    ┌──────▼──────────────────────▼──────┐
    │         Model Registry              │
    └──────┬──────────────────────────────┘
           │
    ┌──────▼──────┐
    │ Benchmarks  │
    └─────────────┘
```

## Core Components

### 1. Quantization Module (`agent8/quantization/`)

**Purpose**: Compress models to 4-bit precision

**Components**:
- `quantizer.py`: FP4/NF4/INT4 quantization implementation
- `optimizer.py`: Model pruning and optimization utilities

**Key Classes**:
- `FP4Quantizer`: Main quantization engine
- `QuantizationConfig`: Configuration management
- `DynamicQuantizer`: Runtime quantization

**Flow**:
```
Model (FP32) → Quantization Config → FP4Quantizer → Quantized Model (FP4)
                                                   ↓
                                            Model Registry
```

### 2. Inference Module (`agent8/inference/`)

**Purpose**: Run inference with quantized models

**Components**:
- `multimodal.py`: Multi-modal inference (text + image)
- `text_inference.py`: Text-only inference
- `vision_inference.py`: Image-only inference

**Key Classes**:
- `MultiModalEngine`: Main inference engine
- `InferenceConfig`: Generation parameters
- `StreamingInferenceEngine`: Streaming generation

**Inference Modes**:
1. Text-only: Language model inference
2. Image-only: Vision model inference
3. Multi-modal: Combined image + text

### 3. Benchmarking Module (`agent8/benchmarks/`)

**Purpose**: Measure performance of quantized models

**Components**:
- `compression_bench.py`: Size and compression metrics
- `performance_bench.py`: Speed and throughput metrics
- `accuracy_bench.py`: Accuracy degradation analysis

**Metrics Collected**:
- Compression ratio
- Model size reduction
- Inference latency (mean, p95, p99)
- Throughput (samples/sec)
- Accuracy degradation
- Memory usage

### 4. Model Registry (`agent8/registry/`)

**Purpose**: Track and manage quantized models

**Components**:
- `model_registry.py`: Centralized model tracking

**Features**:
- Model registration
- Search and filtering
- Version tracking
- Statistics and analytics
- Import/export capabilities

**Registry Schema**:
```json
{
  "version": "1.0",
  "created_at": "timestamp",
  "models": {
    "model_id": {
      "model_name": "llama-70b",
      "quantized_name": "llama-70b-fp4",
      "precision": "fp4",
      "bits": 4,
      "original_size_gb": 140.0,
      "quantized_size_gb": 35.0,
      "compression_ratio": 4.0,
      "output_path": "/path/to/model",
      "created_at": "timestamp"
    }
  }
}
```

## Playbooks

Automated scripts for common operations:

### 1. `quantize_to_fp4.sh`
Quantizes models to FP4 precision

**Usage**:
```bash
./agent8/playbooks/quantize_to_fp4.sh llama-70b
```

### 2. `multimodal_inference.sh`
Runs multi-modal inference

**Usage**:
```bash
./agent8/playbooks/multimodal_inference.sh \
  -t "Describe this image" \
  -i photo.jpg \
  llama-70b-fp4
```

### 3. `run_benchmarks.sh`
Executes comprehensive benchmarks

**Usage**:
```bash
./agent8/playbooks/run_benchmarks.sh llama-70b-fp4
```

## Data Flow

### Quantization Flow
```
1. Load model configuration
2. Initialize FP4Quantizer
3. Apply quantization to weights
4. Save quantized model
5. Register in model registry
6. Return metadata
```

### Inference Flow
```
1. Load quantized model
2. Process inputs (text/image)
3. Run forward pass
4. Generate output
5. Return results + metrics
```

### Benchmarking Flow
```
1. Load quantized model
2. Run compression benchmark
   - Measure size reduction
   - Calculate compression ratio
3. Run performance benchmark
   - Measure latency
   - Measure throughput
4. Run accuracy benchmark
   - Compare to baseline
   - Calculate degradation
5. Save results
6. Generate report
```

## Configuration

### Quantization Config
```python
{
    "bits": 4,
    "quant_type": "fp4",
    "compute_dtype": "float16",
    "double_quant": True,
    "block_size": 64
}
```

### Inference Config
```python
{
    "max_length": 512,
    "temperature": 0.7,
    "top_p": 0.9,
    "do_sample": True,
    "image_size": (224, 224)
}
```

## API Interface

### Python API
```python
from agent8_quant_api import QuantizationEngine, MultiModalInference

# Quantization
engine = QuantizationEngine(precision="fp4")
result = engine.quantize("llama-70b")

# Inference
inference = MultiModalInference("llama-70b-fp4")
output = inference.infer(text="Hello", image="photo.jpg")
```

### Command Line
```bash
# Quantization
agent8-quantize llama-70b -p fp4 -o models/

# Inference
agent8-infer llama-70b-fp4 -t "Hello world"

# Benchmarking
agent8-benchmark llama-70b-fp4 -t all
```

## Performance Characteristics

### FP4 Quantization
- **Compression Ratio**: 4x
- **Memory Reduction**: 75%
- **Accuracy Degradation**: < 3%
- **Latency Overhead**: +3-5%

### Supported Models
- Llama (7B, 13B, 70B)
- Mistral (7B)
- Falcon (7B, 40B)
- Custom models (extensible)

## Dependencies

### Core Dependencies
- Agent 4: Base inference engine
- Agent 5: Model serving infrastructure

### External Dependencies
- PyTorch >= 2.0
- Transformers >= 4.30
- BitsAndBytes >= 0.41
- Accelerate >= 0.20

## Extension Points

### Adding New Precision Formats
1. Extend `QuantizationConfig`
2. Implement quantization logic in `FP4Quantizer`
3. Update `get_quantization_config()`

### Adding New Model Types
1. Add model size estimate in `_estimate_model_size()`
2. Update supported models list
3. Test quantization and inference

### Custom Benchmarks
1. Create new benchmark class
2. Inherit from base benchmark
3. Implement `run()` method
4. Register in playbook

## Security Considerations

- Model files not included in git (see `.gitignore`)
- Registry contains only metadata
- No hardcoded credentials
- Sandboxed execution for playbooks

## Future Enhancements

1. **INT8 Quantization**: Add 8-bit support
2. **Model Pruning**: Structural pruning
3. **Knowledge Distillation**: Teacher-student training
4. **ONNX Export**: Cross-platform deployment
5. **Distributed Inference**: Multi-GPU support
6. **Model Serving API**: REST/gRPC endpoints
