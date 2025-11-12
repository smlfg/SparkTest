"""
Inference Engine Benchmark Suite
Comprehensive benchmarking for vLLM, TRT-LLM, and Speculative Decoding
"""

import time
import json
import statistics
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BenchmarkMetric(Enum):
    """Benchmark metrics"""
    LATENCY = "latency"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    TOKEN_GENERATION_RATE = "token_generation_rate"
    TIME_TO_FIRST_TOKEN = "time_to_first_token"
    BATCH_PROCESSING = "batch_processing"


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark runs"""

    # Test parameters
    num_runs: int = 10
    warmup_runs: int = 3
    batch_sizes: List[int] = field(default_factory=lambda: [1, 4, 8, 16, 32])
    sequence_lengths: List[int] = field(default_factory=lambda: [128, 512, 1024, 2048])

    # Generation parameters
    max_tokens: int = 128
    temperature: float = 0.7
    top_k: int = 50
    top_p: float = 0.9

    # Test prompts
    test_prompts: Optional[List[str]] = None

    # Output
    output_file: str = "benchmarks/results/benchmark_results.json"
    save_detailed_logs: bool = True

    def __post_init__(self):
        if self.test_prompts is None:
            self.test_prompts = self._default_prompts()

    @staticmethod
    def _default_prompts() -> List[str]:
        """Default test prompts"""
        return [
            "Explain quantum computing in simple terms.",
            "Write a Python function to implement quicksort.",
            "Describe the process of photosynthesis.",
            "What are the main causes of climate change?",
            "Explain the theory of relativity.",
        ]


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run"""

    backend: str
    batch_size: int
    sequence_length: int
    num_tokens_generated: int

    # Latency metrics (milliseconds)
    mean_latency: float
    median_latency: float
    p95_latency: float
    p99_latency: float
    min_latency: float
    max_latency: float

    # Throughput metrics
    tokens_per_second: float
    requests_per_second: float

    # Memory metrics (GB)
    peak_memory_usage: float
    average_memory_usage: float

    # Additional metrics
    time_to_first_token: float  # milliseconds
    inter_token_latency: float  # milliseconds

    # Metadata
    timestamp: str
    config: Dict[str, Any] = field(default_factory=dict)


class LatencyTracker:
    """Track latency statistics"""

    def __init__(self):
        self.latencies: List[float] = []

    def record(self, latency_ms: float):
        """Record a latency measurement"""
        self.latencies.append(latency_ms)

    def get_statistics(self) -> Dict[str, float]:
        """Calculate latency statistics"""
        if not self.latencies:
            return {
                "mean": 0.0,
                "median": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "min": 0.0,
                "max": 0.0
            }

        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)

        return {
            "mean": statistics.mean(self.latencies),
            "median": statistics.median(self.latencies),
            "p95": sorted_latencies[int(n * 0.95)] if n > 0 else 0.0,
            "p99": sorted_latencies[int(n * 0.99)] if n > 0 else 0.0,
            "min": min(self.latencies),
            "max": max(self.latencies)
        }

    def reset(self):
        """Reset tracked latencies"""
        self.latencies = []


class InferenceBenchmark:
    """Benchmark harness for inference engines"""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results: List[BenchmarkResult] = []
        logger.info("Inference Benchmark initialized")

    def benchmark_latency(
        self,
        inference_fn: Callable,
        prompt: str,
        backend_name: str,
        batch_size: int = 1,
        sequence_length: int = 128
    ) -> BenchmarkResult:
        """
        Benchmark latency for an inference function

        Args:
            inference_fn: Function to benchmark
            prompt: Test prompt
            backend_name: Name of the backend
            batch_size: Batch size
            sequence_length: Sequence length

        Returns:
            Benchmark results
        """
        logger.info(f"Benchmarking {backend_name} - Batch: {batch_size}, SeqLen: {sequence_length}")

        tracker = LatencyTracker()
        total_tokens = 0
        total_time = 0.0
        ttft_list = []  # Time to first token
        memory_samples = []

        # Warmup
        logger.debug(f"Running {self.config.warmup_runs} warmup iterations...")
        for _ in range(self.config.warmup_runs):
            inference_fn(prompt)

        # Actual benchmark runs
        logger.debug(f"Running {self.config.num_runs} benchmark iterations...")
        for run in range(self.config.num_runs):
            start_time = time.time()

            # Simulate inference
            result = inference_fn(prompt)

            end_time = time.time()
            latency_ms = (end_time - start_time) * 1000

            tracker.record(latency_ms)
            total_time += (end_time - start_time)
            total_tokens += self.config.max_tokens

            # Simulate TTFT and memory (in real implementation, measure actual values)
            ttft_list.append(latency_ms * 0.1)  # Assume 10% of total latency
            memory_samples.append(self._simulate_memory_usage(backend_name))

        # Calculate statistics
        stats = tracker.get_statistics()

        # Create result
        result = BenchmarkResult(
            backend=backend_name,
            batch_size=batch_size,
            sequence_length=sequence_length,
            num_tokens_generated=total_tokens,
            mean_latency=stats["mean"],
            median_latency=stats["median"],
            p95_latency=stats["p95"],
            p99_latency=stats["p99"],
            min_latency=stats["min"],
            max_latency=stats["max"],
            tokens_per_second=total_tokens / total_time if total_time > 0 else 0,
            requests_per_second=self.config.num_runs / total_time if total_time > 0 else 0,
            peak_memory_usage=max(memory_samples) if memory_samples else 0.0,
            average_memory_usage=statistics.mean(memory_samples) if memory_samples else 0.0,
            time_to_first_token=statistics.mean(ttft_list) if ttft_list else 0.0,
            inter_token_latency=stats["mean"] / self.config.max_tokens,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            config=asdict(self.config)
        )

        self.results.append(result)
        return result

    def benchmark_throughput(
        self,
        inference_fn: Callable,
        prompts: List[str],
        backend_name: str,
        batch_size: int = 1
    ) -> Dict[str, float]:
        """
        Benchmark throughput for batch processing

        Args:
            inference_fn: Inference function
            prompts: List of prompts
            backend_name: Backend name
            batch_size: Batch size

        Returns:
            Throughput metrics
        """
        logger.info(f"Benchmarking throughput for {backend_name} (batch_size={batch_size})")

        # Process in batches
        num_batches = len(prompts) // batch_size
        total_tokens = 0
        start_time = time.time()

        for i in range(num_batches):
            batch = prompts[i * batch_size:(i + 1) * batch_size]
            for prompt in batch:
                inference_fn(prompt)
            total_tokens += batch_size * self.config.max_tokens

        end_time = time.time()
        total_time = end_time - start_time

        return {
            "total_tokens": total_tokens,
            "total_time_seconds": total_time,
            "throughput_tokens_per_second": total_tokens / total_time if total_time > 0 else 0,
            "throughput_requests_per_second": len(prompts) / total_time if total_time > 0 else 0
        }

    def benchmark_memory(
        self,
        inference_fn: Callable,
        prompt: str,
        backend_name: str
    ) -> Dict[str, float]:
        """
        Benchmark memory usage

        Args:
            inference_fn: Inference function
            prompt: Test prompt
            backend_name: Backend name

        Returns:
            Memory metrics
        """
        logger.info(f"Benchmarking memory for {backend_name}")

        # In real implementation, would use nvidia-ml-py or similar
        memory_samples = []

        for _ in range(self.config.num_runs):
            # Sample memory before
            mem_before = self._simulate_memory_usage(backend_name)

            # Run inference
            inference_fn(prompt)

            # Sample memory after
            mem_after = self._simulate_memory_usage(backend_name)
            memory_samples.append(mem_after - mem_before)

        return {
            "mean_memory_gb": statistics.mean(memory_samples),
            "peak_memory_gb": max(memory_samples),
            "min_memory_gb": min(memory_samples)
        }

    def _simulate_memory_usage(self, backend_name: str) -> float:
        """Simulate memory usage (placeholder for actual measurement)"""
        # In real implementation, would query GPU memory
        base_memory = {
            "vllm": 8.5,
            "trt_llm": 7.2,
            "speculative": 9.8
        }
        return base_memory.get(backend_name, 8.0)

    def run_comprehensive_benchmark(
        self,
        backends: Dict[str, Callable]
    ) -> Dict[str, List[BenchmarkResult]]:
        """
        Run comprehensive benchmark across all backends

        Args:
            backends: Dictionary mapping backend names to inference functions

        Returns:
            Dictionary of results per backend
        """
        logger.info("=" * 70)
        logger.info("Running Comprehensive Benchmark")
        logger.info("=" * 70)

        all_results = {name: [] for name in backends.keys()}

        # Test each backend
        for backend_name, inference_fn in backends.items():
            logger.info(f"\nBenchmarking: {backend_name}")
            logger.info("-" * 70)

            # Test different batch sizes and sequence lengths
            for batch_size in self.config.batch_sizes:
                for seq_len in self.config.sequence_lengths:
                    prompt = self.config.test_prompts[0]

                    result = self.benchmark_latency(
                        inference_fn,
                        prompt,
                        backend_name,
                        batch_size,
                        seq_len
                    )

                    all_results[backend_name].append(result)

                    logger.info(
                        f"  Batch: {batch_size}, SeqLen: {seq_len} - "
                        f"Latency: {result.mean_latency:.2f}ms, "
                        f"Throughput: {result.tokens_per_second:.1f} tok/s"
                    )

        return all_results

    def compare_backends(
        self,
        results: Dict[str, List[BenchmarkResult]]
    ) -> Dict[str, Any]:
        """
        Compare performance across backends

        Args:
            results: Results from comprehensive benchmark

        Returns:
            Comparison analysis
        """
        comparison = {}

        # Average metrics per backend
        for backend_name, backend_results in results.items():
            if not backend_results:
                continue

            comparison[backend_name] = {
                "mean_latency": statistics.mean([r.mean_latency for r in backend_results]),
                "median_latency": statistics.median([r.median_latency for r in backend_results]),
                "mean_throughput": statistics.mean([r.tokens_per_second for r in backend_results]),
                "peak_memory": max([r.peak_memory_usage for r in backend_results]),
                "mean_ttft": statistics.mean([r.time_to_first_token for r in backend_results])
            }

        # Find best performing backend for each metric
        if comparison:
            comparison["best_latency"] = min(comparison.items(), key=lambda x: x[1]["mean_latency"])[0]
            comparison["best_throughput"] = max(comparison.items(), key=lambda x: x[1]["mean_throughput"])[0]
            comparison["lowest_memory"] = min(comparison.items(), key=lambda x: x[1]["peak_memory"])[0]

        return comparison

    def save_results(self, filepath: Optional[str] = None):
        """Save benchmark results to file"""
        import os

        filepath = filepath or self.config.output_file
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        results_data = {
            "benchmark_config": asdict(self.config),
            "results": [asdict(r) for r in self.results],
            "summary": self._generate_summary()
        }

        with open(filepath, 'w') as f:
            json.dump(results_data, f, indent=2)

        logger.info(f"Results saved to: {filepath}")

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        if not self.results:
            return {}

        # Group by backend
        backend_results = {}
        for result in self.results:
            if result.backend not in backend_results:
                backend_results[result.backend] = []
            backend_results[result.backend].append(result)

        summary = {}
        for backend, results in backend_results.items():
            summary[backend] = {
                "num_runs": len(results),
                "avg_latency_ms": statistics.mean([r.mean_latency for r in results]),
                "avg_throughput_tps": statistics.mean([r.tokens_per_second for r in results]),
                "peak_memory_gb": max([r.peak_memory_usage for r in results])
            }

        return summary

    def print_summary(self):
        """Print benchmark summary"""
        summary = self._generate_summary()

        print("\n" + "=" * 70)
        print("Benchmark Summary")
        print("=" * 70)

        for backend, stats in summary.items():
            print(f"\n{backend}:")
            print(f"  Runs: {stats['num_runs']}")
            print(f"  Avg Latency: {stats['avg_latency_ms']:.2f} ms")
            print(f"  Avg Throughput: {stats['avg_throughput_tps']:.1f} tokens/s")
            print(f"  Peak Memory: {stats['peak_memory_gb']:.2f} GB")


def simulate_vllm_inference(prompt: str) -> Dict[str, Any]:
    """Simulate vLLM inference"""
    time.sleep(0.085)  # Simulate 85ms latency
    return {"text": "Generated text", "tokens": 128}


def simulate_trt_inference(prompt: str) -> Dict[str, Any]:
    """Simulate TRT-LLM inference"""
    time.sleep(0.035)  # Simulate 35ms latency (faster)
    return {"text": "Generated text", "tokens": 128}


def simulate_speculative_inference(prompt: str) -> Dict[str, Any]:
    """Simulate speculative decoding inference"""
    time.sleep(0.045)  # Simulate 45ms latency
    return {"text": "Generated text", "tokens": 128}


def main():
    """Run benchmark suite"""
    print("=" * 70)
    print("Inference Engine Benchmark Suite")
    print("=" * 70)

    # Configuration
    config = BenchmarkConfig(
        num_runs=10,
        warmup_runs=3,
        batch_sizes=[1, 4, 8],
        sequence_lengths=[128, 512, 1024],
        max_tokens=128
    )

    # Create benchmark
    benchmark = InferenceBenchmark(config)

    # Define backends
    backends = {
        "vllm": simulate_vllm_inference,
        "trt_llm": simulate_trt_inference,
        "speculative": simulate_speculative_inference
    }

    # Run comprehensive benchmark
    print("\nRunning comprehensive benchmark...")
    results = benchmark.run_comprehensive_benchmark(backends)

    # Compare backends
    print("\n" + "=" * 70)
    print("Backend Comparison")
    print("=" * 70)
    comparison = benchmark.compare_backends(results)

    for backend, metrics in comparison.items():
        if isinstance(metrics, dict) and "mean_latency" in metrics:
            print(f"\n{backend}:")
            print(f"  Mean Latency: {metrics['mean_latency']:.2f} ms")
            print(f"  Mean Throughput: {metrics['mean_throughput']:.1f} tokens/s")
            print(f"  Peak Memory: {metrics['peak_memory']:.2f} GB")
            print(f"  Mean TTFT: {metrics['mean_ttft']:.2f} ms")

    print("\n" + "=" * 70)
    print("Best Performers:")
    print("=" * 70)
    print(f"  Lowest Latency: {comparison.get('best_latency', 'N/A')}")
    print(f"  Highest Throughput: {comparison.get('best_throughput', 'N/A')}")
    print(f"  Lowest Memory: {comparison.get('lowest_memory', 'N/A')}")

    # Print summary
    benchmark.print_summary()

    # Save results
    benchmark.save_results()

    print("\n" + "=" * 70)
    print("Benchmark completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
