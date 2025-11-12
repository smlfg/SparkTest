# CI/CD Pipeline for Agent 7

Documentation for the Continuous Integration and Continuous Deployment pipeline for Agent 7: LoRA Fine-tuning System.

## Table of Contents

1. [Overview](#overview)
2. [Pipeline Architecture](#pipeline-architecture)
3. [Workflow Jobs](#workflow-jobs)
4. [Configuration](#configuration)
5. [Local Development](#local-development)
6. [Troubleshooting](#troubleshooting)

## Overview

Agent 7 uses GitHub Actions for CI/CD automation. The pipeline ensures code quality, runs comprehensive tests, and provides feedback on every code change.

### Triggers

The CI/CD pipeline is triggered on:

- **Push**: To `main`, `develop`, or `claude/*` branches
- **Pull Request**: To `main` or `develop` branches
- **Schedule**: Nightly at 2 AM UTC
- **Manual**: Via workflow_dispatch

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   GitHub Actions Workflow                    │
└─────────────────────────────────────────────────────────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
          ┌──────▼──────┐           ┌───────▼────────┐
          │   Syntax    │           │  Unit Tests    │
          │ Validation  │           │                │
          └──────┬──────┘           └───────┬────────┘
                 │                           │
                 └─────────────┬─────────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │   Integration Tests       │
                 │  - Student Workflow       │
                 │  - Service Communication  │
                 │  - Error Handling         │
                 └─────────────┬─────────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │   Performance Tests       │
                 │  - Latency Benchmarks     │
                 │  - Training Speed         │
                 │  - Concurrent Users       │
                 └─────────────┬─────────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │   Security Scan           │
                 │  - Bandit                 │
                 │  - Safety                 │
                 └─────────────┬─────────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │   Coverage Report         │
                 │  - Generate HTML          │
                 │  - Upload to Codecov      │
                 └─────────────┬─────────────┘
                               │
                 ┌─────────────▼─────────────┐
                 │   Notifications           │
                 │  - Slack (on failure)     │
                 │  - Email (on success)     │
                 └───────────────────────────┘
```

## Workflow Jobs

### 1. Syntax Validation

**Purpose**: Ensure code quality and style compliance

**Steps**:
1. Checkout code
2. Setup Python environment
3. Install linting tools (black, isort, flake8, mypy)
4. Check code formatting with Black
5. Check import sorting with isort
6. Lint with flake8
7. Type check with mypy

**Configuration**:
```yaml
- name: Check code formatting with Black
  run: black --check --diff .

- name: Check import sorting with isort
  run: isort --check-only --diff .

- name: Lint with flake8
  run: flake8 . --max-line-length=120 --statistics
```

**Local Execution**:
```bash
# Format code
black .
isort .

# Check before commit
black --check .
isort --check-only .
flake8 .
```

### 2. Unit Tests

**Purpose**: Test individual components in isolation

**Steps**:
1. Setup Python environment
2. Cache pip packages
3. Install test dependencies
4. Run pytest on unit tests
5. Upload test results

**Configuration**:
```yaml
- name: Run unit tests
  run: pytest tests/unit/ -v --tb=short
```

**Local Execution**:
```bash
pytest tests/unit/ -v
```

### 3. Integration Tests

**Purpose**: Test end-to-end workflows and service interactions

**Timeout**: 30 minutes

**Steps**:
1. Setup environment
2. Install dependencies
3. Run integration tests with timeout
4. Upload test results and logs

**Configuration**:
```yaml
- name: Run integration tests
  run: |
    pytest tests/integration/ -v --tb=short --timeout=300 --maxfail=3
```

**Tests Included**:
- Student workflow (login → training → inference)
- Service communication (Ollama ↔ WebUI, LLaMA Factory)
- Error handling (invalid data, OOM, timeouts)

**Local Execution**:
```bash
pytest tests/integration/ -v --timeout=300
```

### 4. Performance Tests

**Purpose**: Benchmark performance and ensure SLA compliance

**Timeout**: 20 minutes

**Steps**:
1. Setup environment
2. Install benchmark dependencies
3. Run performance tests with benchmarking
4. Upload benchmark results

**Configuration**:
```yaml
- name: Run performance benchmarks
  run: |
    pytest tests/performance/ -v --benchmark-only --benchmark-min-rounds=5
```

**Metrics Tracked**:
- Inference latency (p50, p95, p99)
- Training throughput (samples/sec)
- Concurrent user capacity
- Response times

**Local Execution**:
```bash
# Run benchmarks
pytest tests/performance/ --benchmark-only

# Save baseline
pytest tests/performance/ --benchmark-save=baseline

# Compare against baseline
pytest tests/performance/ --benchmark-compare=baseline
```

### 5. Security Scan

**Purpose**: Identify security vulnerabilities

**Tools**:
- **Bandit**: Scans for common security issues in Python code
- **Safety**: Checks dependencies for known vulnerabilities

**Configuration**:
```yaml
- name: Run Bandit security scan
  run: bandit -r agent7_lora/ -ll

- name: Check dependencies with Safety
  run: safety check --json
```

**Local Execution**:
```bash
# Install tools
pip install bandit safety

# Run scans
bandit -r agent7_lora/ -f json -o bandit-report.json
safety check
```

### 6. Coverage Report

**Purpose**: Track test coverage and identify gaps

**Steps**:
1. Run tests with coverage tracking
2. Generate HTML and XML reports
3. Upload to Codecov
4. Save HTML report as artifact

**Configuration**:
```yaml
- name: Run tests with coverage
  run: |
    pytest tests/ --cov=agent7_lora --cov=. \
      --cov-report=xml --cov-report=html --cov-report=term

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

**Coverage Goals**:
- Overall: >80%
- Critical modules: >90%
- New code: 100%

**Local Execution**:
```bash
# Generate coverage report
pytest tests/ --cov=. --cov-report=html

# View report
open htmlcov/index.html
```

### 7. Notification

**Purpose**: Alert team of build status

**Triggers**:
- **Failure**: Slack notification
- **Success**: Email notification

**Configuration**:
```yaml
- name: Send Slack notification on failure
  if: failure()
  run: |
    curl -X POST -H 'Content-type: application/json' \
      --data '{"text":"Agent 7 tests failed!"}' \
      ${{ secrets.SLACK_WEBHOOK_URL }}
```

## Configuration

### Environment Variables

```yaml
env:
  PYTHON_VERSION: '3.10'
```

### Secrets

Configure in GitHub repository settings:

- `SLACK_WEBHOOK_URL`: Slack incoming webhook for notifications
- `CODECOV_TOKEN`: Token for Codecov integration (optional)

### Caching

Pip packages are cached to speed up builds:

```yaml
- name: Cache pip packages
  uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
```

### Test Matrix

Tests run on multiple Python versions:

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11']
```

## Local Development

### Running Full CI Pipeline Locally

Create a script to simulate CI:

```bash
#!/bin/bash
# scripts/run_ci_locally.sh

set -e

echo "=== Syntax Validation ==="
black --check .
isort --check-only .
flake8 .

echo "=== Unit Tests ==="
pytest tests/unit/ -v

echo "=== Integration Tests ==="
pytest tests/integration/ -v --timeout=300

echo "=== Performance Tests ==="
pytest tests/performance/ -v --benchmark-only

echo "=== Security Scan ==="
bandit -r agent7_lora/
safety check

echo "=== Coverage Report ==="
pytest tests/ --cov=. --cov-report=term

echo "✓ All checks passed!"
```

Run with:
```bash
chmod +x scripts/run_ci_locally.sh
./scripts/run_ci_locally.sh
```

### Pre-commit Hooks

Install pre-commit hooks to run checks before commits:

```bash
# Install pre-commit
pip install pre-commit

# Create .pre-commit-config.yaml
cat > .pre-commit-config.yaml << EOF
repos:
  - repo: https://github.com/psf/black
    rev: 23.10.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        args: [--max-line-length=120]

  - repo: local
    hooks:
      - id: pytest-quick
        name: pytest-quick
        entry: pytest tests/unit/ -v
        language: system
        pass_filenames: false
EOF

# Install hooks
pre-commit install
```

## Troubleshooting

### Job Timeouts

If jobs timeout:

1. **Check logs** for hanging operations
2. **Increase timeout** in workflow
3. **Split long tests** into smaller units

```yaml
timeout-minutes: 45  # Increase from 30
```

### Flaky Tests

For intermittent failures:

1. **Add retries** to flaky tests
2. **Increase timeouts** for network operations
3. **Use mocking** instead of real services

```python
@pytest.mark.flaky(reruns=3, reruns_delay=2)
def test_flaky_operation():
    pass
```

### Cache Issues

If cache causes problems:

1. **Clear cache** in GitHub Actions UI
2. **Update cache key** to force rebuild
3. **Disable caching** temporarily

```yaml
# Update cache key
key: ${{ runner.os }}-pip-v2-${{ hashFiles('requirements.txt') }}
```

### Dependency Installation Failures

Some packages may fail on CI:

```yaml
- name: Install dependencies
  run: |
    pip install -r requirements.txt || true
  continue-on-error: true
```

### Viewing Logs

Access logs:
1. Go to Actions tab in GitHub
2. Select workflow run
3. Click on job
4. View step logs

Download logs:
```bash
gh run view <run-id> --log
```

## Best Practices

### 1. Keep Builds Fast

- Use caching
- Run tests in parallel
- Split long jobs

### 2. Fail Fast

```yaml
strategy:
  fail-fast: true  # Stop on first failure
```

### 3. Matrix Testing

Test on multiple environments:

```yaml
strategy:
  matrix:
    python-version: ['3.9', '3.10', '3.11']
    os: [ubuntu-latest, macos-latest]
```

### 4. Artifact Management

Save important artifacts:

```yaml
- name: Upload logs
  if: always()
  uses: actions/upload-artifact@v3
  with:
    name: test-logs
    path: logs/
```

### 5. Status Badges

Add status badge to README:

```markdown
![CI Status](https://github.com/user/repo/workflows/Integration%20Tests/badge.svg)
```

## Monitoring

### GitHub Actions Dashboard

Monitor:
- Build success rate
- Average build time
- Failed test trends
- Resource usage

### Metrics to Track

1. **Build Duration**: Target <10 minutes
2. **Success Rate**: Target >95%
3. **Test Coverage**: Target >80%
4. **Flaky Tests**: Target <5%

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest CI/CD Integration](https://docs.pytest.org/en/stable/how-to/usage.html)
- [Codecov Documentation](https://docs.codecov.com/)

## Support

For CI/CD issues:
- Check workflow logs
- Review recent changes
- Consult team documentation
- Open GitHub issue if needed
