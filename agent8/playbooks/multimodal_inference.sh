#!/bin/bash
#
# Multi-Modal Inference Playbook
# Run inference with image and text inputs
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
MODEL_NAME=""
TEXT=""
IMAGE=""
QUANTIZED=true
OUTPUT_FILE=""
BATCH_MODE=false

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS] MODEL_NAME"
    echo ""
    echo "Options:"
    echo "  -t, --text TEXT            Text input"
    echo "  -i, --image PATH           Image path or URL"
    echo "  -q, --quantized BOOL       Use quantized model (default: true)"
    echo "  -o, --output FILE          Save output to file"
    echo "  -b, --batch FILE           Batch mode: process inputs from JSON file"
    echo "  -h, --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  # Text-only inference"
    echo "  $0 -t \"Explain quantum computing\" llama-70b-fp4"
    echo ""
    echo "  # Image-only inference"
    echo "  $0 -i \"image.jpg\" llama-70b-fp4"
    echo ""
    echo "  # Multi-modal inference"
    echo "  $0 -t \"Describe this image\" -i \"photo.jpg\" llama-70b-fp4"
    echo ""
    echo "  # Batch inference"
    echo "  $0 -b inputs.json llama-70b-fp4"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--text)
            TEXT="$2"
            shift 2
            ;;
        -i|--image)
            IMAGE="$2"
            shift 2
            ;;
        -q|--quantized)
            QUANTIZED="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        -b|--batch)
            BATCH_MODE=true
            BATCH_FILE="$2"
            shift 2
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

# Validate inputs
if [ -z "$MODEL_NAME" ]; then
    echo -e "${RED}Error: MODEL_NAME is required${NC}"
    usage
    exit 1
fi

if [ "$BATCH_MODE" = false ] && [ -z "$TEXT" ] && [ -z "$IMAGE" ]; then
    echo -e "${RED}Error: At least one of --text or --image is required${NC}"
    usage
    exit 1
fi

# Print configuration
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Multi-Modal Inference Playbook${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Model:     $MODEL_NAME"
echo "Quantized: $QUANTIZED"
if [ "$BATCH_MODE" = true ]; then
    echo "Mode:      Batch"
    echo "Input:     $BATCH_FILE"
else
    echo "Mode:      Single"
    echo "Text:      ${TEXT:-none}"
    echo "Image:     ${IMAGE:-none}"
fi
echo ""

# Run inference
echo -e "${YELLOW}Running inference...${NC}"
echo ""

if [ "$BATCH_MODE" = true ]; then
    # Batch inference
    python3 - <<EOF
import sys
import json
sys.path.insert(0, '.')

from agent8_quant_api import MultiModalInference

# Load batch inputs
with open("$BATCH_FILE", 'r') as f:
    inputs = json.load(f)

# Initialize inference engine
engine = MultiModalInference("$MODEL_NAME", quantized=$QUANTIZED)

# Run batch inference
results = engine.batch_infer(inputs)

# Print results
print("\n" + "="*60)
print("Batch Inference Results")
print("="*60 + "\n")

for i, result in enumerate(results):
    print(f"Sample {i+1}:")
    print(f"  Mode: {result['mode']}")
    print(f"  Output: {result['output'][:100]}...")
    print(f"  Time: {result['inference_time']:.3f}s")
    print()

# Save results if output file specified
if "$OUTPUT_FILE":
    with open("$OUTPUT_FILE", 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Results saved to: $OUTPUT_FILE")
EOF
else
    # Single inference
    python3 - <<EOF
import sys
import json
sys.path.insert(0, '.')

from agent8_quant_api import MultiModalInference

# Initialize inference engine
engine = MultiModalInference("$MODEL_NAME", quantized=$QUANTIZED)

# Prepare inputs
text = "$TEXT" if "$TEXT" else None
image = "$IMAGE" if "$IMAGE" else None

# Run inference
result = engine.infer(text=text, image=image)

# Print results
print("\n" + "="*60)
print("Inference Result")
print("="*60 + "\n")

print(f"Model: {result['model']}")
print(f"Mode:  {result['mode']}")
print(f"\nInput:")
if result['input']['text']:
    print(f"  Text:  {result['input']['text'][:100]}...")
if result['input']['image']:
    print(f"  Image: {result['input']['image']}")

print(f"\nOutput:")
print(f"  {result['output']}")

print(f"\nPerformance:")
print(f"  Time:     {result['inference_time']:.3f}s")
print(f"  Device:   {result['device']}")
print(f"  Quantized: {result['quantized']}")

# Save results if output file specified
if "$OUTPUT_FILE":
    with open("$OUTPUT_FILE", 'w') as f:
        json.dump(result, f, indent=2)
    print(f"\n✓ Results saved to: $OUTPUT_FILE")
EOF
fi

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✓ Inference completed successfully!${NC}"
else
    echo ""
    echo -e "${RED}✗ Inference failed with exit code $EXIT_CODE${NC}"
    exit $EXIT_CODE
fi
