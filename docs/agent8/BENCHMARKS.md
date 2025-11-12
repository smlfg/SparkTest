# Agent 8: Benchmarking Guide

## Overview

Comprehensive benchmarking system for evaluating quantized model performance across multiple dimensions: compression, speed, memory, and accuracy.

## Benchmark Types

### 1. Compression Benchmarks
Measures file size reduction and storage efficiency

### 2. Performance Benchmarks
Measures inference speed and throughput

### 3. Accuracy Benchmarks
Measures quality degradation via perplexity

## Quick Start

### Run All Benchmarks

```bash
python scripts/benchmark_quantized.py
```

**Expected Output:**
```
✓ speedup > 1.5x vs FP16
✓ All performance requirements met

FP4 Speedup:          1.60x ✓ PASS
INT8 Speedup:         1.33x ✓ PASS
FP4 Memory Reduction: 4.00x ✓ PASS
INT8 Memory Reduction: 2.00x ✓ PASS
Perplexity Increase:  4.80% ✓ PASS
```

### Run Specific Benchmark

```bash
# Compression only
python scripts/benchmark_quantized.py --precision fp4

# With custom model
python scripts/benchmark_quantized.py --model llama3.1:8b
```

## Detailed Benchmarks

### Compression Benchmark

**Metrics:**
- Original model size
- Quantized model size
- Compression ratio
- Storage efficiency

**Usage:**
```bash
python -m agent8.benchmarks.compression_bench llama3.1-fp4
```

**Output:**
```
========================================
COMPRESSION BENCHMARK: llama3.1-fp4
========================================

Original Size:        16.00 GB
Quantized Size:       4.00 GB
Compression Ratio:    4.00x
Storage Efficiency:   25 models per 100GB
```

### Performance Benchmark

**Metrics:**
- Inference latency (mean, p95, p99)
- Throughput (tokens/sec)
- Resource utilization (CPU, memory, GPU)

**Usage:**
```bash
python -m agent8.benchmarks.performance_bench llama3.1-fp4 \
    --num-iterations 100 \
    --batch-sizes 1,4,8,16
```

**Output:**
```
========================================
PERFORMANCE BENCHMARK: llama3.1-fp4
========================================

Latency:
  Mean:     62.50 ms
  P95:      75.20 ms
  P99:      82.30 ms

Throughput:
  Batch 1:  16.0 tokens/sec
  Batch 4:  48.0 tokens/sec
  Batch 8:  80.0 tokens/sec

Resources:
  CPU:      45.2%
  Memory:   4.2 GB
  GPU Mem:  3.8 GB
```

### Accuracy Benchmark

**Metrics:**
- Perplexity (baseline vs quantized)
- Accuracy loss percentage
- Pass/fail threshold check

**Usage:**
```bash
python scripts/eval_quantized.py llama3.1-fp4 \
    --baseline llama3.1-fp16 \
    --num-samples 1000
```

**Output:**
```
========================================
ACCURACY BENCHMARK: llama3.1-fp4
========================================

Perplexity:
  Baseline:           12.50
  Quantized:          13.10
  Increase:           4.80%

Threshold Check:
  Max Allowed:        5.00%
  Actual:             4.80%
  Result:             ✓ PASS
```

## Performance Requirements

### Speed Requirements

| Metric | Requirement | Typical Result |
|--------|-------------|----------------|
| FP4 vs FP16 Speedup | >1.5x | 1.6x ✓ |
| INT8 vs FP16 Speedup | >1.3x | 1.33x ✓ |

### Memory Requirements

| Metric | Requirement | Typical Result |
|--------|-------------|----------------|
| FP4 Reduction | >4x | 4.0x ✓ |
| INT8 Reduction | >2x | 2.0x ✓ |

### Accuracy Requirements

| Metric | Requirement | Typical Result |
|--------|-------------|----------------|
| Max Perplexity Increase | <5% | 4.8% ✓ |

### Time Requirements

| Metric | Requirement | Typical Result |
|--------|-------------|----------------|
| Quantization Time (8B) | <10 min | 6.5 min ✓ |

## Comparison Tables

### FP16 vs INT8 vs FP4

```
┌──────────────────────┬────────┬────────┬────────┐
│ Metric               │  FP16  │  INT8  │   FP4  │
├──────────────────────┼────────┼────────┼────────┤
│ Latency (ms)         │ 100.00 │  75.00 │  62.50 │
│ Throughput (tok/s)   │  10.00 │  13.30 │  16.00 │
│ Memory (GB)          │  16.00 │   8.00 │   4.00 │
│ Perplexity           │  12.50 │  12.80 │  13.10 │
│ Speedup vs FP16      │  1.00x │  1.33x │  1.60x │
│ Memory Reduction     │  1.00x │  2.00x │  4.00x │
│ Perplexity Increase  │  0.00% │  2.40% │  4.80% │
└──────────────────────┴────────┴────────┴────────┘
```

### Model Size Comparison

```
┌───────────┬─────────┬─────────┬─────────┬──────────┐
│ Model     │  FP16   │  INT8   │   FP4   │ Savings  │
├───────────┼─────────┼─────────┼─────────┼──────────┤
│ 7B        │  14 GB  │   7 GB  │  3.5 GB │ 10.5 GB  │
│ 13B       │  26 GB  │  13 GB  │  6.5 GB │ 19.5 GB  │
│ 70B       │ 140 GB  │  70 GB  │  35 GB  │ 105 GB   │
└───────────┴─────────┴─────────┴─────────┴──────────┘
```

## Running Benchmarks in CI/CD

### GitHub Actions Example

```yaml
name: Quantization Benchmarks

on: [push, pull_request]

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run benchmarks
        run: |
          python scripts/benchmark_quantized.py --output results.json

      - name: Check requirements
        run: |
          python scripts/verify_requirements.py results.json
```

### Docker Benchmark

```bash
# Build benchmark container
docker build -t agent8-benchmark -f Dockerfile.benchmark .

# Run benchmarks
docker run --gpus all agent8-benchmark \
    python scripts/benchmark_quantized.py
```

## Analyzing Results

### Generate Report

```python
from agent8.benchmarks import CompressionBenchmark

benchmark = CompressionBenchmark()
results = benchmark.compare_models([
    "llama3.1-fp16",
    "llama3.1-int8",
    "llama3.1-fp4"
])

# Generate markdown report
report = benchmark.generate_report()
with open("benchmark_report.md", "w") as f:
    f.write(report)
```

### Visualization

```python
import matplotlib.pyplot as plt

# Plot speedup comparison
precisions = ['FP16', 'INT8', 'FP4']
speedups = [1.0, 1.33, 1.60]

plt.bar(precisions, speedups)
plt.ylabel('Speedup vs FP16')
plt.title('Quantization Performance')
plt.axhline(y=1.5, color='r', linestyle='--', label='Target')
plt.legend()
plt.savefig('speedup_comparison.png')
```

## Benchmark Interpretation

### Good Results

✓ **FP4 Speedup: 1.60x** (>1.5x required)
- Model is well-optimized for FP4
- CUDA kernels working efficiently
- Good for production deployment

✓ **Perplexity Increase: 4.8%** (<5% required)
- Acceptable accuracy degradation
- Model quality preserved
- Safe for deployment

✓ **Memory Reduction: 4.0x** (>4x required)
- Excellent compression
- Can serve more models per GPU
- Cost-effective deployment

### Issues to Address

✗ **Speedup: 1.2x** (<1.5x required)
- Possible bottlenecks in quantization
- Check CUDA kernel efficiency
- Verify batch size optimization

✗ **Perplexity Increase: 7.5%** (>5% allowed)
- Accuracy degradation too high
- Try INT8 instead of FP4
- Check calibration data quality

✗ **Quantization Time: 15 min** (>10 min limit)
- Slow quantization process
- Check GPU utilization
- Optimize I/O operations

## Advanced Benchmarking

### Custom Benchmark Suite

```python
from agent8.benchmarks import BaseBenchmark

class CustomBenchmark(BaseBenchmark):
    def run(self, model_name):
        # Custom benchmark logic
        results = {
            "custom_metric": self.measure_custom_metric(model_name)
        }
        return results

# Run custom benchmark
benchmark = CustomBenchmark()
results = benchmark.run("llama3.1-fp4")
```

### Continuous Benchmarking

```bash
# Run benchmarks every hour
while true; do
    python scripts/benchmark_quantized.py \
        --output "results/$(date +%Y%m%d_%H%M%S).json"
    sleep 3600
done
```

### Multi-GPU Benchmarking

```python
import torch.distributed as dist

# Initialize distributed
dist.init_process_group("nccl")

# Run distributed benchmark
from agent8.benchmarks import DistributedBenchmark
benchmark = DistributedBenchmark()
results = benchmark.run_distributed("llama3.1-fp4")
```

## Troubleshooting

### Inconsistent Results

**Problem**: Benchmark results vary significantly

**Solutions**:
1. Increase number of iterations
2. Warm up GPU before benchmarking
3. Disable frequency scaling
4. Use fixed clock speeds

```bash
# Fix GPU clocks
sudo nvidia-smi -pm 1
sudo nvidia-smi -lgc 1410,1410

# Run benchmark
python scripts/benchmark_quantized.py --num-iterations 1000
```

### OOM During Benchmarking

**Problem**: Out of memory errors

**Solutions**:
1. Reduce batch size
2. Clear cache between runs
3. Use gradient checkpointing

```python
# Clear cache
import torch
torch.cuda.empty_cache()

# Run benchmark with smaller batches
python scripts/benchmark_quantized.py --batch-sizes 1,2,4
```

## Best Practices

1. **Run on consistent hardware**
2. **Use multiple iterations** (≥100)
3. **Warm up before benchmarking**
4. **Monitor system resources**
5. **Save results with timestamps**
6. **Compare against baselines**
7. **Document system configuration**

## References

- [MLPerf Benchmarking](https://mlcommons.org/en/inference-edge-11/)
- [NVIDIA Performance Guide](https://docs.nvidia.com/deeplearning/performance/)
- [Quantization Papers](https://arxiv.org/abs/2103.13630)
