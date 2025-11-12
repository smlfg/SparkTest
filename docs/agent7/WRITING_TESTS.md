# Writing Tests for Agent 7

Guide for writing effective tests for the Agent 7 LoRA fine-tuning system.

## Table of Contents

1. [Test Structure](#test-structure)
2. [Writing Integration Tests](#writing-integration-tests)
3. [Writing Performance Tests](#writing-performance-tests)
4. [Writing Load Tests](#writing-load-tests)
5. [Best Practices](#best-practices)
6. [Testing Patterns](#testing-patterns)

## Test Structure

### Basic Test Template

```python
"""
Test module description.
"""

import pytest


class TestFeatureName:
    """Test suite for specific feature."""

    def test_basic_functionality(self):
        """Test basic feature functionality."""
        # Arrange
        input_data = "test input"

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_output
```

### Using Fixtures

```python
@pytest.fixture
def sample_data():
    """Provide sample test data."""
    return {
        "key": "value",
        "list": [1, 2, 3]
    }


def test_with_fixture(sample_data):
    """Test using fixture."""
    assert sample_data["key"] == "value"
```

## Writing Integration Tests

### Student Workflow Test Example

```python
def test_complete_student_workflow(mock_api_client, sample_dataset, sample_training_config):
    """
    Test complete student workflow from login to inference.

    Steps:
    1. Student logs in
    2. Checks GPU availability
    3. Uploads dataset
    4. Starts training
    5. Monitors training
    6. Tests inference
    """
    # Step 1: Login
    login_response = mock_api_client.login("student1", "password123")
    assert login_response["status"] == "success", "Login should succeed"
    assert "token" in login_response, "Login should return token"

    # Step 2: Check GPU
    gpu_status = mock_api_client.check_gpu_status()
    assert gpu_status["available"] is True, "GPU should be available"
    assert gpu_status["memory_free"] > 0, "GPU should have free memory"

    # Step 3: Upload dataset
    dataset_response = mock_api_client.upload_dataset(str(sample_dataset))
    assert dataset_response["status"] == "success", "Dataset upload should succeed"
    dataset_id = dataset_response["dataset_id"]

    # Step 4: Start training
    train_response = mock_api_client.start_training(
        dataset_id,
        sample_training_config
    )
    assert train_response["status"] == "success", "Training should start"
    job_id = train_response["job_id"]

    # Step 5: Monitor training
    status = mock_api_client.get_training_status(job_id)
    assert status["status"] in ["running", "completed"], "Training should be active"

    # Complete training (simulation)
    mock_api_client.complete_training(job_id, "student_model")

    # Step 6: Test inference
    inference_response = mock_api_client.run_inference(
        "student_model",
        "Test prompt"
    )
    assert inference_response["status"] == "success", "Inference should succeed"
    assert inference_response["latency_ms"] < 2000, "Inference should be fast (<2s)"
```

### Service Communication Test Example

```python
def test_llama_factory_to_ollama_export():
    """Test exporting model from LLaMA Factory to Ollama."""
    # Setup services
    ollama = MockOllamaService()
    llama_factory = MockLLaMAFactory(ollama)

    # Start training
    train_response = llama_factory.start_training({
        "model": "llama3",
        "epochs": 3
    })
    job_id = train_response["job_id"]

    # Complete training
    llama_factory.complete_job(job_id)

    # Export to Ollama
    export_response = llama_factory.export_model_to_ollama(
        job_id,
        "custom_llama3"
    )

    # Verify export
    assert export_response["status"] == "success"
    assert export_response["registered"] is True

    # Verify model in Ollama
    models = ollama.list_models()
    assert len(models["models"]) == 1
    assert models["models"][0]["name"] == "custom_llama3"
```

### Error Handling Test Example

```python
def test_handles_invalid_dataset():
    """Test system handles invalid dataset gracefully."""
    from pathlib import Path
    import json

    # Create invalid dataset
    invalid_file = Path("/tmp/invalid.json")
    invalid_file.write_text("{invalid json")

    # Attempt to load
    with pytest.raises(json.JSONDecodeError) as exc_info:
        with open(invalid_file, "r") as f:
            json.load(f)

    # Verify error message
    assert "invalid" in str(exc_info.value).lower()
```

## Writing Performance Tests

### Latency Test Example

```python
def test_inference_latency_meets_sla(performance_thresholds):
    """Test that inference latency meets SLA requirements."""
    engine = MockInferenceEngine(base_latency_ms=100)

    # Collect latency samples
    latencies = []
    num_requests = 100

    for i in range(num_requests):
        result = engine.generate(f"Prompt {i}", max_tokens=50)
        latencies.append(result["latency_ms"])

    # Calculate percentiles
    percentiles = calculate_percentiles(latencies)

    # Assert SLA compliance
    thresholds = performance_thresholds["inference"]

    assert percentiles["p50"] < thresholds["latency_p50"], \
        f"p50 latency {percentiles['p50']:.1f}ms exceeds SLA of {thresholds['latency_p50']}ms"

    assert percentiles["p95"] < thresholds["latency_p95"], \
        f"p95 latency {percentiles['p95']:.1f}ms exceeds SLA of {thresholds['latency_p95']}ms"

    assert percentiles["p99"] < 2000, \
        f"p99 latency {percentiles['p99']:.1f}ms exceeds 2000ms"

    # Print results
    print(f"\nLatency Results:")
    print(f"  p50: {percentiles['p50']:.1f}ms")
    print(f"  p95: {percentiles['p95']:.1f}ms")
    print(f"  p99: {percentiles['p99']:.1f}ms")
```

### Throughput Test Example

```python
def test_training_throughput(performance_thresholds):
    """Test training throughput meets requirements."""
    job = MockTrainingJob(samples_per_sec=15)
    job.start()

    # Train for 100 samples
    batch_size = 8
    total_samples = 0

    while total_samples < 100:
        job.train_step(batch_size=batch_size)
        total_samples += batch_size

    # Calculate throughput
    throughput = job.get_throughput()

    # Assert threshold
    threshold = performance_thresholds["training"]["samples_per_sec"]
    assert throughput >= threshold, \
        f"Throughput {throughput:.2f} samples/sec below threshold {threshold}"

    print(f"\nTraining Throughput: {throughput:.2f} samples/sec")
```

### Concurrent Users Test Example

```python
def test_system_handles_concurrent_users():
    """Test system with multiple concurrent users."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    resources = MockSystemResources(max_concurrent=10)

    def user_workflow(user_id):
        """Simulate user workflow."""
        if resources.acquire_resources(memory_needed_mb=5000):
            try:
                time.sleep(0.1)  # Simulate work
                return {"user_id": user_id, "status": "success"}
            finally:
                resources.release_resources(memory_mb=5000)
        return {"user_id": user_id, "status": "resource_unavailable"}

    # Run 10 concurrent users
    num_users = 10
    with ThreadPoolExecutor(max_workers=num_users) as executor:
        futures = [executor.submit(user_workflow, i) for i in range(num_users)]
        results = [f.result() for f in as_completed(futures)]

    # Verify results
    successful = [r for r in results if r["status"] == "success"]
    assert len(successful) >= num_users * 0.8, \
        f"Only {len(successful)}/{num_users} users succeeded"
```

## Writing Load Tests

### Basic Locust User

```python
from locust import HttpUser, task, between


class BasicUser(HttpUser):
    """Basic user for load testing."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks

    def on_start(self):
        """Called when user starts."""
        self.login()

    def login(self):
        """Login to system."""
        response = self.client.post("/api/auth/login", json={
            "username": "test_user",
            "password": "test_pass"
        })

        if response.status_code == 200:
            self.token = response.json().get("token")

    @task(3)  # Weight: 3x more likely than other tasks
    def check_status(self):
        """Check system status (frequent operation)."""
        headers = {"Authorization": f"Bearer {self.token}"}
        self.client.get("/api/system/status", headers=headers)

    @task(1)
    def run_inference(self):
        """Run inference (less frequent operation)."""
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.client.post(
            "/api/inference",
            headers=headers,
            json={"model": "test_model", "prompt": "Hello"}
        )
```

### Custom Load Shape

```python
from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    Step load pattern:
    - 0-60s: 5 users
    - 60-120s: 10 users
    - 120-180s: 20 users
    """

    step_time = 60
    step_load = 5
    spawn_rate = 5
    time_limit = 180

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = (run_time // self.step_time) + 1
        return (current_step * self.step_load, self.spawn_rate)
```

## Best Practices

### 1. Arrange-Act-Assert Pattern

```python
def test_feature():
    # Arrange: Set up test data and preconditions
    input_data = create_test_data()
    expected_output = define_expected_result()

    # Act: Execute the code being tested
    actual_output = function_under_test(input_data)

    # Assert: Verify the results
    assert actual_output == expected_output
```

### 2. Clear Test Names

```python
# ❌ Bad
def test_1():
    pass

# ✅ Good
def test_login_with_valid_credentials_succeeds():
    pass

# ✅ Good
def test_upload_oversized_dataset_raises_error():
    pass
```

### 3. Use Parametrize for Multiple Scenarios

```python
@pytest.mark.parametrize("batch_size,expected_throughput", [
    (1, 10),
    (2, 18),
    (4, 30),
    (8, 50),
])
def test_batch_size_affects_throughput(batch_size, expected_throughput):
    """Test different batch sizes."""
    job = MockTrainingJob()
    job.start()

    job.train_step(batch_size=batch_size)
    throughput = job.get_throughput()

    assert throughput >= expected_throughput
```

### 4. Mock External Dependencies

```python
from unittest.mock import Mock, patch


def test_with_mocked_api():
    """Test with mocked external API."""
    with patch('requests.get') as mock_get:
        # Configure mock
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok"}

        # Test code that uses requests.get
        result = function_that_calls_api()

        # Verify mock was called
        mock_get.assert_called_once()
        assert result["status"] == "ok"
```

### 5. Test Edge Cases

```python
def test_edge_cases():
    """Test edge cases and boundary conditions."""
    # Empty input
    assert function([]) == []

    # Single item
    assert function([1]) == [1]

    # Large input
    assert len(function(range(10000))) == 10000

    # Negative numbers
    assert function([-1, -2, -3]) == expected_result

    # None input
    with pytest.raises(TypeError):
        function(None)
```

### 6. Assertions with Messages

```python
def test_with_clear_messages():
    """Use assertion messages for better debugging."""
    result = calculate_score(data)

    assert result > 0, "Score should be positive"
    assert result <= 100, f"Score {result} should not exceed 100"
    assert isinstance(result, float), "Score should be a float"
```

## Testing Patterns

### Pattern 1: Test Fixture Factories

```python
@pytest.fixture
def create_user():
    """Factory for creating test users."""
    def _create_user(username="test", role="student"):
        return {
            "username": username,
            "role": role,
            "token": f"token_{username}"
        }
    return _create_user


def test_with_factory(create_user):
    """Use factory to create multiple users."""
    student = create_user(username="student1", role="student")
    admin = create_user(username="admin1", role="admin")

    assert student["role"] == "student"
    assert admin["role"] == "admin"
```

### Pattern 2: Context Managers for Setup/Teardown

```python
from contextlib import contextmanager


@contextmanager
def temporary_training_job():
    """Context manager for temporary training job."""
    job = MockTrainingJob()
    job.start()

    try:
        yield job
    finally:
        job.cleanup()  # Always cleanup


def test_with_context_manager():
    """Use context manager for automatic cleanup."""
    with temporary_training_job() as job:
        job.train_step()
        assert job.samples_processed > 0
    # job.cleanup() automatically called
```

### Pattern 3: Custom Markers

```python
import pytest


# Define custom markers in pytest.ini or conftest.py
# [tool:pytest]
# markers =
#     slow: marks tests as slow
#     integration: marks tests as integration tests


@pytest.mark.slow
def test_long_running_operation():
    """Slow test that takes time."""
    pass


@pytest.mark.integration
def test_service_integration():
    """Integration test."""
    pass
```

Run specific markers:
```bash
# Run only integration tests
pytest -m integration

# Skip slow tests
pytest -m "not slow"
```

### Pattern 4: Snapshot Testing

```python
def test_output_snapshot(snapshot):
    """Test against saved snapshot."""
    result = generate_complex_output()

    # First run: saves snapshot
    # Subsequent runs: compares against snapshot
    assert result == snapshot
```

## Common Pitfalls to Avoid

1. **Don't test implementation details** - Test behavior, not internals
2. **Avoid test interdependence** - Each test should run independently
3. **Don't use sleep() unnecessarily** - Use mocking instead
4. **Avoid hardcoded paths** - Use fixtures and temporary directories
5. **Don't skip assertions** - Always verify results

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Locust Documentation](https://docs.locust.io/)
