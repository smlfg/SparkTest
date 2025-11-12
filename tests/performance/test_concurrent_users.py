"""
Performance tests for concurrent users.

Tests system behavior with multiple simultaneous users.
"""

import pytest
import time
import threading
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict


class MockSystemResources:
    """Mock system resources with limits."""

    def __init__(self, max_concurrent=10, gpu_memory_gb=80):
        self.max_concurrent = max_concurrent
        self.total_gpu_memory = gpu_memory_gb * 1024  # MB
        self.used_gpu_memory = 0
        self.active_requests = 0
        self.lock = threading.Lock()
        self.request_queue = []

    def acquire_resources(self, memory_needed_mb=1000):
        """Try to acquire resources for a request."""
        with self.lock:
            if (self.active_requests < self.max_concurrent and
                self.used_gpu_memory + memory_needed_mb <= self.total_gpu_memory):
                self.active_requests += 1
                self.used_gpu_memory += memory_needed_mb
                return True
            return False

    def release_resources(self, memory_mb=1000):
        """Release resources after request completes."""
        with self.lock:
            self.active_requests = max(0, self.active_requests - 1)
            self.used_gpu_memory = max(0, self.used_gpu_memory - memory_mb)

    def get_stats(self):
        """Get current resource stats."""
        with self.lock:
            return {
                "active_requests": self.active_requests,
                "used_memory_mb": self.used_gpu_memory,
                "memory_utilization": self.used_gpu_memory / self.total_gpu_memory
            }


class TestConcurrentUsers:
    """Test system with concurrent users."""

    def test_5_concurrent_users(self):
        """Test system with 5 concurrent users."""
        resources = MockSystemResources(max_concurrent=10)

        def user_workflow(user_id):
            """Simulate a user workflow."""
            results = []

            # Acquire resources
            if resources.acquire_resources(memory_needed_mb=5000):
                try:
                    # Simulate work
                    start = time.time()
                    time.sleep(0.1)  # Simulate inference/training
                    elapsed = time.time() - start

                    results.append({
                        "user_id": user_id,
                        "status": "success",
                        "latency": elapsed
                    })
                finally:
                    resources.release_resources(memory_mb=5000)
            else:
                results.append({
                    "user_id": user_id,
                    "status": "resource_unavailable"
                })

            return results

        # Run 5 concurrent users
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(user_workflow, i) for i in range(5)]
            results = [f.result() for f in as_completed(futures)]

        # All should succeed
        all_results = [r for res_list in results for r in res_list]
        successful = [r for r in all_results if r["status"] == "success"]

        assert len(successful) == 5, "All 5 users should succeed"

    def test_10_concurrent_users(self):
        """Test system with 10 concurrent users."""
        resources = MockSystemResources(max_concurrent=10)

        def user_request(user_id):
            """Single user request."""
            if resources.acquire_resources(memory_needed_mb=4000):
                try:
                    time.sleep(0.05)
                    return {"user_id": user_id, "status": "success"}
                finally:
                    resources.release_resources(memory_mb=4000)
            else:
                return {"user_id": user_id, "status": "queued"}

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(user_request, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        successful = [r for r in results if r["status"] == "success"]
        assert len(successful) >= 8, "At least 8 of 10 users should succeed"

    def test_20_concurrent_users(self):
        """Test system with 20 concurrent users (stress test)."""
        resources = MockSystemResources(max_concurrent=10)

        def user_request(user_id):
            """User request with retry logic."""
            max_retries = 3
            for attempt in range(max_retries):
                if resources.acquire_resources(memory_needed_mb=3000):
                    try:
                        time.sleep(0.02)
                        return {
                            "user_id": user_id,
                            "status": "success",
                            "attempts": attempt + 1
                        }
                    finally:
                        resources.release_resources(memory_mb=3000)
                time.sleep(0.01)  # Wait before retry

            return {"user_id": user_id, "status": "failed", "attempts": max_retries}

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(user_request, i) for i in range(20)]
            results = [f.result() for f in as_completed(futures)]

        successful = [r for r in results if r["status"] == "success"]
        failed = [r for r in results if r["status"] == "failed"]

        # At least 15/20 should eventually succeed
        assert len(successful) >= 15, \
            f"Only {len(successful)}/20 users succeeded"

        print(f"\n20 concurrent users: {len(successful)} success, {len(failed)} failed")


class TestConcurrentWorkflows:
    """Test concurrent user workflows."""

    def test_concurrent_training_jobs(self):
        """Test multiple concurrent training jobs."""
        resources = MockSystemResources(max_concurrent=3, gpu_memory_gb=80)

        def training_job(job_id):
            """Simulate training job."""
            # Training needs more memory
            memory_needed = 20000  # 20GB per job

            acquired = resources.acquire_resources(memory_needed)
            if not acquired:
                return {"job_id": job_id, "status": "resource_unavailable"}

            try:
                start = time.time()
                time.sleep(0.1)  # Simulate training
                elapsed = time.time() - start

                return {
                    "job_id": job_id,
                    "status": "completed",
                    "duration": elapsed
                }
            finally:
                resources.release_resources(memory_needed)

        # Start 3 concurrent training jobs (should fit)
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(training_job, i) for i in range(3)]
            results = [f.result() for f in as_completed(futures)]

        completed = [r for r in results if r["status"] == "completed"]
        assert len(completed) == 3, "All 3 training jobs should complete"

    def test_mixed_workload(self):
        """Test mixed inference and training workload."""
        resources = MockSystemResources(max_concurrent=10, gpu_memory_gb=80)

        def inference_request(req_id):
            """Light inference request."""
            if resources.acquire_resources(memory_needed_mb=1000):
                try:
                    time.sleep(0.02)
                    return {"id": req_id, "type": "inference", "status": "success"}
                finally:
                    resources.release_resources(memory_mb=1000)
            return {"id": req_id, "type": "inference", "status": "queued"}

        def training_job(job_id):
            """Heavy training job."""
            if resources.acquire_resources(memory_needed_mb=15000):
                try:
                    time.sleep(0.1)
                    return {"id": job_id, "type": "training", "status": "success"}
                finally:
                    resources.release_resources(memory_mb=15000)
            return {"id": job_id, "type": "training", "status": "queued"}

        with ThreadPoolExecutor(max_workers=15) as executor:
            # Submit mixed workload
            futures = []

            # 2 training jobs
            for i in range(2):
                futures.append(executor.submit(training_job, f"train_{i}"))

            # 10 inference requests
            for i in range(10):
                futures.append(executor.submit(inference_request, f"infer_{i}"))

            results = [f.result() for f in as_completed(futures)]

        # Analyze results
        training_success = [r for r in results if r["type"] == "training" and r["status"] == "success"]
        inference_success = [r for r in results if r["type"] == "inference" and r["status"] == "success"]

        print(f"\nMixed workload: {len(training_success)} training, {len(inference_success)} inference")

        # Most should succeed
        assert len(training_success) >= 1
        assert len(inference_success) >= 8

    def test_user_fairness(self):
        """Test that system is fair to all users under load."""
        resources = MockSystemResources(max_concurrent=5)

        user_latencies = {i: [] for i in range(10)}

        def user_request(user_id, request_num):
            """User request tracking latency."""
            start = time.time()

            # Try to acquire resources
            acquired = False
            while not acquired and (time.time() - start) < 1.0:  # 1s timeout
                acquired = resources.acquire_resources(memory_needed_mb=5000)
                if not acquired:
                    time.sleep(0.01)

            if acquired:
                try:
                    time.sleep(0.05)  # Work
                    total_latency = time.time() - start
                    return {"user_id": user_id, "latency": total_latency, "status": "success"}
                finally:
                    resources.release_resources(memory_mb=5000)
            else:
                return {"user_id": user_id, "status": "timeout"}

        # Each user makes 5 requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            for user_id in range(10):
                for req_num in range(5):
                    futures.append(executor.submit(user_request, user_id, req_num))

            results = [f.result() for f in as_completed(futures)]

        # Group by user
        for result in results:
            if result["status"] == "success":
                user_latencies[result["user_id"]].append(result["latency"])

        # Calculate average latency per user
        avg_latencies = {
            user_id: statistics.mean(latencies) if latencies else float('inf')
            for user_id, latencies in user_latencies.items()
        }

        # Check fairness - no user should have drastically worse latency
        if len([l for l in avg_latencies.values() if l < float('inf')]) > 1:
            min_avg = min(l for l in avg_latencies.values() if l < float('inf'))
            max_avg = max(l for l in avg_latencies.values() if l < float('inf'))

            # Max shouldn't be more than 3x min (reasonable fairness)
            assert max_avg < min_avg * 3, "System is unfair to some users"


class TestLoadCharacteristics:
    """Test system behavior under different load patterns."""

    def test_gradual_ramp_up(self):
        """Test gradual increase in concurrent users."""
        resources = MockSystemResources(max_concurrent=20)

        def user_request(user_id):
            if resources.acquire_resources(memory_needed_mb=2000):
                try:
                    time.sleep(0.02)
                    return {"user_id": user_id, "status": "success"}
                finally:
                    resources.release_resources(memory_mb=2000)
            return {"user_id": user_id, "status": "rejected"}

        # Ramp up from 5 to 20 users
        user_counts = [5, 10, 15, 20]
        results_by_load = {}

        for user_count in user_counts:
            with ThreadPoolExecutor(max_workers=user_count) as executor:
                futures = [executor.submit(user_request, i) for i in range(user_count)]
                results = [f.result() for f in as_completed(futures)]

            successful = len([r for r in results if r["status"] == "success"])
            results_by_load[user_count] = {
                "total": user_count,
                "successful": successful,
                "success_rate": successful / user_count
            }

        print("\nRamp up results:")
        for load, stats in results_by_load.items():
            print(f"  {load} users: {stats['successful']}/{stats['total']} success ({stats['success_rate']:.1%})")

    def test_spike_load(self):
        """Test sudden spike in load."""
        resources = MockSystemResources(max_concurrent=10)

        def user_request(user_id):
            if resources.acquire_resources(memory_needed_mb=3000):
                try:
                    time.sleep(0.05)
                    return {"user_id": user_id, "status": "success"}
                finally:
                    resources.release_resources(memory_mb=3000)
            return {"user_id": user_id, "status": "rejected"}

        # Sudden spike to 50 users
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(user_request, i) for i in range(50)]
            results = [f.result() for f in as_completed(futures)]

        successful = [r for r in results if r["status"] == "success"]
        rejected = [r for r in results if r["status"] == "rejected"]

        # System should handle gracefully (not crash)
        assert len(results) == 50
        # At least some should succeed
        assert len(successful) >= 10

        print(f"\nSpike test: {len(successful)}/50 succeeded, {len(rejected)} rejected")

    def test_sustained_load(self):
        """Test sustained high load over time."""
        resources = MockSystemResources(max_concurrent=10)

        def continuous_user(user_id, duration_sec=0.5):
            """User making continuous requests."""
            results = []
            start_time = time.time()

            while time.time() - start_time < duration_sec:
                if resources.acquire_resources(memory_needed_mb=2000):
                    try:
                        time.sleep(0.02)
                        results.append({"status": "success"})
                    finally:
                        resources.release_resources(memory_mb=2000)
                else:
                    results.append({"status": "throttled"})
                    time.sleep(0.01)

            return results

        # 15 users making continuous requests
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(continuous_user, i, 0.3) for i in range(15)]
            all_results = [f.result() for f in as_completed(futures)]

        # Flatten results
        total_requests = sum(len(r) for r in all_results)
        successful_requests = sum(len([x for x in r if x["status"] == "success"]) for r in all_results)

        success_rate = successful_requests / total_requests if total_requests > 0 else 0

        print(f"\nSustained load: {successful_requests}/{total_requests} ({success_rate:.1%})")

        # Should maintain reasonable success rate under sustained load
        assert success_rate > 0.6, "Success rate too low under sustained load"
