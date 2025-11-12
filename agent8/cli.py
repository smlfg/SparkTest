"""
Command-line interface for Agent 8
"""

import argparse
import json
import sys
from pathlib import Path


def quantize_cli():
    """CLI for model quantization"""
    parser = argparse.ArgumentParser(description="Quantize models to FP4")
    parser.add_argument("model_name", help="Name of the model to quantize")
    parser.add_argument("-m", "--model-path", help="Path to original model")
    parser.add_argument("-o", "--output-path", help="Output path for quantized model")
    parser.add_argument("-p", "--precision", default="fp4", choices=["fp4", "nf4", "int4"])
    parser.add_argument("-d", "--device", default="cuda", choices=["cuda", "cpu"])

    args = parser.parse_args()

    from agent8_quant_api import QuantizationEngine

    engine = QuantizationEngine(precision=args.precision, device=args.device)
    result = engine.quantize(
        model_name=args.model_name,
        model_path=args.model_path,
        output_path=args.output_path
    )

    print(f"\n✓ Quantization complete: {result['quantized_name']}")
    print(f"  Compression: {result['compression_ratio']:.2f}x")
    print(f"  Size reduction: {result['memory_reduction_gb']:.2f} GB")


def inference_cli():
    """CLI for multi-modal inference"""
    parser = argparse.ArgumentParser(description="Run multi-modal inference")
    parser.add_argument("model_name", help="Name of the model")
    parser.add_argument("-t", "--text", help="Text input")
    parser.add_argument("-i", "--image", help="Image path or URL")
    parser.add_argument("-q", "--quantized", action="store_true", default=True)
    parser.add_argument("-o", "--output", help="Output file for results")

    args = parser.parse_args()

    if not args.text and not args.image:
        print("Error: At least one of --text or --image is required")
        sys.exit(1)

    from agent8_quant_api import MultiModalInference

    inference = MultiModalInference(args.model_name, quantized=args.quantized)
    result = inference.infer(text=args.text, image=args.image)

    print(f"\n✓ Inference complete")
    print(f"  Mode: {result['mode']}")
    print(f"  Output: {result['output']}")
    print(f"  Time: {result['inference_time']:.3f}s")

    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2)
        print(f"  Results saved to: {args.output}")


def benchmark_cli():
    """CLI for benchmarking"""
    parser = argparse.ArgumentParser(description="Benchmark quantized models")
    parser.add_argument("model_name", help="Name of the model")
    parser.add_argument("-t", "--type", default="all",
                       choices=["compression", "performance", "accuracy", "all"])
    parser.add_argument("-o", "--output-dir", default="benchmarks/results")

    args = parser.parse_args()

    from agent8.benchmarks import CompressionBenchmark, PerformanceBenchmark, AccuracyBenchmark

    if args.type in ["compression", "all"]:
        bench = CompressionBenchmark(output_dir=args.output_dir)
        bench.run(args.model_name)

    if args.type in ["performance", "all"]:
        bench = PerformanceBenchmark(output_dir=args.output_dir)
        bench.run(args.model_name)

    if args.type in ["accuracy", "all"]:
        bench = AccuracyBenchmark(output_dir=args.output_dir)
        bench.run(args.model_name)

    print(f"\n✓ Benchmarks complete. Results in: {args.output_dir}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "quantize":
            quantize_cli()
        elif sys.argv[1] == "infer":
            inference_cli()
        elif sys.argv[1] == "benchmark":
            benchmark_cli()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            sys.exit(1)
