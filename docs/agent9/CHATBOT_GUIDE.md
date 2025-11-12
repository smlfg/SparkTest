# Multi-Agent Chatbot - Complete Guide

Orchestrated multi-agent conversational system with specialized agent roles.

## Overview

The Multi-Agent Chatbot provides an intelligent conversation system powered by:
- **5 Specialized Agents** with distinct roles
- **Coordinator Agent** for orchestration
- **Agent 4/5** for LLM inference
- **Context Management** for conversation history

## Architecture

```
User Message
    │
    ▼
┌────────────────────────────────────────┐
│  Multi-Agent Chatbot (Port 8080)      │
├────────────────────────────────────────┤
│                                        │
│  ┌──────────────────────────────┐    │
│  │  Coordinator Agent            │    │
│  │  - Analyzes request           │    │
│  │  - Routes to specialists      │    │
│  │  - Synthesizes responses      │    │
│  └──────────────────────────────┘    │
│            │                           │
│            ├─────────┬─────────┬──────┤
│            ▼         ▼         ▼      │
│  ┌──────────┐ ┌──────────┐ ┌────────┐│
│  │Researcher│ │ Analyst  │ │ Writer ││
│  │  Agent   │ │  Agent   │ │ Agent  ││
│  └──────────┘ └──────────┘ └────────┘│
│       ▲              ▲                 │
│       └──────────────┘                 │
│    Agent 4/5 LLM Inference             │
└────────────────────────────────────────┘
```

## Agent Roles

### 1. Coordinator Agent
- **Purpose**: Orchestrates multi-agent collaboration
- **Skills**: Task decomposition, agent selection, response synthesis
- **When Used**: All complex queries requiring multiple perspectives

### 2. Researcher Agent
- **Purpose**: Conducts research and gathers information
- **Skills**: Information retrieval, synthesis, fact-checking
- **When Used**: Questions requiring factual information

### 3. Analyst Agent
- **Purpose**: Analyzes data and provides insights
- **Skills**: Data analysis, pattern recognition, interpretation
- **When Used**: Questions requiring analysis or insights

### 4. Writer Agent
- **Purpose**: Creates well-written content
- **Skills**: Content creation, editing, formatting
- **When Used**: Requests for written content or summaries

### 5. Critic Agent
- **Purpose**: Reviews and provides constructive feedback
- **Skills**: Critical analysis, quality assessment, improvement suggestions
- **When Used**: Review requests or quality checks

## Quick Start

### 1. Start the Service

```bash
# Using Docker Compose
docker-compose up -d multi-agent-chatbot

# Or run directly
cd playbooks/multi_agent_chatbot
python server.py
```

### 2. Verify Service Health

```bash
curl http://localhost:8080/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "num_agents": 5,
  "active_conversations": 0
}
```

### 3. Send a Message

```bash
# FUNCTIONAL TEST ENDPOINT
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "hello"
  }'
```

Expected response (HTTP 200):
```json
{
  "response": "Hello! I'm a multi-agent conversational system...",
  "conversation_id": "conv_abc123",
  "metadata": {
    "processing_time": 1.23,
    "num_agents": 5,
    "coordination_used": true,
    "message_count": 2
  }
}
```

## API Reference

### POST /chat

**Main chat endpoint** (used for functional tests)

**Request:**
```json
{
  "message": "string",
  "conversation_id": "optional-string",
  "use_coordination": true
}
```

**Response:**
```json
{
  "response": "string",
  "conversation_id": "string",
  "metadata": {
    "processing_time": 1.23,
    "num_agents": 5,
    "coordination_used": true,
    "message_count": 2
  }
}
```

**HTTP Status**: `200 OK`

### GET /conversations

List all active conversations.

**Response:**
```json
{
  "conversations": [
    {
      "conversation_id": "conv_abc123",
      "message_count": 10,
      "created_at": "2024-01-01T00:00:00"
    }
  ]
}
```

### GET /conversations/{conversation_id}

Get conversation history.

**Response:**
```json
{
  "conversation_id": "conv_abc123",
  "message_count": 10,
  "created_at": "2024-01-01T00:00:00",
  "messages": [
    {
      "id": "msg_001",
      "type": "user_input",
      "sender": "user",
      "content": "Hello",
      "timestamp": "2024-01-01T00:00:00"
    },
    {
      "id": "msg_002",
      "type": "agent_response",
      "sender": "assistant",
      "content": "Hello! How can I help?",
      "timestamp": "2024-01-01T00:00:01"
    }
  ]
}
```

### DELETE /conversations/{conversation_id}

Delete a conversation.

**Response:**
```json
{
  "status": "success",
  "message": "Conversation conv_abc123 deleted"
}
```

### GET /agents

List all available agents.

**Response:**
```json
{
  "agents": [
    {
      "id": "coordinator",
      "role": "coordinator",
      "description": "Orchestrates multi-agent collaboration",
      "skills": ["orchestration", "task_decomposition", "synthesis"]
    },
    {
      "id": "researcher",
      "role": "researcher",
      "description": "Conducts research and gathers information",
      "skills": ["information_retrieval", "synthesis", "fact_checking"]
    }
  ]
}
```

## Usage Examples

### Python Client

```python
import aiohttp
import asyncio

async def chat(message: str, conversation_id: str = None):
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8080/chat",
            json={
                "message": message,
                "conversation_id": conversation_id,
                "use_coordination": True
            }
        ) as response:
            return await response.json()

# Start a conversation
result = asyncio.run(chat("Explain how Apache Spark works"))
print(f"Response: {result['response']}")
print(f"Conversation ID: {result['conversation_id']}")

# Continue the conversation
result2 = asyncio.run(chat(
    "Tell me more about RDDs",
    conversation_id=result['conversation_id']
))
print(f"Response: {result2['response']}")
```

### JavaScript Client

```javascript
async function chat(message, conversationId = null) {
  const response = await fetch('http://localhost:8080/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      use_coordination: true
    })
  });
  return await response.json();
}

// Use it
chat("What is machine learning?")
  .then(result => console.log(result.response));
```

### cURL Examples

```bash
# Simple chat
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Chat with specific conversation
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Continue our previous discussion",
    "conversation_id": "conv_abc123"
  }'

# Chat without coordination (single agent)
curl -X POST http://localhost:8080/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quick question",
    "use_coordination": false
  }'
```

## Conversation Flow

### Single-Agent Mode (use_coordination: false)

```
User → Researcher Agent → Response
```

Fast, simple queries.

### Multi-Agent Mode (use_coordination: true)

```
User Message
    │
    ▼
Coordinator Agent
    │
    ├─> Researcher Agent  ──┐
    │                        │
    ├─> Analyst Agent    ────┤
    │                        │
    └─> Writer Agent     ────┤
                             │
                             ▼
                    Coordinator Synthesis
                             │
                             ▼
                          Response
```

Complex queries benefit from multiple perspectives.

## Configuration

### Environment Variables

```bash
# Agent 4/5 inference URL
AGENT_INFERENCE_URL=http://agent4:8000

# LLM model
LLM_MODEL=gpt-4

# Number of specialized agents
NUM_AGENTS=5

# Enable multi-agent coordination
COORDINATION_ENABLED=true

# Max conversation history to maintain
MAX_CONVERSATION_HISTORY=50

# Server settings
CHATBOT_PORT=8080
```

### Playbook Configuration

See `playbooks/multi_agent_chatbot/config.yaml`:

```yaml
playbook:
  name: "multi-agent-chatbot"
  agent: "agent9"
  dependencies: ["agent4", "agent5"]
  ports: [8080]

  docker:
    environment:
      NUM_AGENTS: "5"
      COORDINATION_ENABLED: "true"

  resources:
    memory: "6G"
    cpu: "4.0"

  scaling:
    replicas: 1
    autoscaling:
      enabled: true
      min_replicas: 1
      max_replicas: 10
      target_cpu_percent: 75
```

## Integration with Agent 4/5

The chatbot connects to Agent 4/5 for LLM inference:

```python
# Inference endpoint
POST http://agent4:8000/generate

# Request
{
  "prompt": "You are a researcher agent. Answer: ...",
  "model": "gpt-4",
  "max_tokens": 500,
  "temperature": 0.7
}

# Response
{
  "text": "Generated response...",
  "model": "gpt-4",
  "tokens": 234
}
```

## Advanced Features

### Custom Agent Roles

Add new agent types:

```python
from playbooks.multi_agent_chatbot.orchestration import Agent, AgentCapability, AgentRole

# Define new role
class ExecutorAgent(Agent):
    def __init__(self):
        capability = AgentCapability(
            role=AgentRole.EXECUTOR,
            description="Executes tasks and reports results",
            skills=["task_execution", "reporting", "verification"]
        )
        super().__init__("executor", capability)

# Register with chatbot
chatbot.agents["executor"] = ExecutorAgent()
```

### Conversation Context Management

```python
# Get conversation context
context = chatbot.get_conversation("conv_abc123")

# Access message history
for message in context.messages:
    print(f"{message.sender}: {message.content}")

# Get metadata
print(f"Created: {context.created_at}")
print(f"Messages: {len(context.messages)}")
```

### Streaming Responses

```python
from fastapi.responses import StreamingResponse

@app.post("/chat/stream")
async def chat_stream(message: ChatMessage):
    async def generate():
        response = await chatbot.chat(
            message.message,
            message.conversation_id
        )
        # Stream response word by word
        for word in response["response"].split():
            yield f"data: {word}\n\n"
            await asyncio.sleep(0.1)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

## Performance Tuning

### Parallelizing Agent Calls

```python
# Process multiple agents in parallel
async def parallel_agent_processing(message, agents):
    tasks = [
        agent.process(message, context)
        for agent in agents
    ]
    responses = await asyncio.gather(*tasks)
    return responses
```

### Caching Responses

```python
import redis
from functools import lru_cache

# Redis cache for responses
redis_client = redis.Redis(host='localhost', port=6379)

def cache_response(key, value, ttl=3600):
    redis_client.setex(key, ttl, value)

def get_cached_response(key):
    return redis_client.get(key)
```

### Request Batching

```python
# Batch multiple messages to Agent 4/5
async def batch_generate(prompts: List[str]):
    async with aiohttp.ClientSession() as session:
        tasks = [
            session.post(
                "http://agent4:8000/generate",
                json={"prompt": prompt}
            )
            for prompt in prompts
        ]
        responses = await asyncio.gather(*tasks)
        return [await r.json() for r in responses]
```

## Monitoring

### Metrics

Exposed at `/metrics`:

```
# Total conversations
chatbot_conversations_total 123

# Total messages
chatbot_messages_total 456

# Average response time
chatbot_response_time_seconds 1.23

# Active conversations
chatbot_active_conversations 5

# Agent usage
chatbot_agent_calls_total{agent="researcher"} 78
chatbot_agent_calls_total{agent="analyst"} 45
```

### Logging

Structured JSON logs:

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "agent": "agent9",
  "playbook": "multi-agent-chatbot",
  "message": "Message processed",
  "conversation_id": "conv_abc123",
  "response_time_ms": 1234,
  "agents_used": ["coordinator", "researcher", "analyst"]
}
```

## Troubleshooting

### Issue: Slow responses

**Solution:**
- Disable coordination for simple queries
- Reduce number of agents called
- Add caching layer
- Scale Agent 4/5 inference

### Issue: Context loss

**Solution:**
```python
# Increase context window
MAX_CONVERSATION_HISTORY = 100

# Or use conversation summarization
async def summarize_history(context):
    # Summarize old messages
    summary = await llm.summarize(context.messages[:-10])
    context.metadata["summary"] = summary
```

### Issue: Inconsistent responses

**Solution:**
- Lower LLM temperature (0.3-0.5)
- Add response validation
- Use structured outputs
- Implement response caching

### Issue: High memory usage

**Solution:**
```bash
# Limit conversation history
MAX_CONVERSATION_HISTORY=20

# Clear old conversations
python scripts/cleanup_conversations.py --older-than 24h

# Reduce agent count
NUM_AGENTS=3
```

## Production Deployment

### Horizontal Scaling

```yaml
# docker-compose.yml
services:
  multi-agent-chatbot:
    deploy:
      replicas: 5
      resources:
        limits:
          memory: 6G
          cpus: '4.0'
```

### Load Balancing

```nginx
# nginx.conf
upstream chatbot_backend {
    least_conn;
    server chatbot-1:8080;
    server chatbot-2:8080;
    server chatbot-3:8080;
}

server {
    location /chat {
        proxy_pass http://chatbot_backend;
    }
}
```

### Session Affinity

```python
# Use consistent hashing for conversation routing
from consistent_hash import ConsistentHash

ring = ConsistentHash(['chatbot-1', 'chatbot-2', 'chatbot-3'])

def route_conversation(conversation_id: str):
    return ring.get_node(conversation_id)
```

## API Testing

### Functional Test (from checklist)

```bash
# Test chat endpoint
curl http://localhost:8080/chat -d '{"message":"hello"}'

# Expected: HTTP 200 status code
```

### Integration Tests

```python
import pytest
import aiohttp

@pytest.mark.asyncio
async def test_chat():
    async with aiohttp.ClientSession() as session:
        # Send message
        async with session.post(
            "http://localhost:8080/chat",
            json={"message": "hello"}
        ) as response:
            assert response.status == 200

            result = await response.json()
            assert "response" in result
            assert "conversation_id" in result
            assert "metadata" in result

@pytest.mark.asyncio
async def test_conversation_continuity():
    async with aiohttp.ClientSession() as session:
        # First message
        async with session.post(
            "http://localhost:8080/chat",
            json={"message": "My name is Alice"}
        ) as response:
            result1 = await response.json()
            conv_id = result1["conversation_id"]

        # Second message
        async with session.post(
            "http://localhost:8080/chat",
            json={
                "message": "What's my name?",
                "conversation_id": conv_id
            }
        ) as response:
            result2 = await response.json()
            assert "Alice" in result2["response"]
```

## Resources

- **LangChain Agents**: https://python.langchain.com/docs/modules/agents/
- **Multi-Agent Systems**: https://en.wikipedia.org/wiki/Multi-agent_system
- **API Docs**: http://localhost:8080/docs

## Support

- **Health Check**: `curl http://localhost:8080/health`
- **Agent Info**: `curl http://localhost:8080/agents`
- **Logs**: `docker-compose logs -f multi-agent-chatbot`
