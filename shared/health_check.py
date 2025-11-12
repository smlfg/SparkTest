"""
shared/health_check.py
Health check API for all DGX Spark agents

Provides standardized health check functionality across all agents.
"""

import requests
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_service(
    port: int,
    endpoint: str = "/health",
    timeout: int = 5,
    host: str = "localhost"
) -> bool:
    """
    Check if a service is healthy by calling its health endpoint.

    Args:
        port: Port number the service is running on
        endpoint: Health check endpoint path (default: "/health")
        timeout: Request timeout in seconds (default: 5)
        host: Host address (default: "localhost")

    Returns:
        bool: True if service is healthy (status code 200), False otherwise

    Example:
        >>> check_service(8000, "/health")
        True
    """
    try:
        url = f"http://{host}:{port}{endpoint}"
        logger.debug(f"Checking service health at {url}")

        response = requests.get(url, timeout=timeout)

        if response.status_code == 200:
            logger.info(f"Service at {url} is healthy")
            return True
        else:
            logger.warning(f"Service at {url} returned status code {response.status_code}")
            return False

    except requests.exceptions.ConnectionError:
        logger.error(f"Failed to connect to service at {host}:{port}{endpoint}")
        return False
    except requests.exceptions.Timeout:
        logger.error(f"Health check timeout for service at {host}:{port}{endpoint}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking service health: {str(e)}")
        return False


def check_service_detailed(
    port: int,
    endpoint: str = "/health",
    timeout: int = 5,
    host: str = "localhost"
) -> Tuple[bool, Dict]:
    """
    Check service health and return detailed information.

    Args:
        port: Port number the service is running on
        endpoint: Health check endpoint path (default: "/health")
        timeout: Request timeout in seconds (default: 5)
        host: Host address (default: "localhost")

    Returns:
        Tuple[bool, Dict]: (is_healthy, details_dict)
        details_dict contains: status_code, response_time_ms, timestamp, message, response_body

    Example:
        >>> is_healthy, details = check_service_detailed(8000)
        >>> print(f"Healthy: {is_healthy}, Response time: {details['response_time_ms']}ms")
    """
    details = {
        "timestamp": datetime.utcnow().isoformat(),
        "url": f"http://{host}:{port}{endpoint}",
        "status_code": None,
        "response_time_ms": None,
        "message": "",
        "response_body": None
    }

    try:
        url = f"http://{host}:{port}{endpoint}"
        start_time = datetime.now()

        response = requests.get(url, timeout=timeout)

        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000

        details["status_code"] = response.status_code
        details["response_time_ms"] = round(response_time, 2)

        try:
            details["response_body"] = response.json()
        except json.JSONDecodeError:
            details["response_body"] = response.text

        if response.status_code == 200:
            details["message"] = "Service is healthy"
            logger.info(f"Service at {url} is healthy (response time: {response_time:.2f}ms)")
            return True, details
        else:
            details["message"] = f"Service returned status code {response.status_code}"
            logger.warning(details["message"])
            return False, details

    except requests.exceptions.ConnectionError as e:
        details["message"] = f"Connection error: {str(e)}"
        logger.error(details["message"])
        return False, details
    except requests.exceptions.Timeout:
        details["message"] = f"Health check timeout after {timeout}s"
        logger.error(details["message"])
        return False, details
    except Exception as e:
        details["message"] = f"Unexpected error: {str(e)}"
        logger.error(details["message"])
        return False, details


def check_multiple_services(services: Dict[str, Dict]) -> Dict[str, bool]:
    """
    Check health of multiple services.

    Args:
        services: Dictionary mapping service names to their config
                 Config should contain: port, endpoint (optional), timeout (optional)

    Returns:
        Dict[str, bool]: Dictionary mapping service names to health status

    Example:
        >>> services = {
        ...     "agent1": {"port": 8001, "endpoint": "/health"},
        ...     "agent2": {"port": 8002, "endpoint": "/health"}
        ... }
        >>> results = check_multiple_services(services)
        >>> print(results)
        {'agent1': True, 'agent2': True}
    """
    results = {}

    for service_name, config in services.items():
        port = config.get("port")
        endpoint = config.get("endpoint", "/health")
        timeout = config.get("timeout", 5)
        host = config.get("host", "localhost")

        if port is None:
            logger.error(f"No port specified for service {service_name}")
            results[service_name] = False
            continue

        results[service_name] = check_service(port, endpoint, timeout, host)

    return results


def wait_for_service(
    port: int,
    endpoint: str = "/health",
    max_attempts: int = 30,
    delay: int = 2,
    timeout: int = 5,
    host: str = "localhost"
) -> bool:
    """
    Wait for a service to become healthy.

    Args:
        port: Port number the service is running on
        endpoint: Health check endpoint path (default: "/health")
        max_attempts: Maximum number of health check attempts (default: 30)
        delay: Delay between attempts in seconds (default: 2)
        timeout: Request timeout in seconds (default: 5)
        host: Host address (default: "localhost")

    Returns:
        bool: True if service becomes healthy, False if max attempts reached

    Example:
        >>> wait_for_service(8000, max_attempts=60, delay=1)
        True
    """
    import time

    logger.info(f"Waiting for service at {host}:{port}{endpoint} to become healthy...")

    for attempt in range(1, max_attempts + 1):
        if check_service(port, endpoint, timeout, host):
            logger.info(f"Service is healthy after {attempt} attempt(s)")
            return True

        logger.info(f"Attempt {attempt}/{max_attempts} failed, retrying in {delay}s...")
        time.sleep(delay)

    logger.error(f"Service did not become healthy after {max_attempts} attempts")
    return False


# FastAPI health check endpoint implementation
def create_health_endpoint():
    """
    Create a standard health check endpoint for FastAPI applications.

    Returns:
        Callable: FastAPI endpoint function

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> app.get("/health")(create_health_endpoint())
    """
    def health_check():
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "service": "agent"
        }

    return health_check


if __name__ == "__main__":
    # Example usage
    print("Testing health check functionality...")

    # Test single service
    is_healthy = check_service(8000, "/health")
    print(f"Service health: {is_healthy}")

    # Test detailed check
    is_healthy, details = check_service_detailed(8000, "/health")
    print(f"Detailed check: {is_healthy}")
    print(f"Details: {json.dumps(details, indent=2)}")

    # Test multiple services
    services = {
        "agent1": {"port": 8001},
        "agent2": {"port": 8002},
        "agent3": {"port": 8003}
    }
    results = check_multiple_services(services)
    print(f"Multiple services check: {results}")
