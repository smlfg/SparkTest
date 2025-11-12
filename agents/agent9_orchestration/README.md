# Agent 9: Workflow Orchestration Agent

## Overview
Workflow orchestration agent.

## Features
- TODO: Add specific features

## Endpoints

### Health Check
```
GET /health
```
Returns the health status of the agent.

### Information
```
GET /info
```
Returns agent configuration and details.

### Status
```
GET /status
```
Returns current agent status including resource usage.

## Configuration
Configuration is loaded from `config.yaml`. See `shared/config_schema.yaml` for the complete schema.

## Dependencies
- None (base agent)

## GPU Requirements
- Requires: Yes
- GPU Count: 1

## Ports
- Main port: 8009

## Development

### Running Locally
```bash
python main.py
```

### Running with Docker
```bash
docker build -t agent9_orchestration -f Dockerfile ../..
docker run -p 8009:8009 --gpus all agent9_orchestration
```

### Testing
```bash
curl http://localhost:8009/health
```

## Environment Variables
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENVIRONMENT`: Environment name (default: production)
- `CONFIG_PATH`: Path to configuration file (default: /app/config.yaml)
