"""
Integration tests for infrastructure components
Tests PostgreSQL, Redis, and service communication
"""

import pytest
import time
import json


@pytest.mark.integration
@pytest.mark.smoke
class TestRedisIntegration:
    """Test suite for Redis integration"""

    def test_redis_connection(self, redis_client):
        """Test Redis connection"""
        assert redis_client.ping() is True

    def test_redis_set_get(self, redis_client):
        """Test basic Redis operations"""
        redis_client.set("test:key1", "value1")
        value = redis_client.get("test:key1")
        assert value == "value1"

    def test_redis_hash_operations(self, redis_client):
        """Test Redis hash operations"""
        redis_client.hset("test:hash1", mapping={
            "field1": "value1",
            "field2": "value2",
            "field3": "value3"
        })

        all_data = redis_client.hgetall("test:hash1")
        assert len(all_data) == 3
        assert all_data["field1"] == "value1"

    def test_redis_list_operations(self, redis_client):
        """Test Redis list operations"""
        redis_client.lpush("test:list1", "item1", "item2", "item3")
        length = redis_client.llen("test:list1")
        assert length == 3

        item = redis_client.rpop("test:list1")
        assert item == "item1"

    def test_redis_expiration(self, redis_client):
        """Test Redis key expiration"""
        redis_client.setex("test:expiring_key", 2, "temporary_value")
        assert redis_client.get("test:expiring_key") == "temporary_value"

        time.sleep(3)
        assert redis_client.get("test:expiring_key") is None

    def test_redis_pubsub(self, redis_client):
        """Test Redis pub/sub functionality"""
        pubsub = redis_client.pubsub()
        pubsub.subscribe("test:channel")

        # Publish message
        redis_client.publish("test:channel", "test_message")

        # Receive message (skip subscription confirmation)
        message = None
        for msg in pubsub.listen():
            if msg["type"] == "message":
                message = msg["data"]
                break

        pubsub.unsubscribe("test:channel")
        assert message == "test_message"


@pytest.mark.integration
@pytest.mark.smoke
class TestDatabaseIntegration:
    """Test suite for PostgreSQL integration"""

    def test_database_connection(self, db_connection):
        """Test database connection"""
        cursor = db_connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1

    def test_create_table(self, db_connection):
        """Test creating and using a table"""
        cursor = db_connection.cursor()

        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100),
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        db_connection.commit()

        # Insert data
        cursor.execute(
            "INSERT INTO test_users (name, email) VALUES (%s, %s) RETURNING id",
            ("Test User", "test@example.com")
        )
        user_id = cursor.fetchone()[0]
        db_connection.commit()

        # Query data
        cursor.execute("SELECT name, email FROM test_users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        assert result[0] == "Test User"
        assert result[1] == "test@example.com"

        # Cleanup
        cursor.execute("DROP TABLE test_users")
        db_connection.commit()

    def test_transaction_rollback(self, db_connection):
        """Test transaction rollback"""
        cursor = db_connection.cursor()

        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_rollback (
                id SERIAL PRIMARY KEY,
                value VARCHAR(100)
            )
        """)
        db_connection.commit()

        # Insert and rollback
        cursor.execute("INSERT INTO test_rollback (value) VALUES (%s)", ("test",))
        db_connection.rollback()

        # Verify rollback
        cursor.execute("SELECT COUNT(*) FROM test_rollback")
        count = cursor.fetchone()[0]
        assert count == 0

        # Cleanup
        cursor.execute("DROP TABLE test_rollback")
        db_connection.commit()

    def test_batch_insert(self, db_connection):
        """Test batch insert operations"""
        cursor = db_connection.cursor()

        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_batch (
                id SERIAL PRIMARY KEY,
                value INTEGER
            )
        """)
        db_connection.commit()

        # Batch insert
        data = [(i,) for i in range(100)]
        cursor.executemany("INSERT INTO test_batch (value) VALUES (%s)", data)
        db_connection.commit()

        # Verify
        cursor.execute("SELECT COUNT(*) FROM test_batch")
        count = cursor.fetchone()[0]
        assert count == 100

        # Cleanup
        cursor.execute("DROP TABLE test_batch")
        db_connection.commit()


@pytest.mark.integration
@pytest.mark.agent9
class TestMonitoringIntegration:
    """Test suite for Agent 9: Monitoring"""

    def test_metrics_collection(self, api_client):
        """Test that metrics are being collected"""
        # Trigger some API calls to generate metrics
        api_client.get("/health")
        api_client.get("/agents")

        # Check metrics endpoint
        response = api_client.get("/metrics")
        assert response.status_code == 200

        metrics = response.text
        assert "sparktest_api_requests_total" in metrics
        assert "sparktest_jobs_total" in metrics

    def test_health_monitoring(self, api_client):
        """Test health check monitoring"""
        response = api_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert "services" in data

        # All critical services should be monitored
        required_services = ["api", "redis", "database", "spark"]
        for service in required_services:
            assert service in data["services"]


@pytest.mark.integration
class TestEndToEndWorkflow:
    """End-to-end integration tests for complete workflows"""

    def test_complete_job_workflow(self, api_client, redis_client):
        """Test complete job submission and tracking workflow"""
        # 1. Submit job
        job_data = {
            "job_name": "e2e_test_job",
            "job_type": "data_processing",
            "parameters": {
                "source": "test_source",
                "destination": "test_destination"
            },
            "priority": 8
        }

        submit_response = api_client.post("/jobs/submit", json=job_data)
        assert submit_response.status_code == 200

        job_id = submit_response.json()["job_id"]

        # 2. Verify job in Redis
        job_key = f"job:{job_id}"
        job_exists = redis_client.exists(job_key)
        assert job_exists == 1

        # 3. Check job status
        status_response = api_client.get(f"/jobs/{job_id}")
        assert status_response.status_code == 200

        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert status_data["job_name"] == "e2e_test_job"

        # 4. Verify job in queue
        queue_length = redis_client.llen("job_queue")
        assert queue_length > 0

    def test_multi_agent_coordination(self, api_client, spark_session, redis_client):
        """Test coordination between multiple agents"""
        # Agent 1: Data Ingestion - Create data
        data = [(i, f"item_{i}", i * 10) for i in range(100)]
        df = spark_session.createDataFrame(data, ["id", "name", "value"])
        df.createOrReplaceTempView("ingested_data")

        # Agent 2: Data Processing - Transform data
        processed = spark_session.sql("""
            SELECT id, name, value, value * 2 as doubled_value
            FROM ingested_data
            WHERE id % 2 = 0
        """)
        assert processed.count() == 50

        # Agent 6: Batch Processing - Aggregate data
        from pyspark.sql.functions import sum as spark_sum
        aggregated = processed.agg(spark_sum("value").alias("total"))
        total = aggregated.collect()[0]["total"]

        # Agent 8: Scheduler - Store result in Redis
        redis_client.set("test:aggregation_result", str(total))

        # Agent 9: Monitoring - Verify result
        stored_result = redis_client.get("test:aggregation_result")
        assert stored_result is not None

        # Agent 10: Integration - Verify workflow
        assert int(stored_result) == sum(i * 10 for i in range(0, 100, 2))

    def test_error_handling_workflow(self, api_client):
        """Test error handling across services"""
        # Submit invalid job
        invalid_job = {
            "job_name": "",  # Invalid: empty name
            "job_type": "invalid_type",
            "parameters": {}
        }

        # API should handle gracefully
        response = api_client.post("/jobs/submit", json=invalid_job)
        # Even with invalid data, API should respond (may succeed or fail gracefully)
        assert response.status_code in [200, 400, 422]

    def test_concurrent_operations(self, api_client, redis_client):
        """Test concurrent operations across services"""
        import concurrent.futures

        def perform_operation(index):
            # Submit job
            job_response = api_client.post("/jobs/submit", json={
                "job_name": f"concurrent_job_{index}",
                "job_type": "test",
                "parameters": {"index": index}
            })

            # Store in Redis
            redis_client.set(f"test:concurrent_{index}", str(index))

            # List jobs
            list_response = api_client.get("/jobs")

            return all([
                job_response.status_code == 200,
                list_response.status_code == 200,
                redis_client.get(f"test:concurrent_{index}") == str(index)
            ])

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(perform_operation, range(20)))

        assert all(results), "All concurrent operations should succeed"


@pytest.mark.integration
@pytest.mark.performance
class TestSystemPerformance:
    """System-wide performance tests"""

    def test_system_throughput(self, api_client):
        """Test overall system throughput"""
        import concurrent.futures
        import time

        start_time = time.time()

        def submit_jobs(batch_id):
            for i in range(10):
                api_client.post("/jobs/submit", json={
                    "job_name": f"throughput_job_{batch_id}_{i}",
                    "job_type": "test",
                    "parameters": {"batch": batch_id, "index": i}
                })

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            list(executor.map(submit_jobs, range(5)))

        duration = time.time() - start_time

        # Should handle 50 job submissions in reasonable time
        assert duration < 30.0, f"Throughput test took {duration}s, expected < 30s"

    def test_resource_utilization(self, spark_session, redis_client, db_connection):
        """Test resource utilization under load"""
        # Spark load
        large_df = spark_session.range(10000)
        result = large_df.filter("id % 2 = 0").count()
        assert result == 5000

        # Redis load
        for i in range(100):
            redis_client.set(f"test:load_{i}", f"value_{i}")

        # Database load
        cursor = db_connection.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()

        # All services should remain responsive
        assert redis_client.ping() is True
