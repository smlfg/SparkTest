#!/usr/bin/env python3
"""
Unit tests for health check module
"""

import pytest
from shared.health_check import (
    check_service,
    check_service_detailed,
    check_port_open,
    HealthStatus
)


def test_check_port_open_invalid():
    """Test port check with invalid port"""
    result = check_port_open("localhost", 9999, timeout=1)
    assert result is False


def test_health_check_result_to_dict():
    """Test HealthCheckResult to_dict conversion"""
    from shared.health_check import HealthCheckResult

    result = HealthCheckResult(
        service="test-service",
        status=HealthStatus.HEALTHY,
        response_time=0.5,
        message="Test message",
        details={"key": "value"}
    )

    result_dict = result.to_dict()

    assert result_dict["service"] == "test-service"
    assert result_dict["status"] == "healthy"
    assert result_dict["response_time_ms"] == 500.0
    assert result_dict["message"] == "Test message"
    assert result_dict["details"]["key"] == "value"
    assert "timestamp" in result_dict


def test_check_service_invalid_port():
    """Test check_service with invalid port"""
    result = check_service(
        port=9999,
        endpoint="/health",
        timeout=1
    )
    assert result is False


def test_check_service_detailed_invalid():
    """Test detailed check with invalid service"""
    result = check_service_detailed(
        port=9999,
        endpoint="/health",
        timeout=1,
        service_name="test-service"
    )

    assert result.status == HealthStatus.UNHEALTHY
    assert result.service == "test-service"
    assert isinstance(result.response_time, float)
