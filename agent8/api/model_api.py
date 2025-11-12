"""
REST API for Model Registry
FastAPI service for accessing quantized models
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent8.registry.model_registry import ModelRegistry


# Initialize FastAPI app
app = FastAPI(
    title="Agent 8: Model Optimization API",
    description="REST API for quantized model registry and management",
    version="1.0.0"
)

# Initialize registry
QUANTIZED_MODELS_DIR = Path("/workspace/models/quantized")
QUANTIZED_MODELS_DIR.mkdir(parents=True, exist_ok=True)

registry = ModelRegistry(
    registry_path=str(QUANTIZED_MODELS_DIR / "registry.json")
)


# Pydantic models
class ModelInfo(BaseModel):
    """Model information schema"""
    model_name: str
    quantized_name: str
    precision: str
    bits: int
    original_size_gb: float
    quantized_size_gb: float
    compression_ratio: float
    output_path: str
    created_at: str
    status: str


class ModelsResponse(BaseModel):
    """Response model for quantized models list"""
    models: List[Dict[str, Any]]
    count: int
    total_size_gb: float
    total_savings_gb: float


class RegistryStats(BaseModel):
    """Registry statistics schema"""
    total_models: int
    total_original_size_gb: float
    total_quantized_size_gb: float
    total_savings_gb: float
    average_compression_ratio: float
    precision_distribution: Dict[str, int]


# API Routes

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Agent 8: Model Optimization API",
        "version": "1.0.0",
        "endpoints": [
            "/api/models/quantized",
            "/api/models/{model_id}",
            "/api/stats",
            "/health"
        ]
    }


@app.get("/api/models/quantized", response_model=ModelsResponse)
async def get_quantized_models(
    precision: Optional[str] = Query(None, description="Filter by precision (fp4, int8, nf4)"),
    limit: Optional[int] = Query(None, description="Limit number of results")
):
    """
    Get list of quantized models

    Args:
        precision: Filter by precision type
        limit: Limit number of results

    Returns:
        List of quantized models with metadata
    """
    try:
        # Get models
        if precision:
            models = registry.filter_by_precision(precision)
        else:
            models = registry.list_all()

        # Apply limit
        if limit:
            models = models[:limit]

        # Calculate totals
        total_size = sum(m.get("quantized_size_gb", 0) for m in models)
        total_savings = sum(
            m.get("original_size_gb", 0) - m.get("quantized_size_gb", 0)
            for m in models
        )

        return ModelsResponse(
            models=models,
            count=len(models),
            total_size_gb=total_size,
            total_savings_gb=total_savings
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/models/{model_id}")
async def get_model(model_id: str):
    """
    Get specific model information

    Args:
        model_id: Model ID

    Returns:
        Model information
    """
    model = registry.get(model_id)

    if model is None:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    return model


@app.get("/api/models/search/{model_name}")
async def search_models(model_name: str):
    """
    Search for models by name

    Args:
        model_name: Model name to search

    Returns:
        List of matching models
    """
    models = registry.find_by_name(model_name)

    return {
        "query": model_name,
        "results": models,
        "count": len(models)
    }


@app.get("/api/stats", response_model=RegistryStats)
async def get_statistics():
    """
    Get registry statistics

    Returns:
        Registry statistics
    """
    stats = registry.get_statistics()
    return RegistryStats(**stats)


@app.delete("/api/models/{model_id}")
async def delete_model(model_id: str):
    """
    Delete a model from registry

    Args:
        model_id: Model ID to delete

    Returns:
        Success message
    """
    success = registry.delete(model_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Model {model_id} not found")

    return {"message": f"Model {model_id} deleted successfully"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agent8-model-api",
        "registry_path": str(registry.registry_path),
        "models_count": len(registry.list_all())
    }


# Error handlers

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )


# Main entry point
if __name__ == "__main__":
    import uvicorn

    print("Starting Agent 8 Model API...")
    print(f"Registry path: {registry.registry_path}")
    print("API available at: http://localhost:8888")
    print("Docs available at: http://localhost:8888/docs")

    uvicorn.run(app, host="0.0.0.0", port=8888)
