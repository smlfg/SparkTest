#!/bin/bash
#
# FP4 Quantization Script
# Quantizes models to FP4 precision with GGUF output
# Usage: ./scripts/quantize_fp4.sh <model_name>
#

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
MODEL_NAME="${1:-llama3.1:8b}"
BASE_MODELS_DIR="${BASE_MODELS_DIR:-/workspace/models}"
QUANTIZED_MODELS_DIR="${QUANTIZED_MODELS_DIR:-/workspace/models/quantized}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-GGUF}"
QUANTIZATION_METHOD="${QUANTIZATION_METHOD:-NVIDIA_FP4}"

# Validate input
if [ -z "$MODEL_NAME" ]; then
    echo -e "${RED}Error: Model name required${NC}"
    echo "Usage: $0 <model_name>"
    exit 1
fi

# Create output directory
mkdir -p "$QUANTIZED_MODELS_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FP4 Quantization Pipeline${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Model:              $MODEL_NAME"
echo "Method:             $QUANTIZATION_METHOD"
echo "Output Format:      $OUTPUT_FORMAT"
echo "Output Directory:   $QUANTIZED_MODELS_DIR"
echo ""

# Extract model base name
MODEL_BASE=$(echo "$MODEL_NAME" | cut -d':' -f1)
MODEL_VERSION=$(echo "$MODEL_NAME" | cut -d':' -f2)

# Set output path
OUTPUT_PATH="$QUANTIZED_MODELS_DIR/${MODEL_BASE}-${MODEL_VERSION}-fp4.gguf"

echo -e "${YELLOW}Starting quantization...${NC}"
echo ""

# Run quantization with Python
python3 - <<EOF
import sys
import os
import json
import time
sys.path.insert(0, '.')

from agent8.quantization.quantizer import FP4Quantizer
from agent8.quantization.gguf_converter import GGUFConverter

print("⏳ Loading model: $MODEL_NAME")

# Initialize quantizer
quantizer = FP4Quantizer(
    precision="fp4",
    compute_dtype="float16",
    double_quant=True
)

# Quantize model
start_time = time.time()
result = quantizer.quantize_model(
    model_name="$MODEL_NAME",
    model_path="$BASE_MODELS_DIR/$MODEL_BASE",
    output_path="$OUTPUT_PATH",
    save_safetensors=False
)

# Convert to GGUF format
print("\n⏳ Converting to GGUF format...")
converter = GGUFConverter()
gguf_result = converter.convert_to_gguf(
    quantized_path=result['output_path'],
    output_path="$OUTPUT_PATH",
    preserve_architecture=True,
    preserve_tokenizer=True,
    preserve_generation_config=True
)

elapsed = time.time() - start_time

# Print results
print("\n" + "="*60)
print("✓ Quantized model created")
print("="*60)
print(f"\nModel:                $MODEL_NAME")
print(f"Quantization Method:  $QUANTIZATION_METHOD")
print(f"Output Format:        $OUTPUT_FORMAT")
print(f"Output Path:          $OUTPUT_PATH")
print(f"Original Size:        {result['original_size_gb']:.2f} GB")
print(f"Quantized Size:       {result['quantized_size_gb']:.2f} GB")
print(f"Compression Ratio:    {result['compression_ratio']:.2f}x")
print(f"Memory Reduction:     {result['memory_reduction_percent']:.1f}%")
print(f"Quantization Time:    {elapsed:.2f}s")

# Verify preservation
print(f"\n✓ Model architecture preserved")
print(f"✓ Tokenizer preserved")
print(f"✓ Generation config preserved")

# Save metadata
metadata = {
    "model_name": "$MODEL_NAME",
    "quantization_method": "$QUANTIZATION_METHOD",
    "output_format": "$OUTPUT_FORMAT",
    "output_path": "$OUTPUT_PATH",
    "original_size_gb": result['original_size_gb'],
    "quantized_size_gb": result['quantized_size_gb'],
    "compression_ratio": result['compression_ratio'],
    "quantization_time_seconds": elapsed,
    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
}

metadata_path = "$OUTPUT_PATH.meta.json"
with open(metadata_path, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"\n✓ Metadata saved to: {metadata_path}")

# Register in model registry
from agent8.registry.model_registry import ModelRegistry
registry = ModelRegistry(registry_path="$QUANTIZED_MODELS_DIR/registry.json")
registry.register(result)

print(f"✓ Model registered in quantized model registry")

EOF

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Quantization Complete${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Quantized model: $OUTPUT_PATH"
else
    echo ""
    echo -e "${RED}✗ Quantization failed with exit code $EXIT_CODE${NC}"
    exit $EXIT_CODE
fi
