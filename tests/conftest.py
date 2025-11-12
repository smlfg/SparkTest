"""
Pytest configuration and fixtures for SparkTest integration tests
"""

import pytest
import os
import time
import redis
import psycopg2
from typing import Generator
import httpx
from pyspark.sql import SparkSession

# Test environment configuration
SPARK_MASTER_URL = os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sparktest:sparktest123@postgres:5432/sparktest_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")
API_URL = os.getenv("API_URL", "http://api-gateway:8000")

# Timeouts and retries
SERVICE_STARTUP_TIMEOUT = 60
RETRY_INTERVAL = 2


@pytest.fixture(scope="session")
def wait_for_services():
    """Wait for all services to be ready before running tests"""
    print("\n🔄 Waiting for services to be ready...")

    # Wait for Redis
    redis_ready = False
    for attempt in range(SERVICE_STARTUP_TIMEOUT // RETRY_INTERVAL):
        try:
            r = redis.from_url(REDIS_URL)
            r.ping()
            redis_ready = True
            print("✓ Redis is ready")
            break
        except Exception as e:
            time.sleep(RETRY_INTERVAL)

    if not redis_ready:
        pytest.fail("Redis failed to start within timeout")

    # Wait for PostgreSQL
    db_ready = False
    for attempt in range(SERVICE_STARTUP_TIMEOUT // RETRY_INTERVAL):
        try:
            conn = psycopg2.connect(DATABASE_URL)
            conn.close()
            db_ready = True
            print("✓ PostgreSQL is ready")
            break
        except Exception as e:
            time.sleep(RETRY_INTERVAL)

    if not db_ready:
        pytest.fail("PostgreSQL failed to start within timeout")

    # Wait for API Gateway
    api_ready = False
    for attempt in range(SERVICE_STARTUP_TIMEOUT // RETRY_INTERVAL):
        try:
            response = httpx.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                api_ready = True
                print("✓ API Gateway is ready")
                break
        except Exception as e:
            time.sleep(RETRY_INTERVAL)

    if not api_ready:
        pytest.fail("API Gateway failed to start within timeout")

    print("✅ All services are ready!\n")
    yield


@pytest.fixture(scope="session")
def spark_session(wait_for_services) -> Generator[SparkSession, None, None]:
    """Create a Spark session for testing"""
    spark = SparkSession.builder \
        .appName("SparkTest-Integration-Tests") \
        .master(SPARK_MASTER_URL) \
        .config("spark.sql.shuffle.partitions", "4") \
        .config("spark.default.parallelism", "4") \
        .config("spark.driver.memory", "1g") \
        .config("spark.executor.memory", "1g") \
        .getOrCreate()

    print(f"✓ Spark session created: {spark.version}")

    yield spark

    spark.stop()
    print("✓ Spark session stopped")


@pytest.fixture
def redis_client(wait_for_services) -> Generator[redis.Redis, None, None]:
    """Create a Redis client for testing"""
    client = redis.from_url(REDIS_URL, decode_responses=True)
    yield client
    # Cleanup test keys
    test_keys = client.keys("test:*")
    if test_keys:
        client.delete(*test_keys)


@pytest.fixture
def db_connection(wait_for_services) -> Generator[psycopg2.extensions.connection, None, None]:
    """Create a database connection for testing"""
    conn = psycopg2.connect(DATABASE_URL)
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def api_client(wait_for_services) -> Generator[httpx.Client, None, None]:
    """Create an HTTP client for API testing"""
    with httpx.Client(base_url=API_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def sample_data():
    """Generate sample data for testing"""
    return {
        "users": [
            {"id": 1, "name": "Alice", "age": 30, "city": "New York"},
            {"id": 2, "name": "Bob", "age": 25, "city": "San Francisco"},
            {"id": 3, "name": "Charlie", "age": 35, "city": "Seattle"},
            {"id": 4, "name": "Diana", "age": 28, "city": "Boston"},
            {"id": 5, "name": "Eve", "age": 32, "city": "Austin"},
        ],
        "transactions": [
            {"id": 1, "user_id": 1, "amount": 100.50, "timestamp": "2025-01-01T10:00:00"},
            {"id": 2, "user_id": 2, "amount": 250.75, "timestamp": "2025-01-01T11:00:00"},
            {"id": 3, "user_id": 1, "amount": 75.25, "timestamp": "2025-01-01T12:00:00"},
            {"id": 4, "user_id": 3, "amount": 500.00, "timestamp": "2025-01-01T13:00:00"},
            {"id": 5, "user_id": 2, "amount": 150.00, "timestamp": "2025-01-01T14:00:00"},
        ]
    }


@pytest.fixture(autouse=True)
def test_metadata(request):
    """Automatically log test metadata"""
    print(f"\n🧪 Running: {request.node.name}")
    start_time = time.time()
    yield
    duration = time.time() - start_time
    print(f"⏱️  Duration: {duration:.2f}s")


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "smoke: Smoke tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "agent1: Agent 1 tests")
    config.addinivalue_line("markers", "agent2: Agent 2 tests")
    config.addinivalue_line("markers", "agent3: Agent 3 tests")
    config.addinivalue_line("markers", "agent4: Agent 4 tests")
    config.addinivalue_line("markers", "agent5: Agent 5 tests")
    config.addinivalue_line("markers", "agent6: Agent 6 tests")
    config.addinivalue_line("markers", "agent7: Agent 7 tests")
    config.addinivalue_line("markers", "agent8: Agent 8 tests")
    config.addinivalue_line("markers", "agent9: Agent 9 tests")
    config.addinivalue_line("markers", "agent10: Agent 10 tests")
