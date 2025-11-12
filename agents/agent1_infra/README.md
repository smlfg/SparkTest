# Agent 1: Infrastructure Management

## Overview
The Infrastructure Management Agent handles resource allocation, infrastructure monitoring, and system management tasks for the DGX Spark platform.

## Features
- Resource allocation and management
- Infrastructure health monitoring
- GPU resource tracking
- System metrics collection

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
- Main port: 8001

## Development

### Running Locally
```bash
python main.py
```

### Running with Docker
```bash
docker build -t agent1_infra -f Dockerfile ../..
docker run -p 8001:8001 --gpus all agent1_infra
```

### Testing
```bash
curl http://localhost:8001/health
```

## Environment Variables
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENVIRONMENT`: Environment name (default: production)
- `CONFIG_PATH`: Path to configuration file (default: /app/config.yaml)
