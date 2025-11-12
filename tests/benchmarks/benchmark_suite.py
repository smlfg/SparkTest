"""
Performance Benchmark Suite for SparkTest
Comprehensive benchmarks for all system components
"""

import pytest
import time
from typing import List, Dict, Any
import statistics


class BenchmarkResult:
    """Container for benchmark results"""

    def __init__(self, name: str):
        self.name = name
        self.execution_times: List[float] = []
        self.throughput: List[float] = []
        self.success_count = 0
        self.failure_count = 0

    def add_execution(self, duration: float, success: bool = True):
        self.execution_times.append(duration)
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1

    def add_throughput(self, ops_per_second: float):
        self.throughput.append(ops_per_second)

    def get_stats(self) -> Dict[str, Any]:
        """Calculate statistics"""
        if not self.execution_times:
            return {}

        return {
            "name": self.name,
            "executions": len(self.execution_times),
            "success_rate": self.success_count / len(self.execution_times) * 100,
            "avg_time": statistics.mean(self.execution_times),
            "median_time": statistics.median(self.execution_times),
            "min_time": min(self.execution_times),
            "max_time": max(self.execution_times),
            "std_dev": statistics.stdev(self.execution_times) if len(self.execution_times) > 1 else 0,
            "avg_throughput": statistics.mean(self.throughput) if self.throughput else 0
        }

    def print_stats(self):
        """Print benchmark statistics"""
        stats = self.get_stats()
        print(f"\n{'='*60}")
        print(f"Benchmark: {stats['name']}")
        print(f"{'='*60}")
        print(f"Executions: {stats['executions']}")
        print(f"Success Rate: {stats['success_rate']:.2f}%")
        print(f"Average Time: {stats['avg_time']:.4f}s")
        print(f"Median Time: {stats['median_time']:.4f}s")
        print(f"Min Time: {stats['min_time']:.4f}s")
        print(f"Max Time: {stats['max_time']:.4f}s")
        print(f"Std Deviation: {stats['std_dev']:.4f}s")
        if stats['avg_throughput'] > 0:
            print(f"Avg Throughput: {stats['avg_throughput']:.2f} ops/sec")
        print(f"{'='*60}\n")


@pytest.mark.benchmark
class TestAPIBenchmarks:
    """Benchmark tests for API Gateway"""

    def test_health_check_latency(self, api_client, benchmark):
        """Benchmark health check endpoint latency"""

        def health_check():
            response = api_client.get("/health")
            return response.status_code == 200

        result = benchmark(health_check)
        assert result is True

    def test_job_submission_throughput(self, api_client):
        """Benchmark job submission throughput"""
        result = BenchmarkResult("Job Submission Throughput")

        iterations = 100
        start_time = time.time()

        for i in range(iterations):
            job_start = time.time()
            response = api_client.post("/jobs/submit", json={
                "job_name": f"benchmark_job_{i}",
                "job_type": "benchmark",
                "parameters": {"index": i}
            })
            job_duration = time.time() - job_start

            result.add_execution(job_duration, response.status_code == 200)

        total_duration = time.time() - start_time
        result.add_throughput(iterations / total_duration)

        result.print_stats()

        stats = result.get_stats()
        assert stats["success_rate"] > 95.0
        assert stats["avg_time"] < 0.5

    def test_concurrent_api_requests(self, api_client):
        """Benchmark concurrent API request handling"""
        import concurrent.futures

        result = BenchmarkResult("Concurrent API Requests")

        def make_request(index):
            start = time.time()
            response = api_client.get("/agents")
            duration = time.time() - start
            return duration, response.status_code == 200

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request, i) for i in range(100)]
            results = [f.result() for f in futures]

        total_duration = time.time() - start_time

        for duration, success in results:
            result.add_execution(duration, success)

        result.add_throughput(100 / total_duration)
        result.print_stats()

        stats = result.get_stats()
        assert stats["success_rate"] > 95.0

    def test_list_jobs_performance(self, api_client):
        """Benchmark job listing performance"""
        # First, create some jobs
        for i in range(50):
            api_client.post("/jobs/submit", json={
                "job_name": f"list_test_job_{i}",
                "job_type": "test",
                "parameters": {"index": i}
            })

        result = BenchmarkResult("List Jobs Performance")

        for _ in range(20):
            start = time.time()
            response = api_client.get("/jobs")
            duration = time.time() - start

            result.add_execution(duration, response.status_code == 200)

        result.print_stats()

        stats = result.get_stats()
        assert stats["avg_time"] < 1.0


@pytest.mark.benchmark
class TestSparkBenchmarks:
    """Benchmark tests for Spark operations"""

    def test_dataframe_creation_performance(self, spark_session):
        """Benchmark DataFrame creation performance"""
        result = BenchmarkResult("DataFrame Creation")

        for size in [1000, 5000, 10000]:
            data = [(i, f"value_{i}", i * 2) for i in range(size)]

            start = time.time()
            df = spark_session.createDataFrame(data, ["id", "name", "value"])
            df.count()  # Force evaluation
            duration = time.time() - start

            result.add_execution(duration, True)

        result.print_stats()

        stats = result.get_stats()
        assert stats["avg_time"] < 5.0

    def test_filter_operation_performance(self, spark_session):
        """Benchmark filter operation performance"""
        from pyspark.sql.functions import col

        # Create large dataset
        data = [(i, f"value_{i}", i * 2) for i in range(50000)]
        df = spark_session.createDataFrame(data, ["id", "name", "value"])

        result = BenchmarkResult("Filter Operations")

        for _ in range(10):
            start = time.time()
            filtered = df.filter(col("id") % 2 == 0).count()
            duration = time.time() - start

            result.add_execution(duration, filtered == 25000)

        result.print_stats()

        stats = result.get_stats()
        assert stats["success_rate"] == 100.0

    def test_aggregation_performance(self, spark_session):
        """Benchmark aggregation performance"""
        from pyspark.sql.functions import sum as spark_sum, avg, count

        # Create dataset
        data = [(i % 100, i, i * 2) for i in range(100000)]
        df = spark_session.createDataFrame(data, ["group_id", "id", "value"])

        result = BenchmarkResult("Aggregation Operations")

        for _ in range(5):
            start = time.time()
            aggregated = df.groupBy("group_id").agg(
                spark_sum("value").alias("total"),
                avg("value").alias("average"),
                count("*").alias("count")
            ).count()
            duration = time.time() - start

            result.add_execution(duration, aggregated == 100)

        result.print_stats()

        stats = result.get_stats()
        assert stats["avg_time"] < 10.0

    def test_join_performance(self, spark_session):
        """Benchmark join operation performance"""
        # Create datasets
        data1 = [(i, f"name_{i}") for i in range(10000)]
        data2 = [(i, i * 10) for i in range(10000)]

        df1 = spark_session.createDataFrame(data1, ["id", "name"])
        df2 = spark_session.createDataFrame(data2, ["id", "value"])

        result = BenchmarkResult("Join Operations")

        for _ in range(5):
            start = time.time()
            joined = df1.join(df2, "id", "inner").count()
            duration = time.time() - start

            result.add_execution(duration, joined == 10000)

        result.print_stats()

        stats = result.get_stats()
        assert stats["success_rate"] == 100.0


@pytest.mark.benchmark
class TestRedisBenchmarks:
    """Benchmark tests for Redis operations"""

    def test_redis_set_get_performance(self, redis_client):
        """Benchmark Redis SET/GET operations"""
        result = BenchmarkResult("Redis SET/GET")

        iterations = 1000

        start_time = time.time()
        for i in range(iterations):
            op_start = time.time()
            redis_client.set(f"test:benchmark_{i}", f"value_{i}")
            value = redis_client.get(f"test:benchmark_{i}")
            op_duration = time.time() - op_start

            result.add_execution(op_duration, value == f"value_{i}")

        total_duration = time.time() - start_time
        result.add_throughput(iterations / total_duration)

        result.print_stats()

        stats = result.get_stats()
        assert stats["avg_throughput"] > 100  # ops/sec

    def test_redis_hash_performance(self, redis_client):
        """Benchmark Redis hash operations"""
        result = BenchmarkResult("Redis Hash Operations")

        iterations = 500

        for i in range(iterations):
            start = time.time()
            redis_client.hset(f"test:hash_{i}", mapping={
                "field1": f"value1_{i}",
                "field2": f"value2_{i}",
                "field3": f"value3_{i}"
            })
            data = redis_client.hgetall(f"test:hash_{i}")
            duration = time.time() - start

            result.add_execution(duration, len(data) == 3)

        result.print_stats()

        stats = result.get_stats()
        assert stats["success_rate"] == 100.0

    def test_redis_list_performance(self, redis_client):
        """Benchmark Redis list operations"""
        result = BenchmarkResult("Redis List Operations")

        iterations = 500

        for i in range(iterations):
            key = f"test:list_{i}"

            start = time.time()
            redis_client.lpush(key, *[f"item_{j}" for j in range(10)])
            length = redis_client.llen(key)
            items = redis_client.lrange(key, 0, -1)
            duration = time.time() - start

            result.add_execution(duration, len(items) == 10)

        result.print_stats()


@pytest.mark.benchmark
class TestDatabaseBenchmarks:
    """Benchmark tests for database operations"""

    def test_insert_performance(self, db_connection):
        """Benchmark database insert performance"""
        cursor = db_connection.cursor()

        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_inserts (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                value INTEGER,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        db_connection.commit()

        result = BenchmarkResult("Database Inserts")

        iterations = 100

        for i in range(iterations):
            start = time.time()
            cursor.execute(
                "INSERT INTO benchmark_inserts (name, value) VALUES (%s, %s)",
                (f"name_{i}", i * 10)
            )
            db_connection.commit()
            duration = time.time() - start

            result.add_execution(duration, True)

        result.print_stats()

        # Cleanup
        cursor.execute("DROP TABLE benchmark_inserts")
        db_connection.commit()

        stats = result.get_stats()
        assert stats["avg_time"] < 0.1

    def test_batch_insert_performance(self, db_connection):
        """Benchmark batch insert performance"""
        cursor = db_connection.cursor()

        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_batch (
                id SERIAL PRIMARY KEY,
                value INTEGER
            )
        """)
        db_connection.commit()

        result = BenchmarkResult("Database Batch Inserts")

        batch_sizes = [10, 50, 100]

        for batch_size in batch_sizes:
            data = [(i,) for i in range(batch_size)]

            start = time.time()
            cursor.executemany("INSERT INTO benchmark_batch (value) VALUES (%s)", data)
            db_connection.commit()
            duration = time.time() - start

            result.add_execution(duration, True)
            result.add_throughput(batch_size / duration)

        result.print_stats()

        # Cleanup
        cursor.execute("DROP TABLE benchmark_batch")
        db_connection.commit()

    def test_query_performance(self, db_connection):
        """Benchmark query performance"""
        cursor = db_connection.cursor()

        # Create and populate test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS benchmark_queries (
                id SERIAL PRIMARY KEY,
                category VARCHAR(50),
                value INTEGER
            )
        """)

        # Insert test data
        data = [(f"category_{i % 10}", i * 10) for i in range(1000)]
        cursor.executemany(
            "INSERT INTO benchmark_queries (category, value) VALUES (%s, %s)",
            data
        )
        db_connection.commit()

        result = BenchmarkResult("Database Queries")

        for _ in range(20):
            start = time.time()
            cursor.execute("""
                SELECT category, COUNT(*), AVG(value)
                FROM benchmark_queries
                GROUP BY category
            """)
            results = cursor.fetchall()
            duration = time.time() - start

            result.add_execution(duration, len(results) == 10)

        result.print_stats()

        # Cleanup
        cursor.execute("DROP TABLE benchmark_queries")
        db_connection.commit()


@pytest.mark.benchmark
class TestEndToEndBenchmarks:
    """End-to-end system benchmarks"""

    def test_complete_workflow_performance(self, api_client, spark_session, redis_client):
        """Benchmark complete workflow from submission to completion"""
        result = BenchmarkResult("End-to-End Workflow")

        for i in range(10):
            workflow_start = time.time()

            # Step 1: Submit job via API
            api_response = api_client.post("/jobs/submit", json={
                "job_name": f"e2e_benchmark_{i}",
                "job_type": "benchmark",
                "parameters": {"index": i}
            })

            # Step 2: Process with Spark
            data = [(j, j * 2) for j in range(1000)]
            df = spark_session.createDataFrame(data, ["id", "value"])
            result_count = df.filter("id % 2 = 0").count()

            # Step 3: Store result in Redis
            if api_response.status_code == 200:
                job_id = api_response.json()["job_id"]
                redis_client.set(f"benchmark:result:{job_id}", str(result_count))

            # Step 4: Verify via API
            status_response = api_client.get(f"/jobs/{job_id}")

            workflow_duration = time.time() - workflow_start

            success = all([
                api_response.status_code == 200,
                result_count == 500,
                status_response.status_code == 200
            ])

            result.add_execution(workflow_duration, success)

        result.print_stats()

        stats = result.get_stats()
        assert stats["success_rate"] > 90.0
        assert stats["avg_time"] < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "benchmark"])
