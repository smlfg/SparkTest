"""
Agent 8 Quick Start Examples
Demonstrates key features of the model optimization system
"""

from agent8_quant_api import (
    QUANTIZED_MODELS,
    QuantizationEngine,
    MultiModalInference,
    get_quantization_config,
    quantize_model
)


def example_1_quantize_model():
    """Example 1: Quantize a model to FP4"""
    print("\n" + "="*60)
    print("Example 1: Quantize Model to FP4")
    print("="*60 + "\n")

    # Initialize quantization engine
    engine = QuantizationEngine(precision="fp4")

    # Quantize Llama 70B
    result = engine.quantize(
        model_name="llama-70b",
        output_path="models/llama-70b-fp4"
    )

    print(f"\nQuantization Summary:")
    print(f"  Original size: {result['original_size_gb']:.2f} GB")
    print(f"  Quantized size: {result['quantized_size_gb']:.2f} GB")
    print(f"  Compression ratio: {result['compression_ratio']:.2f}x")


def example_2_multimodal_inference():
    """Example 2: Multi-modal inference with text and image"""
    print("\n" + "="*60)
    print("Example 2: Multi-Modal Inference")
    print("="*60 + "\n")

    # Initialize inference engine
    inference = MultiModalInference(
        model_name="llama-70b-fp4",
        quantized=True
    )

    # Run text-only inference
    result = inference.infer(
        text="Explain the theory of relativity in simple terms"
    )

    print(f"Text Inference:")
    print(f"  Mode: {result['mode']}")
    print(f"  Output: {result['output']}")
    print(f"  Time: {result['inference_time']:.3f}s")


def example_3_benchmark_models():
    """Example 3: Benchmark quantized models"""
    print("\n" + "="*60)
    print("Example 3: Benchmark Quantized Models")
    print("="*60 + "\n")

    from agent8.benchmarks import CompressionBenchmark

    # Create benchmark
    benchmark = CompressionBenchmark()

    # Compare multiple models
    models = ["llama-70b-fp4", "mistral-7b-fp4"]
    comparison = benchmark.compare_models(models)

    print(f"\nBenchmark Summary:")
    print(f"  Models tested: {comparison['summary']['total_models']}")
    print(f"  Avg compression: {comparison['summary']['avg_compression_ratio']:.2f}x")


def example_4_model_registry():
    """Example 4: Use model registry"""
    print("\n" + "="*60)
    print("Example 4: Model Registry")
    print("="*60 + "\n")

    from agent8.registry import ModelRegistry

    # Initialize registry
    registry = ModelRegistry()

    # List all models
    models = registry.list_all()
    print(f"Registered models: {len(models)}")

    # Get statistics
    stats = registry.get_statistics()
    print(f"\nRegistry Statistics:")
    print(f"  Total models: {stats['total_models']}")
    print(f"  Total savings: {stats.get('total_savings_gb', 0):.2f} GB")


def example_5_batch_inference():
    """Example 5: Batch inference"""
    print("\n" + "="*60)
    print("Example 5: Batch Inference")
    print("="*60 + "\n")

    # Initialize inference engine
    inference = MultiModalInference("mistral-7b-fp4")

    # Prepare batch inputs
    inputs = [
        {"text": "What is machine learning?"},
        {"text": "Explain neural networks"},
        {"text": "What is deep learning?"}
    ]

    # Run batch inference
    results = inference.batch_infer(inputs, batch_size=3)

    print(f"Batch Inference Results:")
    for i, result in enumerate(results):
        print(f"  Sample {i+1}: {result['output'][:50]}...")


def example_6_configuration():
    """Example 6: Get quantization configurations"""
    print("\n" + "="*60)
    print("Example 6: Quantization Configurations")
    print("="*60 + "\n")

    # Get FP4 config
    fp4_config = get_quantization_config("fp4")
    print(f"FP4 Configuration:")
    print(f"  Bits: {fp4_config['bits']}")
    print(f"  Compression ratio: {fp4_config['compression_ratio']:.2f}x")
    print(f"  Recommended for: {', '.join(fp4_config['recommended_for'])}")

    # Get NF4 config
    nf4_config = get_quantization_config("nf4")
    print(f"\nNF4 Configuration:")
    print(f"  Bits: {nf4_config['bits']}")
    print(f"  Compute dtype: {nf4_config['compute_dtype']}")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("AGENT 8: MODEL OPTIMIZATION - QUICK START")
    print("="*60)

    print(f"\nAvailable FP4 Models: {QUANTIZED_MODELS['fp4_models']}")
    print(f"Quantization Script: {QUANTIZED_MODELS['quant_script']}")

    # Run examples
    example_1_quantize_model()
    example_2_multimodal_inference()
    example_3_benchmark_models()
    example_4_model_registry()
    example_5_batch_inference()
    example_6_configuration()

    print("\n" + "="*60)
    print("All examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
