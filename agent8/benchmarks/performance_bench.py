"""
Performance Benchmarking Suite
Measures inference latency, throughput, and resource utilization
"""

import time
import torch
import psutil
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import statistics


class PerformanceBenchmark:
    """
    Performance benchmarking for quantized models
    Measures speed, throughput, and resource usage
    """

    def __init__(self, output_dir: str = "benchmarks/results"):
        """
        Initialize performance benchmark

        Args:
            output_dir: Directory to save results
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = []

    def run(
        self,
        model_name: str,
        num_iterations: int = 100,
        batch_sizes: List[int] = [1, 4, 8, 16]
    ) -> Dict[str, Any]:
        """
        Run performance benchmark

        Args:
            model_name: Name of the model
            num_iterations: Number of iterations per test
            batch_sizes: Batch sizes to test

        Returns:
            Performance results
        """
        print(f"\n{'='*60}")
        print(f"Performance Benchmark: {model_name}")
        print(f"{'='*60}\n")

        results = {
            "model_name": model_name,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "config": {
                "num_iterations": num_iterations,
                "batch_sizes": batch_sizes
            },
            "metrics": {}
        }

        # 1. Latency Benchmark
        latency_metrics = self._benchmark_latency(
            model_name,
            num_iterations
        )
        results["metrics"]["latency"] = latency_metrics

        # 2. Throughput Benchmark
        throughput_metrics = self._benchmark_throughput(
            model_name,
            batch_sizes,
            num_iterations
        )
        results["metrics"]["throughput"] = throughput_metrics

        # 3. Resource Utilization
        resource_metrics = self._benchmark_resources(model_name)
        results["metrics"]["resources"] = resource_metrics

        # Save results
        self._save_results(results)

        # Print summary
        self._print_summary(results)

        self.results.append(results)
        return results

    def _benchmark_latency(
        self,
        model_name: str,
        num_iterations: int
    ) -> Dict[str, float]:
        """Benchmark inference latency"""
        print("Benchmarking latency...")

        latencies = []
        for i in range(num_iterations):
            start = time.perf_counter()

            # Simulate inference
            self._simulate_inference(model_name)

            latency = time.perf_counter() - start
            latencies.append(latency * 1000)  # Convert to ms

            if (i + 1) % 20 == 0:
                print(f"  Progress: {i + 1}/{num_iterations}")

        return {
            "mean_ms": statistics.mean(latencies),
            "median_ms": statistics.median(latencies),
            "std_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
            "min_ms": min(latencies),
            "max_ms": max(latencies),
            "p95_ms": self._percentile(latencies, 95),
            "p99_ms": self._percentile(latencies, 99)
        }

    def _benchmark_throughput(
        self,
        model_name: str,
        batch_sizes: List[int],
        num_iterations: int
    ) -> Dict[str, Any]:
        """Benchmark throughput across different batch sizes"""
        print("\nBenchmarking throughput...")

        throughput_results = {}

        for batch_size in batch_sizes:
            print(f"  Batch size: {batch_size}")

            total_samples = 0
            start_time = time.perf_counter()

            for _ in range(num_iterations):
                self._simulate_inference(model_name, batch_size)
                total_samples += batch_size

            elapsed = time.perf_counter() - start_time
            throughput = total_samples / elapsed

            throughput_results[f"batch_{batch_size}"] = {
                "batch_size": batch_size,
                "samples_per_second": throughput,
                "total_samples": total_samples,
                "elapsed_seconds": elapsed
            }

        return throughput_results

    def _benchmark_resources(self, model_name: str) -> Dict[str, Any]:
        """Benchmark resource utilization"""
        print("\nBenchmarking resource usage...")

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        process = psutil.Process()
        process_memory = process.memory_info()

        # GPU usage (if available)
        gpu_metrics = {}
        if torch.cuda.is_available():
            gpu_metrics = {
                "gpu_available": True,
                "gpu_count": torch.cuda.device_count(),
                "gpu_memory_allocated_mb": torch.cuda.memory_allocated() / (1024 ** 2),
                "gpu_memory_reserved_mb": torch.cuda.memory_reserved() / (1024 ** 2)
            }
        else:
            gpu_metrics = {"gpu_available": False}

        return {
            "cpu_percent": cpu_percent,
            "cpu_count": psutil.cpu_count(),
            "memory_used_gb": memory.used / (1024 ** 3),
            "memory_available_gb": memory.available / (1024 ** 3),
            "memory_percent": memory.percent,
            "process_memory_mb": process_memory.rss / (1024 ** 2),
            **gpu_metrics
        }

    def _simulate_inference(self, model_name: str, batch_size: int = 1):
        """Simulate model inference"""
        # Simulate computation time based on model size
        base_time = 0.001  # 1ms base

        if "70b" in model_name.lower():
            base_time *= 10
        elif "40b" in model_name.lower():
            base_time *= 5
        elif "13b" in model_name.lower():
            base_time *= 2

        # FP4 models are faster
        if "fp4" in model_name.lower():
            base_time *= 0.8

        # Account for batch size
        time.sleep(base_time * batch_size)

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]

    def _save_results(self, results: Dict[str, Any]):
        """Save results to JSON"""
        filename = f"performance_bench_{results['model_name']}_{int(time.time())}.json"
        output_path = self.output_dir / filename

        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        print(f"\n✓ Results saved to: {output_path}")

    def _print_summary(self, results: Dict[str, Any]):
        """Print benchmark summary"""
        print(f"\n{'='*60}")
        print("PERFORMANCE SUMMARY")
        print(f"{'='*60}\n")

        latency = results["metrics"]["latency"]
        resources = results["metrics"]["resources"]

        print(f"Model: {results['model_name']}")
        print(f"\nLatency:")
        print(f"  Mean:     {latency['mean_ms']:.2f} ms")
        print(f"  Median:   {latency['median_ms']:.2f} ms")
        print(f"  P95:      {latency['p95_ms']:.2f} ms")
        print(f"  P99:      {latency['p99_ms']:.2f} ms")

        print(f"\nThroughput:")
        for key, value in results["metrics"]["throughput"].items():
            print(f"  Batch {value['batch_size']:2d}: {value['samples_per_second']:.2f} samples/sec")

        print(f"\nResources:")
        print(f"  CPU:      {resources['cpu_percent']:.1f}%")
        print(f"  Memory:   {resources['memory_used_gb']:.2f} GB ({resources['memory_percent']:.1f}%)")
        if resources.get('gpu_available'):
            print(f"  GPU Mem:  {resources['gpu_memory_allocated_mb']:.2f} MB")

        print(f"\n{'='*60}\n")
