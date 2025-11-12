"""
Agent 4: Data Storage And Management Agent
Data storage and management agent
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import sys
import os
from datetime import datetime

# Add shared directory to path
sys.path.insert(0, '/app')

from shared.health_check import create_health_endpoint
from shared.utils.logger import setup_logger
from shared.utils.config_loader import load_config, validate_config

# Initialize logger
logger = setup_logger(__name__, agent_name="agent4_storage")

# Load configuration
config_path = os.getenv("CONFIG_PATH", "/app/config.yaml")
try:
    config = load_config(config_path)
    validate_config(config)
    logger.info("Configuration loaded and validated successfully")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")
    sys.exit(1)

# Initialize FastAPI app
app = FastAPI(
    title="Agent 4: Data Storage And Management Agent",
    description="Data storage and management agent",
    version="1.0.0"
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "agent4_storage",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "agent": "agent4_storage",
        "description": "Data storage and management agent",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "status": "/status"
        }
    }


@app.get("/info")
async def info():
    """Get agent information"""
    return {
        "agent": "agent4_storage",
        "config": config.get("playbook", {}),
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/status")
async def status():
    """Get agent status"""
    return {
        "agent": "agent4_storage",
        "status": "running",
        "uptime": "N/A",  # TODO: Implement uptime tracking
        "resources": {
            "gpu_available": True,  # TODO: Implement GPU check
            "memory_usage": "N/A",  # TODO: Implement memory tracking
            "cpu_usage": "N/A"  # TODO: Implement CPU tracking
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    logger.info("Agent 4 (Data Storage And Management Agent) is starting up...")
    logger.info(f"Configuration: {config.get('playbook', {}).get('name')}")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event handler"""
    logger.info("Agent 4 (Data Storage And Management Agent) is shutting down...")


if __name__ == "__main__":
    import uvicorn

    port = config.get("playbook", {}).get("ports", [8004])[0]
    logger.info(f"Starting agent on port {port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
