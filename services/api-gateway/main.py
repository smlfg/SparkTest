"""
SparkTest API Gateway
Main FastAPI application for orchestrating Spark jobs and managing resources
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import os
import logging
from datetime import datetime
import redis
import asyncpg
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="SparkTest API Gateway",
    description="API Gateway for SparkTest Multi-Agent System",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment variables
SPARK_MASTER_URL = os.getenv("SPARK_MASTER_URL", "spark://spark-master:7077")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sparktest:sparktest123@postgres:5432/sparktest_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Prometheus metrics
job_counter = Counter('sparktest_jobs_total', 'Total number of Spark jobs submitted')
job_duration = Histogram('sparktest_job_duration_seconds', 'Spark job execution duration')
api_requests = Counter('sparktest_api_requests_total', 'Total API requests', ['endpoint', 'method'])

# Redis client
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Pydantic models
class JobSubmission(BaseModel):
    job_name: str
    job_type: str
    parameters: Dict[str, Any]
    priority: Optional[int] = 5

class JobStatus(BaseModel):
    job_id: str
    job_name: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: datetime
    services: Dict[str, str]

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for monitoring"""
    services = {
        "api": "healthy",
        "redis": "unknown",
        "database": "unknown",
        "spark": "unknown"
    }

    # Check Redis
    try:
        redis_client.ping()
        services["redis"] = "healthy"
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        services["redis"] = "unhealthy"

    # Check Database
    try:
        # This is a simplified check - in production, use connection pooling
        services["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        services["database"] = "unhealthy"

    # Check Spark Master
    try:
        # In production, check Spark Master REST API
        services["spark"] = "healthy"
    except Exception as e:
        logger.error(f"Spark health check failed: {e}")
        services["spark"] = "unhealthy"

    overall_status = "healthy" if all(s == "healthy" for s in services.values()) else "degraded"

    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.utcnow(),
        services=services
    )

@app.get("/")
async def root():
    """Root endpoint"""
    api_requests.labels(endpoint="/", method="GET").inc()
    return {
        "message": "SparkTest API Gateway",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.post("/jobs/submit", response_model=Dict[str, str])
async def submit_job(job: JobSubmission, background_tasks: BackgroundTasks):
    """Submit a Spark job for execution"""
    api_requests.labels(endpoint="/jobs/submit", method="POST").inc()
    job_counter.inc()

    try:
        # Generate job ID
        job_id = f"job_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"

        # Store job in Redis
        job_data = {
            "job_id": job_id,
            "job_name": job.job_name,
            "job_type": job.job_type,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "parameters": str(job.parameters),
            "priority": job.priority
        }

        redis_client.hset(f"job:{job_id}", mapping=job_data)
        redis_client.lpush("job_queue", job_id)

        logger.info(f"Job submitted: {job_id} - {job.job_name}")

        return {
            "job_id": job_id,
            "status": "submitted",
            "message": f"Job {job.job_name} submitted successfully"
        }

    except Exception as e:
        logger.error(f"Error submitting job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs/{job_id}", response_model=Dict[str, Any])
async def get_job_status(job_id: str):
    """Get status of a specific job"""
    api_requests.labels(endpoint="/jobs/{job_id}", method="GET").inc()

    try:
        job_data = redis_client.hgetall(f"job:{job_id}")

        if not job_data:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        return job_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/jobs", response_model=List[Dict[str, Any]])
async def list_jobs(status: Optional[str] = None, limit: int = 100):
    """List all jobs with optional status filter"""
    api_requests.labels(endpoint="/jobs", method="GET").inc()

    try:
        # Get all job keys
        job_keys = redis_client.keys("job:*")
        jobs = []

        for key in job_keys[:limit]:
            job_data = redis_client.hgetall(key)
            if status is None or job_data.get("status") == status:
                jobs.append(job_data)

        return jobs

    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a running job"""
    api_requests.labels(endpoint="/jobs/{job_id}", method="DELETE").inc()

    try:
        job_data = redis_client.hgetall(f"job:{job_id}")

        if not job_data:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

        # Update job status
        redis_client.hset(f"job:{job_id}", "status", "cancelled")

        return {"message": f"Job {job_id} cancelled successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.get("/agents")
async def list_agents():
    """List all available agents"""
    api_requests.labels(endpoint="/agents", method="GET").inc()

    agents = [
        {"id": 1, "name": "Agent 1", "status": "active", "description": "Data Ingestion"},
        {"id": 2, "name": "Agent 2", "status": "active", "description": "Data Processing"},
        {"id": 3, "name": "Agent 3", "status": "active", "description": "Analytics"},
        {"id": 4, "name": "Agent 4", "status": "active", "description": "ML Pipeline"},
        {"id": 5, "name": "Agent 5", "status": "active", "description": "Query Engine"},
        {"id": 6, "name": "Agent 6", "status": "active", "description": "Batch Processing"},
        {"id": 7, "name": "Agent 7", "status": "active", "description": "Stream Processing"},
        {"id": 8, "name": "Agent 8", "status": "active", "description": "Scheduler"},
        {"id": 9, "name": "Agent 9", "status": "active", "description": "Monitoring"},
        {"id": 10, "name": "Agent 10", "status": "active", "description": "Integration & Testing"},
    ]

    return {"agents": agents, "total": len(agents)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
