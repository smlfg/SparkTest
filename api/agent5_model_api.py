#!/usr/bin/env python3
"""
Agent 5 Model Management API
Unified interface for managing Ollama and NVIDIA NIM models
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

try:
    import aiohttp
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import JSONResponse, StreamingResponse
    from pydantic import BaseModel, Field
    import uvicorn
except ImportError:
    print("Installing required packages...")
    os.system("pip install fastapi uvicorn aiohttp pydantic")
    import aiohttp
    from fastapi import FastAPI, HTTPException, Query
    from fastapi.responses import JSONResponse, StreamingResponse
    from pydantic import BaseModel, Field
    import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Model Registry
MODEL_REGISTRY = {
    "ollama_models": [
        "llama3.1:70b",
        "mistral:7b",
        "codellama:13b",
        "neural-chat:7b",
        "mixtral:8x7b"
    ],
    "nim_endpoints": [
        "nvcr.io/nim/meta/llama-3.1-405b-instruct",
        "nvcr.io/nim/meta/llama-3.1-70b-instruct",
        "nvcr.io/nim/meta/llama-3.1-8b-instruct"
    ]
}


class ModelProvider(str, Enum):
    """Model provider types"""
    OLLAMA = "ollama"
    NIM = "nim"


class ModelStatus(str, Enum):
    """Model deployment status"""
    AVAILABLE = "available"
    LOADING = "loading"
    ERROR = "error"
    UNKNOWN = "unknown"


class ModelInfo(BaseModel):
    """Model information schema"""
    name: str
    provider: ModelProvider
    status: ModelStatus
    size: Optional[str] = None
    modified: Optional[str] = None
    endpoint: Optional[str] = None
    capabilities: List[str] = Field(default_factory=list)


class CompletionRequest(BaseModel):
    """Completion request schema"""
    model: str
    prompt: str
    stream: bool = False
    max_tokens: Optional[int] = 2048
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    provider: Optional[ModelProvider] = None


class ChatMessage(BaseModel):
    """Chat message schema"""
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    """Chat completion request schema"""
    model: str
    messages: List[ChatMessage]
    stream: bool = False
    max_tokens: Optional[int] = 2048
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    provider: Optional[ModelProvider] = None


# Configuration
class Config:
    """API Configuration"""
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    NIM_BASE_URL = os.getenv("NIM_BASE_URL", "http://localhost:8000")
    NGC_API_KEY = os.getenv("NGC_API_KEY", "")
    API_PORT = int(os.getenv("API_PORT", "8888"))
    API_HOST = os.getenv("API_HOST", "0.0.0.0")


# Initialize FastAPI app
app = FastAPI(
    title="Agent 5 Inference Engine API",
    description="Unified API for Ollama and NVIDIA NIM inference",
    version="1.0.0"
)


class ModelManager:
    """Manager for handling model operations"""

    def __init__(self):
        self.config = Config()
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def list_ollama_models(self) -> List[ModelInfo]:
        """List available Ollama models"""
        try:
            session = await self._get_session()
            url = f"{self.config.OLLAMA_BASE_URL}/api/tags"

            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for model in data.get("models", []):
                        models.append(ModelInfo(
                            name=model["name"],
                            provider=ModelProvider.OLLAMA,
                            status=ModelStatus.AVAILABLE,
                            size=model.get("size"),
                            modified=model.get("modified_at"),
                            endpoint=self.config.OLLAMA_BASE_URL,
                            capabilities=["completion", "chat", "embedding"]
                        ))
                    return models
                else:
                    logger.error(f"Failed to list Ollama models: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []

    async def list_nim_models(self) -> List[ModelInfo]:
        """List available NIM models"""
        try:
            session = await self._get_session()
            url = f"{self.config.NIM_BASE_URL}/v1/models"
            headers = {}

            if self.config.NGC_API_KEY:
                headers["Authorization"] = f"Bearer {self.config.NGC_API_KEY}"

            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    for model in data.get("data", []):
                        models.append(ModelInfo(
                            name=model["id"],
                            provider=ModelProvider.NIM,
                            status=ModelStatus.AVAILABLE,
                            endpoint=self.config.NIM_BASE_URL,
                            capabilities=["completion", "chat"]
                        ))
                    return models
                else:
                    logger.error(f"Failed to list NIM models: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Error listing NIM models: {e}")
            return []

    async def pull_ollama_model(self, model_name: str) -> Dict[str, Any]:
        """Pull/download an Ollama model"""
        try:
            session = await self._get_session()
            url = f"{self.config.OLLAMA_BASE_URL}/api/pull"
            payload = {"name": model_name}

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    return {
                        "status": "success",
                        "message": f"Model {model_name} pulled successfully"
                    }
                else:
                    error = await response.text()
                    return {
                        "status": "error",
                        "message": f"Failed to pull model: {error}"
                    }
        except Exception as e:
            logger.error(f"Error pulling Ollama model: {e}")
            return {"status": "error", "message": str(e)}

    async def ollama_completion(self, request: CompletionRequest) -> Dict[str, Any]:
        """Generate completion using Ollama"""
        try:
            session = await self._get_session()
            url = f"{self.config.OLLAMA_BASE_URL}/api/generate"
            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "stream": request.stream,
                "options": {
                    "num_predict": request.max_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p
                }
            }

            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    if request.stream:
                        return response
                    else:
                        data = await response.json()
                        return {
                            "model": request.model,
                            "response": data.get("response", ""),
                            "done": data.get("done", True),
                            "context": data.get("context", [])
                        }
                else:
                    raise HTTPException(status_code=response.status,
                                      detail="Ollama completion failed")
        except Exception as e:
            logger.error(f"Error in Ollama completion: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def nim_completion(self, request: CompletionRequest) -> Dict[str, Any]:
        """Generate completion using NIM"""
        try:
            session = await self._get_session()
            url = f"{self.config.NIM_BASE_URL}/v1/completions"
            headers = {"Content-Type": "application/json"}

            if self.config.NGC_API_KEY:
                headers["Authorization"] = f"Bearer {self.config.NGC_API_KEY}"

            payload = {
                "model": request.model,
                "prompt": request.prompt,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "stream": request.stream
            }

            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    if request.stream:
                        return response
                    else:
                        return await response.json()
                else:
                    raise HTTPException(status_code=response.status,
                                      detail="NIM completion failed")
        except Exception as e:
            logger.error(f"Error in NIM completion: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def chat_completion(self, request: ChatCompletionRequest,
                            provider: ModelProvider) -> Dict[str, Any]:
        """Generate chat completion"""
        try:
            session = await self._get_session()

            if provider == ModelProvider.OLLAMA:
                url = f"{self.config.OLLAMA_BASE_URL}/api/chat"
                payload = {
                    "model": request.model,
                    "messages": [msg.dict() for msg in request.messages],
                    "stream": request.stream,
                    "options": {
                        "num_predict": request.max_tokens,
                        "temperature": request.temperature,
                        "top_p": request.top_p
                    }
                }
                headers = {"Content-Type": "application/json"}
            else:  # NIM
                url = f"{self.config.NIM_BASE_URL}/v1/chat/completions"
                payload = {
                    "model": request.model,
                    "messages": [msg.dict() for msg in request.messages],
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                    "top_p": request.top_p,
                    "stream": request.stream
                }
                headers = {"Content-Type": "application/json"}
                if self.config.NGC_API_KEY:
                    headers["Authorization"] = f"Bearer {self.config.NGC_API_KEY}"

            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    if request.stream:
                        return response
                    else:
                        return await response.json()
                else:
                    raise HTTPException(status_code=response.status,
                                      detail=f"{provider.value} chat completion failed")
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# Initialize manager
manager = ModelManager()


# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Starting Agent 5 Inference Engine API")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await manager.close()
    logger.info("Shutting down Agent 5 Inference Engine API")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Agent 5 Inference Engine",
        "version": "1.0.0",
        "endpoints": {
            "models": "/api/models",
            "completion": "/api/completion",
            "chat": "/api/chat",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/models", response_model=Dict[str, List[ModelInfo]])
async def list_models(provider: Optional[ModelProvider] = None):
    """List all available models"""
    result = {}

    if provider is None or provider == ModelProvider.OLLAMA:
        ollama_models = await manager.list_ollama_models()
        result["ollama"] = ollama_models

    if provider is None or provider == ModelProvider.NIM:
        nim_models = await manager.list_nim_models()
        result["nim"] = nim_models

    return result


@app.get("/api/models/registry")
async def get_model_registry():
    """Get the model registry"""
    return MODEL_REGISTRY


@app.post("/api/models/pull")
async def pull_model(model_name: str = Query(..., description="Model name to pull")):
    """Pull/download a model (Ollama only)"""
    result = await manager.pull_ollama_model(model_name)
    return result


@app.post("/api/completion")
async def create_completion(request: CompletionRequest):
    """Generate text completion"""
    provider = request.provider or ModelProvider.OLLAMA

    if provider == ModelProvider.OLLAMA:
        result = await manager.ollama_completion(request)
    else:
        result = await manager.nim_completion(request)

    return result


@app.post("/api/chat")
async def create_chat_completion(request: ChatCompletionRequest):
    """Generate chat completion"""
    provider = request.provider or ModelProvider.OLLAMA
    result = await manager.chat_completion(request, provider)
    return result


@app.get("/api/providers")
async def list_providers():
    """List configured providers"""
    return {
        "providers": [
            {
                "name": "ollama",
                "endpoint": Config.OLLAMA_BASE_URL,
                "status": "configured"
            },
            {
                "name": "nim",
                "endpoint": Config.NIM_BASE_URL,
                "status": "configured" if Config.NGC_API_KEY else "missing_api_key"
            }
        ]
    }


def main():
    """Run the API server"""
    print(f"""
    ╔════════════════════════════════════════════════════════════╗
    ║       Agent 5 Inference Engine - Model Management API      ║
    ╠════════════════════════════════════════════════════════════╣
    ║  Ollama Endpoint: {Config.OLLAMA_BASE_URL:38} ║
    ║  NIM Endpoint:    {Config.NIM_BASE_URL:38} ║
    ║  API Server:      http://{Config.API_HOST}:{Config.API_PORT:28} ║
    ╚════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host=Config.API_HOST,
        port=Config.API_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()
