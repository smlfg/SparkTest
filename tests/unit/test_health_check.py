"""
Unit tests for shared health check module
"""

import pytest
import requests
from unittest.mock import Mock, patch
from shared.health_check import (
    check_service,
    check_service_detailed,
    check_multiple_services,
    wait_for_service
)


class TestHealthCheck:
    """Test cases for health check functionality"""

    @patch('shared.health_check.requests.get')
    def test_check_service_healthy(self, mock_get):
        """Test successful health check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        result = check_service(8000, "/health")
        assert result is True
        mock_get.assert_called_once()

    @patch('shared.health_check.requests.get')
    def test_check_service_unhealthy(self, mock_get):
        """Test failed health check"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = check_service(8000, "/health")
        assert result is False

    @patch('shared.health_check.requests.get')
    def test_check_service_connection_error(self, mock_get):
        """Test connection error handling"""
        mock_get.side_effect = requests.exceptions.ConnectionError()

        result = check_service(8000, "/health")
        assert result is False

    @patch('shared.health_check.requests.get')
    def test_check_service_timeout(self, mock_get):
        """Test timeout handling"""
        mock_get.side_effect = requests.exceptions.Timeout()

        result = check_service(8000, "/health", timeout=1)
        assert result is False

    @patch('shared.health_check.requests.get')
    def test_check_service_detailed(self, mock_get):
        """Test detailed health check"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy"}
        mock_get.return_value = mock_response

        is_healthy, details = check_service_detailed(8000, "/health")

        assert is_healthy is True
        assert details["status_code"] == 200
        assert "response_time_ms" in details
        assert "timestamp" in details
        assert details["response_body"] == {"status": "healthy"}

    @patch('shared.health_check.check_service')
    def test_check_multiple_services(self, mock_check):
        """Test checking multiple services"""
        mock_check.side_effect = [True, False, True]

        services = {
            "agent1": {"port": 8001},
            "agent2": {"port": 8002},
            "agent3": {"port": 8003}
        }

        results = check_multiple_services(services)

        assert results["agent1"] is True
        assert results["agent2"] is False
        assert results["agent3"] is True
        assert mock_check.call_count == 3

    @patch('shared.health_check.check_service')
    @patch('shared.health_check.time.sleep')
    def test_wait_for_service_success(self, mock_sleep, mock_check):
        """Test waiting for service to become healthy"""
        mock_check.side_effect = [False, False, True]

        result = wait_for_service(8000, max_attempts=3, delay=1)

        assert result is True
        assert mock_check.call_count == 3

    @patch('shared.health_check.check_service')
    @patch('shared.health_check.time.sleep')
    def test_wait_for_service_timeout(self, mock_sleep, mock_check):
        """Test waiting for service timeout"""
        mock_check.return_value = False

        result = wait_for_service(8000, max_attempts=3, delay=1)

        assert result is False
        assert mock_check.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
