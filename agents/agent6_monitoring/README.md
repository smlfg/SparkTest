# Agent 6: System Monitoring And Metrics Collection Agent

## Overview
System monitoring and metrics collection agent.

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
- Main port: 8006

## Development

### Running Locally
```bash
python main.py
```

### Running with Docker
```bash
docker build -t agent6_monitoring -f Dockerfile ../..
docker run -p 8006:8006 --gpus all agent6_monitoring
```

### Testing
```bash
curl http://localhost:8006/health
```

## Environment Variables
- `LOG_LEVEL`: Logging level (default: INFO)
- `ENVIRONMENT`: Environment name (default: production)
- `CONFIG_PATH`: Path to configuration file (default: /app/config.yaml)
