"""
DGX Spark Playbooks - Shared Module
Common utilities and interfaces for all agents
"""

__version__ = "1.0.0"
__author__ = "DGX Spark Playbooks Team"

from .health_check import (
    check_service,
    check_service_detailed,
    check_multiple_services,
    wait_for_service,
    check_port_open,
    HealthStatus,
    HealthCheckResult
)

__all__ = [
    "check_service",
    "check_service_detailed",
    "check_multiple_services",
    "wait_for_service",
    "check_port_open",
    "HealthStatus",
    "HealthCheckResult",
]
