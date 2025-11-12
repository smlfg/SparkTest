# Agent 9 Tests

Test suite for Agent 9: Application Layer according to `agent9_checklist.yaml`.

## Test Structure

```
tests/
├── README.md                    # This file
├── functional_tests.sh          # Functional tests (bash script)
├── test_rag_application.py      # RAG unit tests
├── test_chatbot.py              # Chatbot unit tests
├── unit/                        # Unit tests
└── integration/                 # Integration tests
```

## Functional Tests (Checklist Compliance)

The functional tests validate requirements from `agent9_checklist.yaml`.

### RAG Application

**Test:**
```bash
curl http://localhost:3000/api/rag/query -d '{"question":"test"}'
```

**Expected JSON:**
```json
{
  "answer": "string",
  "sources": ["array"]
}
```

### Multi-Agent Chatbot

**Test:**
```bash
curl http://localhost:8080/chat -d '{"message":"hello"}'
```

**Expected:** HTTP 200

## Running Tests

### All Functional Tests

```bash
# Run functional test suite
./tests/functional_tests.sh
```

Expected output:
```
==================================
Agent 9 Functional Tests
==================================

1. RAG Application Tests
------------------------
Waiting for RAG service... ready
Testing: RAG query endpoint ... ✓ PASSED
Testing: RAG sources validation ... ✓ PASSED

2. Multi-Agent Chatbot Tests
----------------------------
Waiting for Chatbot service... ready
Testing: Chatbot endpoint ... ✓ PASSED
Testing: Chatbot conversation tracking ... ✓ PASSED

==================================
Test Results
==================================
Passed: 4
Failed: 0

All tests passed!
```

### Unit Tests

```bash
# Run all unit tests
pytest tests/ -v

# Run specific test file
pytest tests/test_rag_application.py -v
pytest tests/test_chatbot.py -v

# Run with coverage
pytest tests/ --cov=playbooks --cov-report=html

# Run specific test
pytest tests/test_rag_application.py::TestRAGApplication::test_embedding_model -v
```

### Integration Tests

```bash
# Run integration tests
pytest tests/integration/ -v

# Run with Docker Compose
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## Test Requirements

### Python Dependencies

```bash
pip install pytest pytest-asyncio pytest-cov
```

### Services Running

Before running tests, ensure services are running:

```bash
# Start all services
docker-compose up -d

# Wait for services to be healthy
python shared/health_check.py --agent9
```

## Technical Requirements Tests

### RAG Application

Tests verify:

1. **Framework**: LangChain or LlamaIndex ✓
   ```python
   # test_rag_application.py
   test_langchain_integration()
   ```

2. **Vector DB**: Chroma or Milvus ✓
   ```python
   # test_rag_application.py
   test_vector_db_options()
   ```

3. **Embedding Model**: BAAI/bge-large-en-v1.5 ✓
   ```python
   # test_rag_application.py
   test_embedding_model()
   ```

4. **API Endpoint**: `/api/rag/query` ✓
   ```python
   # test_rag_application.py
   test_rag_query_endpoint()
   ```

### Multi-Agent Chatbot

Tests verify:

1. **Agent Initialization**: 5 specialized agents ✓
   ```python
   # test_chatbot.py
   test_agent_initialization()
   ```

2. **API Endpoint**: `/chat` returns HTTP 200 ✓
   ```python
   # test_chatbot.py
   test_chat_endpoint()
   ```

3. **Conversation Management**: Context tracking ✓
   ```python
   # test_chatbot.py
   test_conversation_continuity()
   ```

## Integration Points Tests

### Agent 4/5 Integration

Tests verify integration with inference endpoints:

```python
# test_rag_application.py
test_rag_query_format()

# test_chatbot.py
test_llm_connection()
```

## Test Data

### Sample Documents (RAG)

```python
sample_docs = [
    {
        "content": "Apache Spark is a unified analytics engine.",
        "metadata": {"source": "spark_docs"}
    },
    {
        "content": "MLlib is Spark's machine learning library.",
        "metadata": {"source": "mllib_docs"}
    }
]
```

### Sample Conversations (Chatbot)

```python
sample_conversations = [
    {
        "message": "What is Apache Spark?",
        "expected_topics": ["analytics", "distributed", "processing"]
    },
    {
        "message": "How does Spark handle fault tolerance?",
        "expected_topics": ["RDD", "lineage", "recompute"]
    }
]
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Agent 9 Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov

      - name: Run unit tests
        run: pytest tests/ -v --cov

      - name: Start services
        run: docker-compose up -d

      - name: Wait for services
        run: sleep 60

      - name: Run functional tests
        run: ./tests/functional_tests.sh

      - name: Cleanup
        run: docker-compose down
```

### Jenkins

```groovy
pipeline {
    agent any

    stages {
        stage('Test') {
            steps {
                sh 'pip install -r requirements.txt'
                sh 'pytest tests/ -v --cov'
            }
        }

        stage('Functional Tests') {
            steps {
                sh 'docker-compose up -d'
                sh 'sleep 60'
                sh './tests/functional_tests.sh'
            }
        }

        stage('Cleanup') {
            steps {
                sh 'docker-compose down'
            }
        }
    }
}
```

## Test Coverage

Target coverage: **>80%**

```bash
# Generate coverage report
pytest tests/ --cov=playbooks --cov-report=term --cov-report=html

# View HTML report
open htmlcov/index.html
```

## Troubleshooting

### Tests Fail to Connect

```bash
# Check services are running
docker-compose ps

# Check health
python shared/health_check.py --agent9

# Check logs
docker-compose logs rag-workbench
docker-compose logs multi-agent-chatbot
```

### Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/app:$PYTHONPATH

# Or run from project root
cd /home/user/SparkTest
pytest tests/ -v
```

### Timeout Errors

```bash
# Increase timeout in tests
PYTEST_TIMEOUT=300 pytest tests/ -v

# Or in functional_tests.sh, increase sleep time
for i in {1..60}; do  # Increased from 30
```

## Writing New Tests

### Unit Test Template

```python
import pytest
import asyncio

class TestNewFeature:
    """Tests for new feature"""

    @pytest.mark.asyncio
    async def test_feature(self):
        """Test feature functionality"""
        # Arrange
        service = YourService()

        # Act
        result = await service.method()

        # Assert
        assert result is not None
        assert "expected_field" in result
```

### Functional Test Template

```bash
# Add to functional_tests.sh
test_endpoint \
    "Feature name" \
    "http://localhost:PORT/endpoint" \
    '{"param":"value"}' \
    '.expected_field'
```

## Performance Tests

```python
@pytest.mark.benchmark
def test_rag_query_performance(benchmark):
    """Test RAG query performance"""
    result = benchmark(
        lambda: asyncio.run(rag_service.query("test"))
    )
    assert result is not None
```

## Load Tests

```bash
# Using Apache Bench
ab -n 1000 -c 10 \
  -p query.json \
  -T application/json \
  http://localhost:3000/api/rag/query

# Using Locust
locust -f tests/load_tests.py --host=http://localhost:3000
```

## Documentation Tests

All guides in `docs/agent9/` should have corresponding tests:

- `RAG_GUIDE.md` → `test_rag_application.py`
- `CHATBOT_GUIDE.md` → `test_chatbot.py`

## Support

- **Test Issues**: Check logs with `docker-compose logs -f`
- **Coverage Reports**: `pytest --cov-report=html`
- **CI/CD**: See `.github/workflows/` for automation
