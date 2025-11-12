"""
Integration tests for service-to-service communication.

Tests communication between:
- Ollama ↔ Open-WebUI
- LLaMA Factory ↔ Ollama
- Dashboard ↔ All services
"""

import pytest
import time
from unittest.mock import Mock, patch


class MockOllamaService:
    """Mock Ollama service for testing."""

    def __init__(self):
        self.models = []
        self.running = True

    def list_models(self):
        if not self.running:
            raise ConnectionError("Service not available")
        return {"models": self.models}

    def generate(self, model, prompt):
        if not self.running:
            raise ConnectionError("Service not available")
        if model not in [m["name"] for m in self.models]:
            raise ValueError(f"Model {model} not found")
        return {
            "response": f"Response to: {prompt}",
            "latency_ms": 100
        }

    def register_model(self, model_name, model_path):
        if not self.running:
            raise ConnectionError("Service not available")
        self.models.append({"name": model_name, "path": model_path})
        return {"status": "success"}


class MockOpenWebUI:
    """Mock Open-WebUI service for testing."""

    def __init__(self, ollama_service):
        self.ollama = ollama_service
        self.conversations = []

    def create_conversation(self, model, messages):
        # Communicate with Ollama
        try:
            response = self.ollama.generate(model, messages[-1]["content"])
            conversation_id = f"conv_{len(self.conversations)}"
            self.conversations.append({
                "id": conversation_id,
                "model": model,
                "messages": messages,
                "response": response
            })
            return {"status": "success", "conversation_id": conversation_id, "response": response}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def list_models(self):
        # Get models from Ollama
        try:
            return self.ollama.list_models()
        except Exception as e:
            return {"status": "error", "error": str(e)}


class MockLLaMAFactory:
    """Mock LLaMA Factory service for testing."""

    def __init__(self, ollama_service):
        self.ollama = ollama_service
        self.training_jobs = []

    def start_training(self, config):
        job_id = f"job_{len(self.training_jobs)}"
        self.training_jobs.append({
            "id": job_id,
            "config": config,
            "status": "running"
        })
        return {"status": "success", "job_id": job_id}

    def get_job_status(self, job_id):
        for job in self.training_jobs:
            if job["id"] == job_id:
                return {"status": job["status"], "progress": 100}
        return {"status": "not_found"}

    def export_model_to_ollama(self, job_id, model_name):
        """Export trained model to Ollama."""
        for job in self.training_jobs:
            if job["id"] == job_id:
                if job["status"] == "completed":
                    # Register with Ollama
                    result = self.ollama.register_model(model_name, f"/models/{model_name}")
                    return {"status": "success", "registered": True}
                return {"status": "error", "error": "Job not completed"}
        return {"status": "error", "error": "Job not found"}

    def complete_job(self, job_id):
        """Helper to complete a job."""
        for job in self.training_jobs:
            if job["id"] == job_id:
                job["status"] = "completed"
                return True
        return False


class MockDashboard:
    """Mock Dashboard service for testing."""

    def __init__(self, ollama, webui, llama_factory):
        self.ollama = ollama
        self.webui = webui
        self.llama_factory = llama_factory

    def get_system_status(self):
        """Get status of all services."""
        status = {}

        try:
            ollama_models = self.ollama.list_models()
            status["ollama"] = {"status": "running", "models": len(ollama_models.get("models", []))}
        except Exception as e:
            status["ollama"] = {"status": "error", "error": str(e)}

        try:
            webui_models = self.webui.list_models()
            status["webui"] = {"status": "running", "conversations": len(self.webui.conversations)}
        except Exception as e:
            status["webui"] = {"status": "error", "error": str(e)}

        status["llama_factory"] = {
            "status": "running",
            "jobs": len(self.llama_factory.training_jobs)
        }

        return status

    def trigger_training(self, dataset, config):
        """Trigger training via LLaMA Factory."""
        return self.llama_factory.start_training(config)

    def test_inference(self, model, prompt):
        """Test inference via WebUI/Ollama."""
        return self.webui.create_conversation(model, [{"role": "user", "content": prompt}])


class TestOllamaWebUIConnection:
    """Test Ollama ↔ Open-WebUI communication."""

    def test_webui_lists_ollama_models(self):
        """Test that WebUI can list models from Ollama."""
        ollama = MockOllamaService()
        ollama.register_model("llama3", "/models/llama3")

        webui = MockOpenWebUI(ollama)
        models = webui.list_models()

        assert "models" in models
        assert len(models["models"]) == 1
        assert models["models"][0]["name"] == "llama3"

    def test_webui_inference_through_ollama(self):
        """Test that WebUI can run inference through Ollama."""
        ollama = MockOllamaService()
        ollama.register_model("llama3", "/models/llama3")

        webui = MockOpenWebUI(ollama)
        response = webui.create_conversation(
            "llama3",
            [{"role": "user", "content": "Hello"}]
        )

        assert response["status"] == "success"
        assert "response" in response
        assert "conversation_id" in response

    def test_webui_handles_ollama_unavailable(self):
        """Test WebUI handles Ollama being unavailable."""
        ollama = MockOllamaService()
        ollama.running = False

        webui = MockOpenWebUI(ollama)
        response = webui.list_models()

        assert response["status"] == "error"
        assert "error" in response

    def test_webui_handles_model_not_found(self):
        """Test WebUI handles model not found in Ollama."""
        ollama = MockOllamaService()
        webui = MockOpenWebUI(ollama)

        response = webui.create_conversation(
            "nonexistent_model",
            [{"role": "user", "content": "Hello"}]
        )

        assert response["status"] == "error"


class TestLLaMAFactoryOllamaConnection:
    """Test LLaMA Factory ↔ Ollama communication."""

    def test_llama_factory_exports_to_ollama(self):
        """Test LLaMA Factory can export models to Ollama."""
        ollama = MockOllamaService()
        llama_factory = MockLLaMAFactory(ollama)

        # Start and complete training
        train_response = llama_factory.start_training({"model": "llama3"})
        job_id = train_response["job_id"]
        llama_factory.complete_job(job_id)

        # Export to Ollama
        export_response = llama_factory.export_model_to_ollama(job_id, "custom_model")

        assert export_response["status"] == "success"
        assert export_response["registered"] is True
        assert len(ollama.models) == 1

    def test_llama_factory_export_incomplete_job(self):
        """Test export fails for incomplete training job."""
        ollama = MockOllamaService()
        llama_factory = MockLLaMAFactory(ollama)

        # Start training but don't complete
        train_response = llama_factory.start_training({"model": "llama3"})
        job_id = train_response["job_id"]

        # Try to export
        export_response = llama_factory.export_model_to_ollama(job_id, "custom_model")

        assert export_response["status"] == "error"
        assert "not completed" in export_response["error"].lower()

    def test_llama_factory_export_nonexistent_job(self):
        """Test export fails for non-existent job."""
        ollama = MockOllamaService()
        llama_factory = MockLLaMAFactory(ollama)

        export_response = llama_factory.export_model_to_ollama("invalid_job", "model")

        assert export_response["status"] == "error"


class TestDashboardIntegration:
    """Test Dashboard ↔ All services communication."""

    def test_dashboard_gets_all_service_status(self):
        """Test dashboard can get status from all services."""
        ollama = MockOllamaService()
        webui = MockOpenWebUI(ollama)
        llama_factory = MockLLaMAFactory(ollama)
        dashboard = MockDashboard(ollama, webui, llama_factory)

        status = dashboard.get_system_status()

        assert "ollama" in status
        assert "webui" in status
        assert "llama_factory" in status
        assert status["ollama"]["status"] == "running"

    def test_dashboard_triggers_training(self):
        """Test dashboard can trigger training via LLaMA Factory."""
        ollama = MockOllamaService()
        webui = MockOpenWebUI(ollama)
        llama_factory = MockLLaMAFactory(ollama)
        dashboard = MockDashboard(ollama, webui, llama_factory)

        response = dashboard.trigger_training("dataset.json", {"model": "llama3"})

        assert response["status"] == "success"
        assert "job_id" in response
        assert len(llama_factory.training_jobs) == 1

    def test_dashboard_runs_inference(self):
        """Test dashboard can run inference through services."""
        ollama = MockOllamaService()
        ollama.register_model("llama3", "/models/llama3")

        webui = MockOpenWebUI(ollama)
        llama_factory = MockLLaMAFactory(ollama)
        dashboard = MockDashboard(ollama, webui, llama_factory)

        response = dashboard.test_inference("llama3", "Test prompt")

        assert response["status"] == "success"
        assert "response" in response

    def test_dashboard_handles_service_failures(self):
        """Test dashboard handles service failures gracefully."""
        ollama = MockOllamaService()
        ollama.running = False  # Simulate Ollama down

        webui = MockOpenWebUI(ollama)
        llama_factory = MockLLaMAFactory(ollama)
        dashboard = MockDashboard(ollama, webui, llama_factory)

        status = dashboard.get_system_status()

        assert status["ollama"]["status"] == "error"
        # Dashboard should still work even if one service is down
        assert "llama_factory" in status


class TestEndToEndServiceFlow:
    """Test complete end-to-end service communication flow."""

    def test_complete_training_to_inference_flow(self):
        """Test complete flow from training to inference across all services."""
        # Setup all services
        ollama = MockOllamaService()
        webui = MockOpenWebUI(ollama)
        llama_factory = MockLLaMAFactory(ollama)
        dashboard = MockDashboard(ollama, webui, llama_factory)

        # Step 1: Dashboard triggers training
        train_response = dashboard.trigger_training(
            "dataset.json",
            {"model": "llama3", "epochs": 3}
        )
        assert train_response["status"] == "success"
        job_id = train_response["job_id"]

        # Step 2: Complete training
        llama_factory.complete_job(job_id)

        # Step 3: Export model to Ollama
        export_response = llama_factory.export_model_to_ollama(job_id, "fine_tuned_model")
        assert export_response["status"] == "success"

        # Step 4: Verify model in Ollama
        models = ollama.list_models()
        assert len(models["models"]) == 1
        assert models["models"][0]["name"] == "fine_tuned_model"

        # Step 5: Run inference through WebUI
        inference_response = webui.create_conversation(
            "fine_tuned_model",
            [{"role": "user", "content": "Test the model"}]
        )
        assert inference_response["status"] == "success"

        # Step 6: Check system status
        status = dashboard.get_system_status()
        assert status["ollama"]["status"] == "running"
        assert status["ollama"]["models"] == 1
        assert status["webui"]["conversations"] == 1
        assert status["llama_factory"]["jobs"] == 1
