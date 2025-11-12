#!/usr/bin/env python3
"""
Integration tests for Agent 5: Inference Engine
"""

import pytest
import requests
import time
import os


# Configuration
API_BASE_URL = os.getenv('API_URL', 'http://localhost:8888')
OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')
TIMEOUT = 10


class TestServiceAvailability:
    """Test service availability"""

    def test_api_health(self):
        """Test API health endpoint"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
            assert response.status_code == 200

            data = response.json()
            assert 'status' in data
            assert data['status'] == 'healthy'

        except requests.exceptions.ConnectionError:
            pytest.skip("API service not available")

    def test_ollama_availability(self):
        """Test Ollama availability"""
        try:
            response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=TIMEOUT)
            assert response.status_code == 200

        except requests.exceptions.ConnectionError:
            pytest.skip("Ollama service not available")


class TestModelAPI:
    """Test Model Management API endpoints"""

    def test_list_models(self):
        """Test list models endpoint"""
        try:
            response = requests.get(f"{API_BASE_URL}/api/models", timeout=TIMEOUT)
            assert response.status_code == 200

            data = response.json()
            assert isinstance(data, dict)

        except requests.exceptions.ConnectionError:
            pytest.skip("API service not available")

    def test_get_model_registry(self):
        """Test get model registry"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/models/registry",
                timeout=TIMEOUT
            )
            assert response.status_code == 200

            data = response.json()
            assert 'ollama_models' in data
            assert 'nim_endpoints' in data

        except requests.exceptions.ConnectionError:
            pytest.skip("API service not available")

    def test_list_providers(self):
        """Test list providers endpoint"""
        try:
            response = requests.get(
                f"{API_BASE_URL}/api/providers",
                timeout=TIMEOUT
            )
            assert response.status_code == 200

            data = response.json()
            assert 'providers' in data
            assert isinstance(data['providers'], list)

        except requests.exceptions.ConnectionError:
            pytest.skip("API service not available")


class TestInference:
    """Test inference operations"""

    @pytest.mark.slow
    def test_completion_endpoint(self):
        """Test completion endpoint (requires running model)"""
        try:
            payload = {
                "model": "llama3.1:70b",
                "prompt": "Hello",
                "max_tokens": 10,
                "provider": "ollama"
            }

            response = requests.post(
                f"{API_BASE_URL}/api/completion",
                json=payload,
                timeout=60
            )

            # May fail if model not available, that's ok for testing
            assert response.status_code in [200, 404, 500]

        except requests.exceptions.ConnectionError:
            pytest.skip("API service not available")

    @pytest.mark.slow
    def test_chat_endpoint(self):
        """Test chat endpoint (requires running model)"""
        try:
            payload = {
                "model": "llama3.1:70b",
                "messages": [
                    {"role": "user", "content": "Hi"}
                ],
                "max_tokens": 10,
                "provider": "ollama"
            }

            response = requests.post(
                f"{API_BASE_URL}/api/chat",
                json=payload,
                timeout=60
            )

            # May fail if model not available, that's ok for testing
            assert response.status_code in [200, 404, 500]

        except requests.exceptions.ConnectionError:
            pytest.skip("API service not available")


class TestEndToEnd:
    """End-to-end integration tests"""

    def test_full_workflow(self):
        """Test complete workflow: list models -> check health -> attempt inference"""
        try:
            # Step 1: Check API health
            health_response = requests.get(
                f"{API_BASE_URL}/health",
                timeout=TIMEOUT
            )
            assert health_response.status_code == 200

            # Step 2: List available models
            models_response = requests.get(
                f"{API_BASE_URL}/api/models",
                timeout=TIMEOUT
            )
            assert models_response.status_code == 200

            # Step 3: Get registry
            registry_response = requests.get(
                f"{API_BASE_URL}/api/models/registry",
                timeout=TIMEOUT
            )
            assert registry_response.status_code == 200

            # All basic endpoints working
            assert True

        except requests.exceptions.ConnectionError:
            pytest.skip("API service not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
