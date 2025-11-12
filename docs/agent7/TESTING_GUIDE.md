# Agent 7 Testing Guide

Comprehensive testing guide for Agent 7: LoRA Fine-tuning System.

## Table of Contents

1. [Overview](#overview)
2. [Test Structure](#test-structure)
3. [Running Tests](#running-tests)
4. [Test Categories](#test-categories)
5. [Performance Benchmarks](#performance-benchmarks)
6. [Load Testing](#load-testing)
7. [CI/CD Pipeline](#cicd-pipeline)
8. [Troubleshooting](#troubleshooting)

## Overview

Agent 7's test suite ensures the reliability, performance, and scalability of the LoRA fine-tuning system. The tests cover:

- **Integration Tests**: End-to-end workflows and service communication
- **Performance Tests**: Latency, throughput, and training speed benchmarks
- **Load Tests**: Concurrent user scenarios and stress testing
- **Unit Tests**: Individual component testing

### Test Coverage Goals

- **Code Coverage**: >80%
- **Integration Coverage**: All critical workflows
- **Performance SLA**: All benchmarks within thresholds

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared pytest fixtures
├── integration/             # Integration tests
│   ├── test_student_workflow.py
│   ├── test_service_communication.py
│   └── test_error_handling.py
├── performance/             # Performance benchmarks
│   ├── test_inference_latency.py
│   ├── test_training_speed.py
│   └── test_concurrent_users.py
├── load/                    # Load testing
│   └── locustfile.py
├── unit/                    # Unit tests
│   └── ...
├── fixtures/                # Test data
│   └── ...
└── helpers/                 # Test utilities
    └── ...
```

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-timeout pytest-benchmark

# Run all tests
pytest

# Run specific category
pytest tests/integration/
pytest tests/performance/
```

### Integration Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test file
pytest tests/integration/test_student_workflow.py -v

# Run specific test
pytest tests/integration/test_student_workflow.py::TestStudentWorkflow::test_full_workflow_integration -v
```

### Performance Tests

```bash
# Run performance benchmarks
pytest tests/performance/ -v

# Run with benchmark output
pytest tests/performance/ --benchmark-only

# Save benchmark results
pytest tests/performance/ --benchmark-save=baseline
```

### Load Tests

```bash
# Install Locust
pip install locust

# Run load tests (web UI)
locust -f tests/load/locustfile.py --host=http://localhost:8000

# Headless mode (10 users, 5 minutes)
locust -f tests/load/locustfile.py --host=http://localhost:8000 \
  --users 10 --spawn-rate 1 --run-time 5m --headless
```

## Test Categories

### 1. Integration Tests

#### Student Workflow Tests

Test complete student journey from login to model deployment.

**File**: `tests/integration/test_student_workflow.py`

**Coverage**:
- ✅ Login authentication
- ✅ Dashboard access
- ✅ GPU availability check
- ✅ Dataset upload
- ✅ Training job start
- ✅ Training completion
- ✅ Model inference testing

**Example**:
```python
def test_full_workflow_integration(mock_api_client, sample_dataset):
    # Login
    login_response = mock_api_client.login("student1", "password123")
    assert login_response["status"] == "success"

    # Upload dataset
    dataset_response = mock_api_client.upload_dataset(str(sample_dataset))
    assert dataset_response["status"] == "success"

    # Start training
    train_response = mock_api_client.start_training(...)
    assert train_response["status"] == "success"

    # ... complete workflow
```

#### Service Communication Tests

Test inter-service communication and integration.

**File**: `tests/integration/test_service_communication.py`

**Coverage**:
- ✅ Ollama ↔ Open-WebUI communication
- ✅ LLaMA Factory ↔ Ollama integration
- ✅ Dashboard ↔ All services
- ✅ Model export and registration
- ✅ End-to-end service flow

#### Error Handling Tests

Test system resilience and error recovery.

**File**: `tests/integration/test_error_handling.py`

**Coverage**:
- ✅ Invalid dataset uploads
- ✅ OOM during training
- ✅ Service unavailable scenarios
- ✅ Network timeout handling
- ✅ Circuit breaker patterns

### 2. Performance Tests

#### Inference Latency

**File**: `tests/performance/test_inference_latency.py`

**Metrics**:
- P50 latency: <500ms
- P95 latency: <1000ms
- Throughput: >50 tokens/sec

**Example**:
```python
def test_latency_percentiles(performance_thresholds):
    engine = MockInferenceEngine()

    # Run 100 requests
    latencies = []
    for i in range(100):
        result = engine.generate(f"Prompt {i}")
        latencies.append(result["latency_ms"])

    percentiles = calculate_percentiles(latencies)

    assert percentiles["p50"] < thresholds["latency_p50"]
    assert percentiles["p95"] < thresholds["latency_p95"]
```

#### Training Speed

**File**: `tests/performance/test_training_speed.py`

**Metrics**:
- Samples/second: >10
- Startup time: <120s
- Checkpoint save: <30s

#### Concurrent Users

**File**: `tests/performance/test_concurrent_users.py`

**Scenarios**:
- 5 concurrent users
- 10 concurrent users
- 20 concurrent users (stress test)

### 3. Load Tests

#### Load Testing with Locust

**File**: `tests/load/locustfile.py`

**Scenarios**:

1. **Steady Load** (10 users, 10 minutes)
   ```bash
   locust -f tests/load/locustfile.py --users 10 --run-time 10m
   ```

2. **High Load** (20 users, 5 minutes)
   ```bash
   locust -f tests/load/locustfile.py --users 20 --run-time 5m
   ```

3. **Spike Test** (spike to 50 users)
   ```bash
   locust -f tests/load/locustfile.py --users 50 --spawn-rate 10 --run-time 3m
   ```

**Metrics Collected**:
- Requests per second
- Failure rate
- 95th percentile latency
- Average response time

## Performance Benchmarks

### SLA Thresholds

```python
performance_thresholds = {
    "inference": {
        "latency_p50": 500,  # ms
        "latency_p95": 1000,  # ms
        "throughput": 50,  # tokens/sec
    },
    "training": {
        "startup": 120,  # seconds
        "samples_per_sec": 10,
        "checkpoint_save": 30,  # seconds
    },
    "dashboard": {
        "page_load": 2000,  # ms
        "api_response": 200,  # ms
        "websocket_latency": 50,  # ms
    }
}
```

### Running Benchmarks

```bash
# Run all benchmarks
pytest tests/performance/ --benchmark-only

# Compare against baseline
pytest tests/performance/ --benchmark-compare=baseline

# Save new baseline
pytest tests/performance/ --benchmark-save=new_baseline

# Generate benchmark report
pytest tests/performance/ --benchmark-only --benchmark-json=report.json
```

## CI/CD Pipeline

### GitHub Actions Workflow

**File**: `.github/workflows/integration-tests.yml`

### Triggered On

- Push to `main`, `develop`, or `claude/*` branches
- Pull requests to `main` or `develop`
- Nightly schedule (2 AM UTC)
- Manual trigger

### Jobs

1. **syntax-validation**
   - Black code formatting
   - isort import sorting
   - flake8 linting
   - mypy type checking

2. **unit-tests**
   - Run all unit tests
   - Generate coverage report

3. **integration-tests**
   - Run integration test suite
   - Upload test results

4. **performance-tests**
   - Run performance benchmarks
   - Upload benchmark results

5. **security-scan**
   - Bandit security scan
   - Safety dependency check

6. **coverage-report**
   - Generate coverage report
   - Upload to Codecov

7. **notification**
   - Slack notification on failure
   - Email on success

### Local CI Simulation

```bash
# Run full CI pipeline locally
./scripts/run_ci_locally.sh

# Or run individual steps
black --check .
isort --check-only .
flake8 .
pytest tests/ --cov=. --cov-report=term
```

## Writing Tests

See [WRITING_TESTS.md](./WRITING_TESTS.md) for detailed guide on writing tests.

## Troubleshooting

### Common Issues

#### Tests Timing Out

```bash
# Increase timeout
pytest tests/ --timeout=600

# Disable timeout for debugging
pytest tests/ --timeout=0
```

#### Import Errors

```bash
# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/
```

#### GPU Not Available

Tests are designed to work without GPU. Mock objects simulate GPU operations.

```python
# Tests use mock GPU
class MockGPU:
    def __init__(self, total_memory_gb=80):
        self.total_memory = total_memory_gb * 1024
```

#### Fixture Not Found

Make sure `conftest.py` is in the tests directory:

```bash
tests/
├── conftest.py  # Should be here
├── integration/
└── performance/
```

### Debug Mode

```bash
# Run with verbose output
pytest tests/ -vv

# Show print statements
pytest tests/ -s

# Drop into debugger on failure
pytest tests/ --pdb

# Run specific test with full traceback
pytest tests/integration/test_student_workflow.py::test_login -vv --tb=long
```

### Viewing Test Coverage

```bash
# Generate HTML coverage report
pytest tests/ --cov=. --cov-report=html

# Open in browser
open htmlcov/index.html
```

## Best Practices

1. **Use Fixtures**: Leverage pytest fixtures for setup/teardown
2. **Mock External Dependencies**: Don't rely on external services
3. **Parametrize Tests**: Use `@pytest.mark.parametrize` for multiple scenarios
4. **Clear Test Names**: Use descriptive test names that explain what's being tested
5. **Fast Tests**: Keep unit tests under 1 second, integration tests under 10 seconds
6. **Isolation**: Each test should be independent and not rely on others
7. **Assertions**: Include clear assertion messages

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Locust Documentation](https://docs.locust.io/)
- [Python unittest](https://docs.python.org/3/library/unittest.html)

## Support

For questions or issues:
- Open an issue on GitHub
- Check existing test examples
- Review test output logs
