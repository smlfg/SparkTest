"""
Shared Health Check API for All Agents
Provides unified health checking across all DGX Spark Playbook services
"""

import asyncio
import aiohttp
import time
import sys
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    service: str
    status: HealthStatus
    response_time_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class HealthChecker:
    """
    Unified health checker for all services
    """

    def __init__(self, timeout: int = 10):
        """
        Initialize health checker

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    async def check_service(
        self,
        host: str = "localhost",
        port: int = 8000,
        endpoint: str = "/health",
        expected_status: int = 200,
        service_name: Optional[str] = None
    ) -> HealthCheckResult:
        """
        Check health of a service

        Args:
            host: Service host
            port: Service port
            endpoint: Health check endpoint
            expected_status: Expected HTTP status code
            service_name: Optional service name for logging

        Returns:
            HealthCheckResult with status and details
        """
        if service_name is None:
            service_name = f"{host}:{port}"

        url = f"http://{host}:{port}{endpoint}"
        start_time = time.time()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    response_time = (time.time() - start_time) * 1000

                    # Get response body
                    try:
                        details = await response.json()
                    except:
                        details = {"raw": await response.text()}

                    # Determine status
                    if response.status == expected_status:
                        status = HealthStatus.HEALTHY
                    elif 200 <= response.status < 300:
                        status = HealthStatus.DEGRADED
                    else:
                        status = HealthStatus.UNHEALTHY

                    return HealthCheckResult(
                        service=service_name,
                        status=status,
                        response_time_ms=response_time,
                        details=details
                    )

        except asyncio.TimeoutError:
            return HealthCheckResult(
                service=service_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                error=f"Timeout after {self.timeout}s"
            )
        except aiohttp.ClientError as e:
            return HealthCheckResult(
                service=service_name,
                status=HealthStatus.UNHEALTHY,
                response_time_ms=(time.time() - start_time) * 1000,
                error=f"Connection error: {str(e)}"
            )
        except Exception as e:
            return HealthCheckResult(
                service=service_name,
                status=HealthStatus.UNKNOWN,
                response_time_ms=(time.time() - start_time) * 1000,
                error=f"Unexpected error: {str(e)}"
            )

    async def check_multiple_services(
        self,
        services: List[Dict[str, Any]]
    ) -> List[HealthCheckResult]:
        """
        Check health of multiple services in parallel

        Args:
            services: List of service configurations with host, port, endpoint

        Returns:
            List of health check results
        """
        tasks = [
            self.check_service(
                host=service.get("host", "localhost"),
                port=service["port"],
                endpoint=service.get("endpoint", "/health"),
                expected_status=service.get("expected_status", 200),
                service_name=service.get("name")
            )
            for service in services
        ]

        return await asyncio.gather(*tasks)

    def is_healthy(self, result: HealthCheckResult) -> bool:
        """Check if a service is healthy"""
        return result.status == HealthStatus.HEALTHY

    def print_results(self, results: List[HealthCheckResult]):
        """Pretty print health check results"""
        print("\n" + "=" * 70)
        print("HEALTH CHECK RESULTS")
        print("=" * 70)

        for result in results:
            status_icon = {
                HealthStatus.HEALTHY: "✓",
                HealthStatus.UNHEALTHY: "✗",
                HealthStatus.DEGRADED: "⚠",
                HealthStatus.UNKNOWN: "?"
            }.get(result.status, "?")

            print(f"\n{status_icon} {result.service}")
            print(f"  Status: {result.status.value}")
            print(f"  Response Time: {result.response_time_ms:.2f}ms")

            if result.error:
                print(f"  Error: {result.error}")

            if result.details and not result.error:
                print(f"  Details: {json.dumps(result.details, indent=4)[:200]}")

        print("\n" + "=" * 70)

        # Summary
        total = len(results)
        healthy = sum(1 for r in results if r.status == HealthStatus.HEALTHY)
        unhealthy = sum(1 for r in results if r.status == HealthStatus.UNHEALTHY)
        degraded = sum(1 for r in results if r.status == HealthStatus.DEGRADED)

        print(f"\nSummary: {healthy}/{total} healthy, {unhealthy} unhealthy, {degraded} degraded")
        print("=" * 70 + "\n")


# Agent 9 service configurations
AGENT9_SERVICES = [
    {
        "name": "ComfyUI",
        "host": "localhost",
        "port": 8188,
        "endpoint": "/system_stats"
    },
    {
        "name": "RAG Workbench",
        "host": "localhost",
        "port": 3000,
        "endpoint": "/health"
    },
    {
        "name": "Multi-Agent Chatbot",
        "host": "localhost",
        "port": 8080,
        "endpoint": "/health"
    },
    {
        "name": "Knowledge Graph Viz",
        "host": "localhost",
        "port": 3001,
        "endpoint": "/health"
    },
    {
        "name": "Video Search & Summarization",
        "host": "localhost",
        "port": 8081,
        "endpoint": "/health"
    }
]


async def check_agent9_services() -> bool:
    """
    Check all Agent 9 services

    Returns:
        True if all services are healthy, False otherwise
    """
    checker = HealthChecker(timeout=10)
    results = await checker.check_multiple_services(AGENT9_SERVICES)

    checker.print_results(results)

    # Return True only if all services are healthy
    return all(checker.is_healthy(result) for result in results)


async def check_single_service(
    port: int,
    endpoint: str = "/health",
    host: str = "localhost"
) -> bool:
    """
    Simple function to check a single service

    Args:
        port: Service port
        endpoint: Health check endpoint
        host: Service host

    Returns:
        True if service is healthy, False otherwise
    """
    checker = HealthChecker(timeout=10)
    result = await checker.check_service(
        host=host,
        port=port,
        endpoint=endpoint
    )

    logger.info(f"Health check for {host}:{port}{endpoint}: {result.status.value}")

    return checker.is_healthy(result)


def check_service(port: int, endpoint: str = "/health") -> bool:
    """
    Synchronous wrapper for health check (for use in Docker HEALTHCHECK)

    Args:
        port: Service port
        endpoint: Health check endpoint

    Returns:
        True if service is healthy, False otherwise
    """
    try:
        return asyncio.run(check_single_service(port, endpoint))
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return False


async def main():
    """Main entry point for health checker"""
    import argparse

    parser = argparse.ArgumentParser(description="Health Check Utility")
    parser.add_argument("--port", type=int, help="Service port")
    parser.add_argument("--endpoint", default="/health", help="Health check endpoint")
    parser.add_argument("--host", default="localhost", help="Service host")
    parser.add_argument("--agent9", action="store_true", help="Check all Agent 9 services")
    parser.add_argument("--timeout", type=int, default=10, help="Request timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.agent9:
        # Check all Agent 9 services
        all_healthy = await check_agent9_services()
        sys.exit(0 if all_healthy else 1)

    elif args.port:
        # Check single service
        checker = HealthChecker(timeout=args.timeout)
        result = await checker.check_service(
            host=args.host,
            port=args.port,
            endpoint=args.endpoint
        )

        if args.json:
            output = {
                "service": result.service,
                "status": result.status.value,
                "response_time_ms": result.response_time_ms,
                "timestamp": result.timestamp.isoformat(),
                "details": result.details,
                "error": result.error
            }
            print(json.dumps(output, indent=2))
        else:
            checker.print_results([result])

        sys.exit(0 if checker.is_healthy(result) else 1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
