"""
Performance tests for inference latency.

Measures:
- p50, p95, p99 latency
- Throughput (tokens/sec)
"""

import pytest
import time
import statistics
from typing import List


class MockInferenceEngine:
    """Mock inference engine for testing."""

    def __init__(self, base_latency_ms=100, tokens_per_sec=50):
        self.base_latency_ms = base_latency_ms
        self.tokens_per_sec = tokens_per_sec
        self.request_count = 0

    def generate(self, prompt: str, max_tokens: int = 100):
        """Simulate text generation."""
        self.request_count += 1

        # Simulate latency with some variance
        import random
        latency_ms = self.base_latency_ms + random.gauss(0, 20)

        # Simulate token generation time
        generation_time_ms = (max_tokens / self.tokens_per_sec) * 1000

        total_time_ms = latency_ms + generation_time_ms

        # Small actual delay for realism
        time.sleep(min(total_time_ms / 1000, 0.1))

        return {
            "text": f"Generated response to: {prompt}",
            "tokens": max_tokens,
            "latency_ms": total_time_ms
        }


def calculate_percentiles(values: List[float]) -> dict:
    """Calculate latency percentiles."""
    if not values:
        return {}

    sorted_values = sorted(values)

    return {
        "p50": statistics.median(sorted_values),
        "p95": sorted_values[int(len(sorted_values) * 0.95)],
        "p99": sorted_values[int(len(sorted_values) * 0.99)],
        "min": min(sorted_values),
        "max": max(sorted_values),
        "mean": statistics.mean(sorted_values),
        "stdev": statistics.stdev(sorted_values) if len(sorted_values) > 1 else 0
    }


class TestInferenceLatency:
    """Test inference latency metrics."""

    def test_single_request_latency(self):
        """Test single request latency."""
        engine = MockInferenceEngine(base_latency_ms=100)

        start = time.time()
        result = engine.generate("Test prompt", max_tokens=50)
        elapsed_ms = (time.time() - start) * 1000

        # Should complete reasonably quickly
        assert elapsed_ms < 5000  # 5 seconds max
        assert "latency_ms" in result

    def test_latency_percentiles(self, performance_thresholds):
        """Test that latency percentiles meet SLA."""
        engine = MockInferenceEngine(base_latency_ms=100)

        # Run 100 requests
        latencies = []
        for i in range(100):
            result = engine.generate(f"Prompt {i}", max_tokens=50)
            latencies.append(result["latency_ms"])

        # Calculate percentiles
        percentiles = calculate_percentiles(latencies)

        # Check against thresholds
        thresholds = performance_thresholds["inference"]
        assert percentiles["p50"] < thresholds["latency_p50"], \
            f"p50 latency {percentiles['p50']:.1f}ms exceeds {thresholds['latency_p50']}ms"
        assert percentiles["p95"] < thresholds["latency_p95"], \
            f"p95 latency {percentiles['p95']:.1f}ms exceeds {thresholds['latency_p95']}ms"

    def test_throughput_measurement(self, performance_thresholds):
        """Test tokens per second throughput."""
        engine = MockInferenceEngine(base_latency_ms=100, tokens_per_sec=60)

        total_tokens = 0
        start_time = time.time()

        # Generate multiple requests
        for i in range(10):
            result = engine.generate(f"Prompt {i}", max_tokens=100)
            total_tokens += result["tokens"]

        elapsed_time = time.time() - start_time

        # Calculate throughput
        throughput = total_tokens / elapsed_time

        thresholds = performance_thresholds["inference"]
        assert throughput > thresholds["throughput"], \
            f"Throughput {throughput:.1f} tok/s is below {thresholds['throughput']} tok/s"

    def test_latency_under_load(self):
        """Test latency remains acceptable under load."""
        engine = MockInferenceEngine(base_latency_ms=100)

        # Baseline latency (single request)
        baseline = engine.generate("Test", max_tokens=50)
        baseline_latency = baseline["latency_ms"]

        # Load test (multiple rapid requests)
        load_latencies = []
        for i in range(50):
            result = engine.generate(f"Load test {i}", max_tokens=50)
            load_latencies.append(result["latency_ms"])

        avg_load_latency = statistics.mean(load_latencies)

        # Latency shouldn't degrade too much under load
        # Allow up to 50% increase
        assert avg_load_latency < baseline_latency * 1.5, \
            "Latency degraded too much under load"

    def test_cold_start_vs_warm_latency(self):
        """Test cold start latency vs warm latency."""
        engine = MockInferenceEngine(base_latency_ms=100)

        # First request (cold start)
        cold_start = engine.generate("First request", max_tokens=50)

        # Subsequent requests (warm)
        warm_latencies = []
        for i in range(10):
            result = engine.generate(f"Warm request {i}", max_tokens=50)
            warm_latencies.append(result["latency_ms"])

        avg_warm_latency = statistics.mean(warm_latencies)

        # Record metrics
        print(f"\nCold start latency: {cold_start['latency_ms']:.1f}ms")
        print(f"Average warm latency: {avg_warm_latency:.1f}ms")


class TestThroughputOptimization:
    """Test throughput optimization techniques."""

    def test_batch_inference_throughput(self):
        """Test that batch inference improves throughput."""

        class BatchInferenceEngine:
            def __init__(self):
                self.base_latency_ms = 100

            def generate_single(self, prompt):
                time.sleep(self.base_latency_ms / 1000)
                return {"text": f"Response to {prompt}"}

            def generate_batch(self, prompts):
                # Batch has overhead but processes multiple at once
                time.sleep((self.base_latency_ms + 20) / 1000)
                return [{"text": f"Response to {p}"} for p in prompts]

        engine = BatchInferenceEngine()

        # Sequential processing
        prompts = [f"Prompt {i}" for i in range(10)]
        start_seq = time.time()
        for prompt in prompts:
            engine.generate_single(prompt)
        time_seq = time.time() - start_seq

        # Batch processing
        start_batch = time.time()
        engine.generate_batch(prompts)
        time_batch = time.time() - start_batch

        # Batch should be much faster
        assert time_batch < time_seq * 0.3, "Batch processing should be much faster"

    def test_concurrent_request_handling(self):
        """Test handling multiple concurrent requests."""
        engine = MockInferenceEngine(base_latency_ms=100)

        # Simulate concurrent requests
        import concurrent.futures

        prompts = [f"Concurrent prompt {i}" for i in range(20)]

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(engine.generate, p, 50) for p in prompts]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        assert len(results) == len(prompts)
        assert engine.request_count == len(prompts)


class TestLatencyMonitoring:
    """Test latency monitoring and alerting."""

    def test_latency_spike_detection(self):
        """Test detection of latency spikes."""

        class LatencyMonitor:
            def __init__(self, threshold_ms=1000, window_size=10):
                self.threshold = threshold_ms
                self.window_size = window_size
                self.recent_latencies = []

            def record_latency(self, latency_ms):
                self.recent_latencies.append(latency_ms)
                if len(self.recent_latencies) > self.window_size:
                    self.recent_latencies.pop(0)

            def detect_spike(self):
                if len(self.recent_latencies) < self.window_size:
                    return False

                avg_latency = statistics.mean(self.recent_latencies)
                return avg_latency > self.threshold

        monitor = LatencyMonitor(threshold_ms=500, window_size=5)

        # Normal latencies
        for i in range(5):
            monitor.record_latency(200)

        assert not monitor.detect_spike()

        # Add spike
        for i in range(5):
            monitor.record_latency(800)

        assert monitor.detect_spike()

    def test_latency_trend_analysis(self):
        """Test analyzing latency trends over time."""

        class TrendAnalyzer:
            def __init__(self):
                self.latencies = []

            def record(self, latency_ms, timestamp):
                self.latencies.append((timestamp, latency_ms))

            def get_trend(self):
                """Simple trend: compare first half to second half."""
                if len(self.latencies) < 10:
                    return "insufficient_data"

                mid = len(self.latencies) // 2
                first_half = [lat for _, lat in self.latencies[:mid]]
                second_half = [lat for _, lat in self.latencies[mid:]]

                avg_first = statistics.mean(first_half)
                avg_second = statistics.mean(second_half)

                if avg_second > avg_first * 1.2:
                    return "degrading"
                elif avg_second < avg_first * 0.8:
                    return "improving"
                else:
                    return "stable"

        analyzer = TrendAnalyzer()

        # Stable latencies
        for i in range(20):
            analyzer.record(200, time.time())

        assert analyzer.get_trend() == "stable"

        # Degrading latencies
        analyzer2 = TrendAnalyzer()
        for i in range(10):
            analyzer2.record(200, time.time())
        for i in range(10):
            analyzer2.record(400, time.time())

        assert analyzer2.get_trend() == "degrading"
