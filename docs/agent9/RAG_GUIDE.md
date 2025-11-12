# RAG AI Workbench - Complete Guide

Retrieval-Augmented Generation (RAG) pipeline using LangChain and Chroma vector database.

## Overview

The RAG AI Workbench provides a production-ready RAG system that combines:
- **LangChain** for orchestration
- **Chroma** for vector storage
- **BAAI/bge-large-en-v1.5** embeddings
- **Agent 4/5** for LLM inference

## Architecture

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│     RAG AI Workbench (Port 3000)    │
├─────────────────────────────────────┤
│                                     │
│  1. Query Embedding                 │
│     └─> BAAI/bge-large-en-v1.5     │
│                                     │
│  2. Vector Search                   │
│     └─> Chroma Vector DB            │
│                                     │
│  3. Context Retrieval               │
│     └─> Top-K Documents             │
│                                     │
│  4. Answer Generation               │
│     └─> Agent 4/5 LLM               │
│                                     │
└─────────────────────────────────────┘
```

## Quick Start

### 1. Start the Service

```bash
# Using Docker Compose
docker-compose up -d rag-workbench

# Or run directly
cd playbooks/rag_ai_workbench
python server.py
```

### 2. Verify Service Health

```bash
curl http://localhost:3000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "document_count": 0,
  "vector_store": "Chroma"
}
```

### 3. Ingest Documents

```bash
# Ingest a single document
curl -X POST http://localhost:3000/api/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Apache Spark is a unified analytics engine for large-scale data processing.",
    "metadata": {
      "source": "spark_docs",
      "category": "overview"
    }
  }'
```

Response:
```json
{
  "status": "success",
  "chunks_created": 1,
  "message": "Document ingested successfully"
}
```

### 4. Query the RAG System

```bash
# FUNCTIONAL TEST ENDPOINT
curl -X POST http://localhost:3000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Apache Spark?"
  }'
```

Expected response format:
```json
{
  "answer": "Apache Spark is a unified analytics engine...",
  "sources": [
    {
      "content": "Apache Spark is...",
      "metadata": {
        "source": "spark_docs",
        "category": "overview"
      },
      "score": 0.95
    }
  ],
  "metadata": {
    "num_sources": 3,
    "vector_store": "Chroma",
    "embedding_model": "BAAI/bge-large-en-v1.5"
  }
}
```

## API Reference

### POST /api/rag/query

**Main RAG query endpoint** (used for functional tests)

**Request:**
```json
{
  "question": "string",
  "top_k": 5,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "answer": "string",
  "sources": [
    {
      "content": "string",
      "metadata": {},
      "score": 0.95
    }
  ],
  "metadata": {}
}
```

### POST /api/ingest

Ingest a single document.

**Request:**
```json
{
  "content": "string",
  "metadata": {}
}
```

### POST /api/ingest/batch

Ingest multiple documents.

**Request:**
```json
{
  "documents": [
    {
      "content": "string",
      "metadata": {}
    }
  ]
}
```

### GET /api/stats

Get system statistics.

**Response:**
```json
{
  "document_count": 42,
  "vector_store": "Chroma",
  "embedding_model": "BAAI/bge-large-en-v1.5",
  "langchain_available": true
}
```

## Technical Details

### Embedding Model

**BAAI/bge-large-en-v1.5**
- 1024-dimensional embeddings
- State-of-the-art performance on MTEB benchmark
- Normalized embeddings for cosine similarity

### Vector Database

**Chroma**
- Open-source vector database
- Persistent storage at `/app/data/chroma`
- Supports similarity search with scores
- Collection name: `rag_documents`

### Text Splitting

**RecursiveCharacterTextSplitter**
- Chunk size: 500 characters
- Chunk overlap: 50 characters
- Preserves semantic boundaries

### LLM Integration

Connects to **Agent 4/5** inference service:
- Endpoint: `http://agent4:8000/generate`
- Model: GPT-4 (configurable)
- Temperature: 0.7 (configurable)

## Configuration

### Environment Variables

```bash
# Agent 4/5 inference URL
AGENT_INFERENCE_URL=http://agent4:8000

# Embedding model
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5

# LLM model
LLM_MODEL=gpt-4

# Vector store path
CHROMA_PERSIST_DIR=/app/data/chroma

# Server settings
RAG_PORT=3000
RAG_TOP_K=5
RAG_CHUNK_SIZE=500
```

### Playbook Configuration

See `playbooks/rag_ai_workbench/config.yaml`:

```yaml
playbook:
  name: "rag-ai-workbench"
  agent: "agent9"
  dependencies: ["agent4", "agent5"]
  ports: [3000]

  resources:
    memory: "8G"
    cpu: "4.0"
```

## Usage Examples

### Python Client

```python
import aiohttp
import asyncio

async def query_rag(question: str):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:3000/api/rag/query",
            json={"question": question, "top_k": 5}
        ) as response:
            return await response.json()

# Use it
result = asyncio.run(query_rag("What is Spark?"))
print(result["answer"])
```

### Batch Ingestion

```python
documents = [
    {
        "content": "Spark SQL is a module for structured data processing.",
        "metadata": {"source": "spark_sql_docs"}
    },
    {
        "content": "MLlib is Spark's machine learning library.",
        "metadata": {"source": "mllib_docs"}
    }
]

async with aiohttp.ClientSession() as session:
    async with session.post(
        "http://localhost:3000/api/ingest/batch",
        json={"documents": documents}
    ) as response:
        result = await response.json()
        print(f"Ingested {result['documents_processed']} documents")
```

### Advanced Querying

```python
# Query with custom parameters
query = {
    "question": "How does Spark handle fault tolerance?",
    "top_k": 10,  # Retrieve more documents
    "temperature": 0.3  # More focused answers
}

async with aiohttp.ClientSession() as session:
    async with session.post(
        "http://localhost:3000/api/rag/query",
        json=query
    ) as response:
        result = await response.json()

        print(f"Answer: {result['answer']}")
        print(f"\nSources ({len(result['sources'])}):")
        for i, source in enumerate(result['sources'], 1):
            print(f"\n{i}. Score: {source['score']:.3f}")
            print(f"   {source['content'][:100]}...")
```

## Integration with Agent 5

The RAG system connects to Agent 5 (inference) for:

1. **Embeddings**: Generate vector representations
2. **LLM Inference**: Generate answers from context

```python
# Agent 5 inference endpoint
INFERENCE_URL = "http://agent4:8000"

# Embedding request
POST /embeddings
{
  "text": "document content",
  "model": "BAAI/bge-large-en-v1.5"
}

# Generation request
POST /generate
{
  "prompt": "Answer based on context: ...",
  "model": "gpt-4",
  "max_tokens": 500,
  "temperature": 0.7
}
```

## Performance Tuning

### Chunk Size Optimization

```python
# For shorter documents (tweets, messages)
chunk_size = 200
chunk_overlap = 20

# For longer documents (articles, papers)
chunk_size = 1000
chunk_overlap = 100
```

### Top-K Selection

```python
# Quick answers (faster, less context)
top_k = 3

# Comprehensive answers (slower, more context)
top_k = 10
```

### Caching Strategy

```python
# Enable Redis caching for embeddings
REDIS_URL = "redis://localhost:6379/0"
CACHE_EMBEDDINGS = True
CACHE_TTL = 3600  # 1 hour
```

## Monitoring

### Metrics

Exposed at `/metrics`:

```
# Document count
rag_documents_total 1234

# Query count
rag_queries_total 567

# Average query time
rag_query_duration_seconds 0.234

# Vector search time
rag_vector_search_duration_seconds 0.045

# LLM generation time
rag_generation_duration_seconds 0.189
```

### Logging

Structured JSON logs:

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "agent": "agent9",
  "playbook": "rag-ai-workbench",
  "message": "Query processed",
  "query": "What is Spark?",
  "response_time_ms": 234,
  "num_sources": 5
}
```

## Troubleshooting

### Issue: Slow queries

**Solution:**
- Reduce `top_k` value
- Optimize chunk size
- Add Redis caching
- Scale Agent 4/5 inference

### Issue: Low quality answers

**Solution:**
- Increase `top_k` for more context
- Improve document quality
- Adjust chunk size and overlap
- Use better embedding model

### Issue: High memory usage

**Solution:**
- Reduce batch size for ingestion
- Clear old conversations
- Use smaller embedding model
- Add memory limits in Docker

### Issue: Vector store errors

**Solution:**
```bash
# Reset Chroma database
rm -rf /app/data/chroma/*

# Re-ingest documents
python scripts/reingest_documents.py
```

## Production Deployment

### Scaling

```yaml
# docker-compose.yml
services:
  rag-workbench:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 8G
          cpus: '4.0'
```

### High Availability

```yaml
# Load balancer configuration
upstream rag_backend {
    server rag-workbench-1:3000;
    server rag-workbench-2:3000;
    server rag-workbench-3:3000;
}
```

### Backup & Recovery

```bash
# Backup Chroma database
tar -czf chroma_backup_$(date +%Y%m%d).tar.gz /app/data/chroma/

# Restore from backup
tar -xzf chroma_backup_20240101.tar.gz -C /app/data/
```

## API Testing

### Functional Test (from checklist)

```bash
# Test RAG query endpoint
curl http://localhost:3000/api/rag/query \
  -d '{"question":"test"}'

# Expected response format:
{
  "answer": "string",
  "sources": ["array"]
}
```

### Integration Tests

```python
import pytest
import aiohttp

@pytest.mark.asyncio
async def test_rag_query():
    async with aiohttp.ClientSession() as session:
        # Ingest test document
        await session.post(
            "http://localhost:3000/api/ingest",
            json={"content": "Test document"}
        )

        # Query
        async with session.post(
            "http://localhost:3000/api/rag/query",
            json={"question": "test"}
        ) as response:
            result = await response.json()

            assert "answer" in result
            assert "sources" in result
            assert isinstance(result["sources"], list)
```

## Resources

- **LangChain Docs**: https://python.langchain.com/
- **Chroma Docs**: https://docs.trychroma.com/
- **BAAI BGE Model**: https://huggingface.co/BAAI/bge-large-en-v1.5
- **API Docs**: http://localhost:3000/docs

## Support

- **Health Check**: `curl http://localhost:3000/health`
- **Stats**: `curl http://localhost:3000/api/stats`
- **Logs**: `docker-compose logs -f rag-workbench`
