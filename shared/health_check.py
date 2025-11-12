#!/usr/bin/env python3
"""
Shared Health Check API for All Agents
Provides common health check functionality for all services
"""

import asyncio
import logging
import sys
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Health check result data class"""
    service: str
    status: HealthStatus
    response_time: float
    message: str
    details: Optional[Dict] = None
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "service": self.service,
            "status": self.status.value,
            "response_time_ms": round(self.response_time * 1000, 2),
            "message": self.message,
            "details": self.details or {},
            "timestamp": self.timestamp
        }


def create_session(
    retries: int = 3,
    backoff_factor: float = 0.3,
    timeout: int = 10
) -> requests.Session:
    """
    Create a requests session with retry logic

    Args:
        retries: Number of retries
        backoff_factor: Backoff factor for retries
        timeout: Request timeout in seconds

    Returns:
        Configured requests session
    """
    session = requests.Session()

    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST", "HEAD"]
    )

    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def check_service(
    port: int,
    endpoint: str = "/health",
    host: str = "localhost",
    protocol: str = "http",
    timeout: int = 10,
    expected_status: int = 200,
    service_name: Optional[str] = None
) -> bool:
    """
    Check if a service is healthy

    Args:
        port: Port number to check
        endpoint: Health check endpoint path
        host: Host to check (default: localhost)
        protocol: Protocol (http or https)
        timeout: Request timeout in seconds
        expected_status: Expected HTTP status code
        service_name: Optional service name for logging

    Returns:
        True if service is healthy, False otherwise
    """
    service_name = service_name or f"{host}:{port}"
    url = f"{protocol}://{host}:{port}{endpoint}"

    try:
        logger.debug(f"Checking {service_name} at {url}")
        response = requests.get(url, timeout=timeout)

        if response.status_code == expected_status:
            logger.info(f"✓ {service_name} is healthy")
            return True
        else:
            logger.warning(
                f"✗ {service_name} returned status {response.status_code}"
            )
            return False

    except requests.exceptions.ConnectionError:
        logger.error(f"✗ {service_name} - Connection refused")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"✗ {service_name} - Request timeout")
        return False
    except Exception as e:
        logger.error(f"✗ {service_name} - Error: {e}")
        return False


def check_service_detailed(
    port: int,
    endpoint: str = "/health",
    host: str = "localhost",
    protocol: str = "http",
    timeout: int = 10,
    service_name: Optional[str] = None
) -> HealthCheckResult:
    """
    Perform detailed health check with metrics

    Args:
        port: Port number to check
        endpoint: Health check endpoint path
        host: Host to check
        protocol: Protocol (http or https)
        timeout: Request timeout
        service_name: Service name

    Returns:
        HealthCheckResult object
    """
    service_name = service_name or f"{host}:{port}"
    url = f"{protocol}://{host}:{port}{endpoint}"

    start_time = time.time()

    try:
        response = requests.get(url, timeout=timeout)
        response_time = time.time() - start_time

        if response.status_code == 200:
            # Try to parse JSON response for additional details
            try:
                details = response.json()
            except:
                details = {"raw_response": response.text[:200]}

            return HealthCheckResult(
                service=service_name,
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                message="Service is healthy",
                details=details
            )
        else:
            return HealthCheckResult(
                service=service_name,
                status=HealthStatus.UNHEALTHY,
                response_time=response_time,
                message=f"Unexpected status code: {response.status_code}",
                details={"status_code": response.status_code}
            )

    except requests.exceptions.ConnectionError as e:
        return HealthCheckResult(
            service=service_name,
            status=HealthStatus.UNHEALTHY,
            response_time=time.time() - start_time,
            message="Connection refused",
            details={"error": str(e)}
        )
    except requests.exceptions.Timeout:
        return HealthCheckResult(
            service=service_name,
            status=HealthStatus.UNHEALTHY,
            response_time=timeout,
            message="Request timeout",
            details={"timeout": timeout}
        )
    except Exception as e:
        return HealthCheckResult(
            service=service_name,
            status=HealthStatus.UNKNOWN,
            response_time=time.time() - start_time,
            message=f"Error: {type(e).__name__}",
            details={"error": str(e)}
        )


def check_multiple_services(
    services: List[Dict[str, Union[int, str]]],
    parallel: bool = True
) -> Dict[str, HealthCheckResult]:
    """
    Check multiple services

    Args:
        services: List of service configurations
            Each dict should contain: port, endpoint (optional), name (optional)
        parallel: Whether to check services in parallel

    Returns:
        Dictionary mapping service names to HealthCheckResult objects
    """
    results = {}

    if parallel:
        # TODO: Implement parallel checking with asyncio
        # For now, check sequentially
        pass

    for service in services:
        port = service["port"]
        endpoint = service.get("endpoint", "/health")
        name = service.get("name", f"service-{port}")
        host = service.get("host", "localhost")

        result = check_service_detailed(
            port=port,
            endpoint=endpoint,
            host=host,
            service_name=name
        )
        results[name] = result

    return results


def wait_for_service(
    port: int,
    endpoint: str = "/health",
    host: str = "localhost",
    timeout: int = 60,
    check_interval: int = 2,
    service_name: Optional[str] = None
) -> bool:
    """
    Wait for a service to become healthy

    Args:
        port: Port number
        endpoint: Health check endpoint
        host: Host to check
        timeout: Maximum wait time in seconds
        check_interval: Interval between checks in seconds
        service_name: Service name for logging

    Returns:
        True if service became healthy, False if timeout
    """
    service_name = service_name or f"{host}:{port}"
    start_time = time.time()

    logger.info(f"Waiting for {service_name} to become healthy...")

    while time.time() - start_time < timeout:
        if check_service(
            port=port,
            endpoint=endpoint,
            host=host,
            service_name=service_name
        ):
            elapsed = time.time() - start_time
            logger.info(
                f"✓ {service_name} is ready (took {elapsed:.1f}s)"
            )
            return True

        time.sleep(check_interval)

    logger.error(f"✗ {service_name} did not become healthy within {timeout}s")
    return False


def check_port_open(host: str, port: int, timeout: int = 5) -> bool:
    """
    Check if a port is open (TCP connection test)

    Args:
        host: Host to check
        port: Port number
        timeout: Connection timeout

    Returns:
        True if port is open, False otherwise
    """
    import socket

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        logger.debug(f"Port check error: {e}")
        return False


def main():
    """CLI interface for health checks"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Health check utility for agent services"
    )
    parser.add_argument(
        "port",
        type=int,
        help="Port number to check"
    )
    parser.add_argument(
        "--endpoint",
        default="/health",
        help="Health check endpoint (default: /health)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="Host to check (default: localhost)"
    )
    parser.add_argument(
        "--protocol",
        default="http",
        choices=["http", "https"],
        help="Protocol (default: http)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=10,
        help="Request timeout in seconds (default: 10)"
    )
    parser.add_argument(
        "--wait",
        action="store_true",
        help="Wait for service to become healthy"
    )
    parser.add_argument(
        "--wait-timeout",
        type=int,
        default=60,
        help="Maximum wait time in seconds (default: 60)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    if args.wait:
        success = wait_for_service(
            port=args.port,
            endpoint=args.endpoint,
            host=args.host,
            timeout=args.wait_timeout
        )
        sys.exit(0 if success else 1)
    else:
        if args.json:
            result = check_service_detailed(
                port=args.port,
                endpoint=args.endpoint,
                host=args.host,
                protocol=args.protocol,
                timeout=args.timeout
            )
            import json
            print(json.dumps(result.to_dict(), indent=2))
            sys.exit(0 if result.status == HealthStatus.HEALTHY else 1)
        else:
            success = check_service(
                port=args.port,
                endpoint=args.endpoint,
                host=args.host,
                protocol=args.protocol,
                timeout=args.timeout
            )
            sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
