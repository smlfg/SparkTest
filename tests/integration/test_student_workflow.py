"""
Integration tests for complete student workflow.

Tests the end-to-end flow from login to model deployment.
"""

import pytest
import time
from pathlib import Path


class TestStudentWorkflow:
    """Test complete student workflow from start to finish."""

    def test_01_login(self, mock_api_client):
        """Test student login."""
        response = mock_api_client.login("student1", "password123")

        assert response["status"] == "success"
        assert "token" in response
        assert mock_api_client.logged_in is True

    def test_02_dashboard_access(self, mock_api_client):
        """Test dashboard access and GPU availability."""
        mock_api_client.login("student1", "password123")

        gpu_status = mock_api_client.check_gpu_status()

        assert gpu_status["available"] is True
        assert gpu_status["memory_total"] > 0
        assert gpu_status["memory_free"] > 0
        assert gpu_status["gpu_count"] > 0

    def test_03_dataset_upload(self, mock_api_client, sample_dataset):
        """Test dataset upload."""
        mock_api_client.login("student1", "password123")

        response = mock_api_client.upload_dataset(str(sample_dataset))

        assert response["status"] == "success"
        assert "dataset_id" in response
        assert len(mock_api_client.datasets) == 1

    def test_04_training_start(self, mock_api_client, sample_dataset, sample_training_config):
        """Test training job start."""
        mock_api_client.login("student1", "password123")

        # Upload dataset
        dataset_response = mock_api_client.upload_dataset(str(sample_dataset))
        dataset_id = dataset_response["dataset_id"]

        # Start training
        train_response = mock_api_client.start_training(
            dataset_id,
            sample_training_config
        )

        assert train_response["status"] == "success"
        assert "job_id" in train_response
        assert len(mock_api_client.training_jobs) == 1

    def test_05_training_completion(self, mock_api_client, sample_dataset, sample_training_config):
        """Test training job completion."""
        mock_api_client.login("student1", "password123")

        # Upload and start training
        dataset_response = mock_api_client.upload_dataset(str(sample_dataset))
        train_response = mock_api_client.start_training(
            dataset_response["dataset_id"],
            sample_training_config
        )

        job_id = train_response["job_id"]

        # Simulate training completion
        mock_api_client.complete_training(job_id, "student_model_v1")

        # Check status
        status = mock_api_client.get_training_status(job_id)

        assert status["status"] == "completed"
        assert len(mock_api_client.models) == 1

    def test_06_model_testing(self, mock_api_client, sample_dataset, sample_training_config):
        """Test model inference after training."""
        mock_api_client.login("student1", "password123")

        # Complete workflow
        dataset_response = mock_api_client.upload_dataset(str(sample_dataset))
        train_response = mock_api_client.start_training(
            dataset_response["dataset_id"],
            sample_training_config
        )
        job_id = train_response["job_id"]
        mock_api_client.complete_training(job_id, "student_model_v1")

        # Test inference
        inference_response = mock_api_client.run_inference(
            "student_model_v1",
            "What is machine learning?"
        )

        assert inference_response["status"] == "success"
        assert "response" in inference_response
        assert "latency_ms" in inference_response
        assert inference_response["latency_ms"] < 2000  # < 2s latency

    def test_full_workflow_integration(self, mock_api_client, sample_dataset, sample_training_config):
        """Test complete end-to-end workflow."""
        # Step 1: Login
        login_response = mock_api_client.login("student1", "password123")
        assert login_response["status"] == "success"

        # Step 2: Check GPU
        gpu_status = mock_api_client.check_gpu_status()
        assert gpu_status["available"] is True

        # Step 3: Upload dataset
        dataset_response = mock_api_client.upload_dataset(str(sample_dataset))
        assert dataset_response["status"] == "success"
        dataset_id = dataset_response["dataset_id"]

        # Step 4: Start training
        train_response = mock_api_client.start_training(
            dataset_id,
            sample_training_config
        )
        assert train_response["status"] == "success"
        job_id = train_response["job_id"]

        # Step 5: Monitor training (simulated)
        status = mock_api_client.get_training_status(job_id)
        assert status["status"] == "running"

        # Complete training
        mock_api_client.complete_training(job_id, "final_model")

        # Step 6: Verify model available
        models = mock_api_client.list_models()
        assert len(models["models"]) == 1
        assert models["models"][0]["name"] == "final_model"

        # Step 7: Test inference
        inference_response = mock_api_client.run_inference(
            "final_model",
            "Test prompt"
        )
        assert inference_response["status"] == "success"
        assert inference_response["latency_ms"] < 2000

    def test_workflow_with_multiple_datasets(self, mock_api_client, sample_dataset, test_workspace):
        """Test workflow with multiple dataset uploads."""
        mock_api_client.login("student1", "password123")

        # Upload multiple datasets
        dataset_ids = []
        for i in range(3):
            response = mock_api_client.upload_dataset(str(sample_dataset))
            dataset_ids.append(response["dataset_id"])

        assert len(mock_api_client.datasets) == 3
        assert len(dataset_ids) == 3

    def test_workflow_with_error_recovery(self, mock_api_client, sample_dataset, sample_training_config):
        """Test workflow with simulated errors and recovery."""
        mock_api_client.login("student1", "password123")

        # Upload dataset
        dataset_response = mock_api_client.upload_dataset(str(sample_dataset))
        dataset_id = dataset_response["dataset_id"]

        # Start training
        train_response = mock_api_client.start_training(
            dataset_id,
            sample_training_config
        )
        job_id = train_response["job_id"]

        # Check status of non-existent job (error case)
        bad_status = mock_api_client.get_training_status("invalid_job_id")
        assert bad_status["status"] == "not_found"

        # Check status of valid job (recovery)
        good_status = mock_api_client.get_training_status(job_id)
        assert good_status["status"] == "running"


class TestConcurrentWorkflows:
    """Test multiple students working concurrently."""

    def test_concurrent_logins(self, mock_api_client):
        """Test multiple student logins."""
        students = [
            ("student1", "pass1"),
            ("student2", "pass2"),
            ("student3", "pass3")
        ]

        for username, password in students:
            response = mock_api_client.login(username, password)
            assert response["status"] == "success"

    def test_concurrent_dataset_uploads(self, mock_api_client, sample_dataset):
        """Test concurrent dataset uploads."""
        mock_api_client.login("student1", "password123")

        # Simulate 3 concurrent uploads
        responses = []
        for i in range(3):
            response = mock_api_client.upload_dataset(str(sample_dataset))
            responses.append(response)

        assert len(responses) == 3
        assert all(r["status"] == "success" for r in responses)
        assert len(mock_api_client.datasets) == 3

    def test_concurrent_training_jobs(self, mock_api_client, sample_dataset, sample_training_config):
        """Test concurrent training jobs."""
        mock_api_client.login("student1", "password123")

        # Start 3 concurrent training jobs
        job_ids = []
        for i in range(3):
            dataset_response = mock_api_client.upload_dataset(str(sample_dataset))
            train_response = mock_api_client.start_training(
                dataset_response["dataset_id"],
                sample_training_config
            )
            job_ids.append(train_response["job_id"])

        assert len(job_ids) == 3
        assert len(mock_api_client.training_jobs) == 3

        # Verify all jobs are running
        for job_id in job_ids:
            status = mock_api_client.get_training_status(job_id)
            assert status["status"] == "running"
