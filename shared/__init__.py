"""
shared/__init__.py
Shared interfaces and utilities for all DGX Spark agents
"""

from .health_check import (
    check_service,
    check_service_detailed,
    check_multiple_services,
    wait_for_service,
    create_health_endpoint
)

__version__ = "1.0.0"

__all__ = [
    "check_service",
    "check_service_detailed",
    "check_multiple_services",
    "wait_for_service",
    "create_health_endpoint"
]
