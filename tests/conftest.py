"""
Pytest configuration and shared fixtures for Agent 7 tests.
"""

import pytest
import sys
from pathlib import Path
import tempfile
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_workspace(tmp_path_factory):
    """Create a temporary workspace for tests."""
    workspace = tmp_path_factory.mktemp("test_workspace")
    (workspace / "loras").mkdir()
    (workspace / "datasets").mkdir()
    (workspace / "outputs").mkdir()
    return workspace


@pytest.fixture
def sample_dataset(test_workspace):
    """Create a sample Alpaca dataset."""
    dataset = [
        {
            "instruction": "What is machine learning?",
            "input": "",
            "output": "Machine learning is a subset of AI that enables systems to learn from data."
        },
        {
            "instruction": "Explain the concept.",
            "input": "Neural networks",
            "output": "Neural networks are computing systems inspired by biological neural networks."
        }
    ]

    dataset_path = test_workspace / "datasets" / "sample.json"
    with open(dataset_path, "w") as f:
        json.dump(dataset, f)

    return dataset_path


@pytest.fixture
def sample_vlm_dataset(test_workspace):
    """Create a sample VLM dataset."""
    dataset = [
        {
            "image": "./test_image.jpg",
            "text": "USER: <image>\nWhat is in this image?\nASSISTANT: A test image."
        }
    ]

    dataset_path = test_workspace / "datasets" / "vlm_sample.json"
    with open(dataset_path, "w") as f:
        json.dump(dataset, f)

    return dataset_path


@pytest.fixture
def mock_api_client():
    """Mock API client for testing."""
    class MockAPIClient:
        def __init__(self):
            self.logged_in = False
            self.datasets = []
            self.training_jobs = []
            self.models = []

        def login(self, username, password):
            if username and password:
                self.logged_in = True
                return {"status": "success", "token": "mock_token"}
            return {"status": "error"}

        def check_gpu_status(self):
            return {
                "available": True,
                "memory_total": 80000,
                "memory_free": 60000,
                "gpu_count": 1
            }

        def upload_dataset(self, file_path):
            dataset_id = f"dataset_{len(self.datasets)}"
            self.datasets.append({"id": dataset_id, "path": file_path})
            return {"status": "success", "dataset_id": dataset_id}

        def start_training(self, dataset_id, config):
            job_id = f"job_{len(self.training_jobs)}"
            self.training_jobs.append({
                "id": job_id,
                "dataset_id": dataset_id,
                "status": "running",
                "config": config
            })
            return {"status": "success", "job_id": job_id}

        def get_training_status(self, job_id):
            for job in self.training_jobs:
                if job["id"] == job_id:
                    return {"status": job["status"], "progress": 100}
            return {"status": "not_found"}

        def complete_training(self, job_id, model_name):
            for job in self.training_jobs:
                if job["id"] == job_id:
                    job["status"] = "completed"
                    self.models.append({"name": model_name, "job_id": job_id})
                    return True
            return False

        def list_models(self):
            return {"models": self.models}

        def run_inference(self, model_name, prompt):
            return {
                "status": "success",
                "response": f"Mock response to: {prompt}",
                "latency_ms": 150
            }

    return MockAPIClient()


@pytest.fixture
def performance_thresholds():
    """Performance thresholds for testing."""
    return {
        "inference": {
            "latency_p50": 500,  # ms
            "latency_p95": 1000,  # ms
            "throughput": 50,  # tokens/sec
        },
        "training": {
            "startup": 120,  # seconds
            "samples_per_sec": 10,
            "checkpoint_save": 30,  # seconds
        },
        "dashboard": {
            "page_load": 2000,  # ms
            "api_response": 200,  # ms
            "websocket_latency": 50,  # ms
        }
    }


@pytest.fixture
def sample_training_config():
    """Sample training configuration."""
    return {
        "model_name": "unsloth/llama-3-8b-bnb-4bit",
        "lora_r": 8,
        "lora_alpha": 16,
        "num_epochs": 1,
        "learning_rate": 2e-4,
        "batch_size": 2
    }
