#!/bin/bash
#
# FP4 Quantization Playbook
# Quantizes models to 4-bit floating-point precision
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
MODEL_NAME=""
MODEL_PATH=""
OUTPUT_DIR="models"
PRECISION="fp4"
COMPUTE_DTYPE="float16"
DOUBLE_QUANT=true

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS] MODEL_NAME"
    echo ""
    echo "Options:"
    echo "  -m, --model-path PATH      Path to the original model"
    echo "  -o, --output-dir DIR       Output directory (default: models)"
    echo "  -p, --precision TYPE       Precision type: fp4, nf4, int4 (default: fp4)"
    echo "  -d, --compute-dtype TYPE   Compute dtype (default: float16)"
    echo "  --no-double-quant          Disable double quantization"
    echo "  -h, --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 llama-70b"
    echo "  $0 -m /path/to/model -o ./quantized llama-70b"
    echo "  $0 -p nf4 mistral-7b"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--model-path)
            MODEL_PATH="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -p|--precision)
            PRECISION="$2"
            shift 2
            ;;
        -d|--compute-dtype)
            COMPUTE_DTYPE="$2"
            shift 2
            ;;
        --no-double-quant)
            DOUBLE_QUANT=false
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}"
            usage
            exit 1
            ;;
        *)
            MODEL_NAME="$1"
            shift
            ;;
    esac
done

# Validate model name
if [ -z "$MODEL_NAME" ]; then
    echo -e "${RED}Error: MODEL_NAME is required${NC}"
    usage
    exit 1
fi

# Print configuration
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}FP4 Quantization Playbook${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Model Name:       $MODEL_NAME"
echo "Model Path:       ${MODEL_PATH:-auto-detect}"
echo "Output Directory: $OUTPUT_DIR"
echo "Precision:        $PRECISION"
echo "Compute Dtype:    $COMPUTE_DTYPE"
echo "Double Quant:     $DOUBLE_QUANT"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run quantization
echo -e "${YELLOW}Starting quantization...${NC}"
echo ""

python3 - <<EOF
import sys
sys.path.insert(0, '.')

from agent8_quant_api import QuantizationEngine

# Initialize engine
engine = QuantizationEngine(
    precision="$PRECISION",
    compute_dtype="$COMPUTE_DTYPE",
    double_quant=$DOUBLE_QUANT
)

# Quantize model
result = engine.quantize(
    model_name="$MODEL_NAME",
    model_path="${MODEL_PATH}" if "${MODEL_PATH}" else None,
    output_path="$OUTPUT_DIR/${MODEL_NAME}-${PRECISION}"
)

print("\n" + "="*60)
print("Quantization Complete!")
print("="*60)
print(f"\nModel: {result['quantized_name']}")
print(f"Output: {result['output_path']}")
print(f"Compression: {result['compression_ratio']:.2f}x")
print(f"Size Reduction: {result['memory_reduction_gb']:.2f} GB ({result['memory_reduction_percent']:.1f}%)")
EOF

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Quantization successful!${NC}"
    echo -e "${GREEN}  Output: $OUTPUT_DIR/${MODEL_NAME}-${PRECISION}${NC}"
else
    echo ""
    echo -e "${RED}✗ Quantization failed with exit code $EXIT_CODE${NC}"
    exit $EXIT_CODE
fi
