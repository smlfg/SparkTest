"""
Integration tests for API Gateway
Tests REST API endpoints and job submission
"""

import pytest
import time
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.smoke
class TestAPIGateway:
    """Test suite for API Gateway integration"""

    def test_health_check(self, api_client):
        """Test health check endpoint"""
        response = api_client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data
        assert "services" in data
        assert data["services"]["api"] == "healthy"

    def test_root_endpoint(self, api_client):
        """Test root endpoint"""
        response = api_client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "1.0.0"

    def test_list_agents(self, api_client):
        """Test agents listing endpoint"""
        response = api_client.get("/agents")
        assert response.status_code == 200

        data = response.json()
        assert "agents" in data
        assert "total" in data
        assert data["total"] == 10
        assert len(data["agents"]) == 10

        # Verify agent structure
        agent = data["agents"][0]
        assert "id" in agent
        assert "name" in agent
        assert "status" in agent
        assert "description" in agent

    def test_submit_job(self, api_client):
        """Test job submission"""
        job_data = {
            "job_name": "test_job",
            "job_type": "batch_processing",
            "parameters": {
                "input_path": "/data/input",
                "output_path": "/data/output"
            },
            "priority": 5
        }

        response = api_client.post("/jobs/submit", json=job_data)
        assert response.status_code == 200

        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert data["status"] == "submitted"
        assert "message" in data

        # Store job_id for cleanup
        return data["job_id"]

    def test_get_job_status(self, api_client):
        """Test getting job status"""
        # First submit a job
        job_id = self.test_submit_job(api_client)

        # Get job status
        response = api_client.get(f"/jobs/{job_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data
        assert "created_at" in data

    def test_list_jobs(self, api_client):
        """Test listing all jobs"""
        # Submit a few jobs first
        for i in range(3):
            job_data = {
                "job_name": f"test_job_{i}",
                "job_type": "batch_processing",
                "parameters": {"index": i},
                "priority": i
            }
            api_client.post("/jobs/submit", json=job_data)

        # List all jobs
        response = api_client.get("/jobs")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_cancel_job(self, api_client):
        """Test cancelling a job"""
        # Submit a job
        job_id = self.test_submit_job(api_client)

        # Cancel the job
        response = api_client.delete(f"/jobs/{job_id}")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data

        # Verify job is cancelled
        status_response = api_client.get(f"/jobs/{job_id}")
        status_data = status_response.json()
        assert status_data["status"] == "cancelled"

    def test_job_not_found(self, api_client):
        """Test fetching non-existent job"""
        response = api_client.get("/jobs/non_existent_job_id")
        assert response.status_code == 404

    def test_metrics_endpoint(self, api_client):
        """Test Prometheus metrics endpoint"""
        response = api_client.get("/metrics")
        assert response.status_code == 200
        assert "sparktest_jobs_total" in response.text
        assert "sparktest_api_requests_total" in response.text


@pytest.mark.integration
@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API Gateway"""

    def test_concurrent_job_submissions(self, api_client):
        """Test handling multiple concurrent job submissions"""
        import concurrent.futures

        def submit_job(index):
            job_data = {
                "job_name": f"concurrent_job_{index}",
                "job_type": "test",
                "parameters": {"index": index}
            }
            response = api_client.post("/jobs/submit", json=job_data)
            return response.status_code == 200

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(submit_job, range(20)))

        assert all(results), "All concurrent submissions should succeed"

    def test_api_response_time(self, api_client):
        """Test API response time is within acceptable limits"""
        start = time.time()
        response = api_client.get("/health")
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0, f"Health check took {duration}s, expected < 1s"
