#!/bin/bash
#
# Benchmarking Playbook
# Run comprehensive benchmarks on quantized models
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

MODEL_NAME=""
BENCH_TYPE="all"
OUTPUT_DIR="benchmarks/results"

usage() {
    echo "Usage: $0 [OPTIONS] MODEL_NAME"
    echo ""
    echo "Options:"
    echo "  -t, --type TYPE        Benchmark type: compression, performance, accuracy, all (default: all)"
    echo "  -o, --output-dir DIR   Output directory (default: benchmarks/results)"
    echo "  -h, --help             Show this help message"
}

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--type)
            BENCH_TYPE="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            MODEL_NAME="$1"
            shift
            ;;
    esac
done

if [ -z "$MODEL_NAME" ]; then
    echo "Error: MODEL_NAME is required"
    usage
    exit 1
fi

echo -e "${BLUE}Running benchmarks for: $MODEL_NAME${NC}"
echo ""

mkdir -p "$OUTPUT_DIR"

python3 - <<EOF
import sys
sys.path.insert(0, '.')

from agent8.benchmarks import CompressionBenchmark, PerformanceBenchmark, AccuracyBenchmark

bench_type = "$BENCH_TYPE"
model_name = "$MODEL_NAME"
output_dir = "$OUTPUT_DIR"

if bench_type in ["compression", "all"]:
    print("\n" + "="*60)
    print("COMPRESSION BENCHMARK")
    print("="*60)
    comp_bench = CompressionBenchmark(output_dir=output_dir)
    comp_bench.run(model_name)

if bench_type in ["performance", "all"]:
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK")
    print("="*60)
    perf_bench = PerformanceBenchmark(output_dir=output_dir)
    perf_bench.run(model_name)

if bench_type in ["accuracy", "all"]:
    print("\n" + "="*60)
    print("ACCURACY BENCHMARK")
    print("="*60)
    acc_bench = AccuracyBenchmark(output_dir=output_dir)
    acc_bench.run(model_name)

print("\n" + "="*60)
print("ALL BENCHMARKS COMPLETE")
print("="*60)
EOF

echo ""
echo -e "${GREEN}✓ Benchmarks completed!${NC}"
echo -e "${GREEN}  Results saved to: $OUTPUT_DIR${NC}"
