#!/usr/bin/env python3
"""
Shared Health Check API for DGX Spark Playbooks
Provides standardized health checking for all agents
"""

import os
import sys
import time
import logging
import argparse
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

try:
    import requests
    import psutil
except ImportError:
    print("Installing required packages...")
    os.system("pip install requests psutil")
    import requests
    import psutil

# Try to import GPU monitoring (optional)
try:
    import pynvml
    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Health check result data class"""
    service: str
    status: HealthStatus
    message: str
    response_time: float
    details: Dict = None

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "service": self.service,
            "status": self.status.value,
            "message": self.message,
            "response_time_ms": round(self.response_time * 1000, 2),
            "details": self.details or {}
        }


class HealthChecker:
    """Unified health checker for all services"""

    def __init__(self, timeout: int = 10):
        """
        Initialize health checker

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DGX-Spark-HealthChecker/1.0'
        })

        # Initialize GPU monitoring if available
        self.gpu_available = False
        if GPU_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.gpu_available = True
                logger.info("GPU monitoring enabled")
            except Exception as e:
                logger.warning(f"GPU monitoring unavailable: {e}")

    def __del__(self):
        """Cleanup resources"""
        if self.gpu_available:
            try:
                pynvml.nvmlShutdown()
            except:
                pass

    def check_service(
        self,
        port: int,
        endpoint: str = "/health",
        host: str = "localhost",
        protocol: str = "http",
        expected_status: int = 200
    ) -> HealthCheckResult:
        """
        Check if a service is healthy

        Args:
            port: Service port
            endpoint: Health check endpoint
            host: Service host
            protocol: http or https
            expected_status: Expected HTTP status code

        Returns:
            HealthCheckResult object
        """
        service_name = f"{host}:{port}"
        url = f"{protocol}://{host}:{port}{endpoint}"

        try:
            start_time = time.time()
            response = self.session.get(url, timeout=self.timeout)
            response_time = time.time() - start_time

            if response.status_code == expected_status:
                return HealthCheckResult(
                    service=service_name,
                    status=HealthStatus.HEALTHY,
                    message=f"Service responding normally",
                    response_time=response_time,
                    details={
                        "status_code": response.status_code,
                        "url": url
                    }
                )
            else:
                return HealthCheckResult(
                    service=service_name,
                    status=HealthStatus.DEGRADED,
                    message=f"Unexpected status code: {response.status_code}",
                    response_time=response_time,
                    details={
                        "status_code": response.status_code,
                        "expected": expected_status,
                        "url": url
                    }
                )

        except requests.exceptions.ConnectionError:
            return HealthCheckResult(
                service=service_name,
                status=HealthStatus.UNHEALTHY,
                message="Connection refused",
                response_time=0,
                details={"url": url, "error": "connection_refused"}
            )
        except requests.exceptions.Timeout:
            return HealthCheckResult(
                service=service_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Request timeout after {self.timeout}s",
                response_time=self.timeout,
                details={"url": url, "error": "timeout"}
            )
        except Exception as e:
            return HealthCheckResult(
                service=service_name,
                status=HealthStatus.UNHEALTHY,
                message=f"Error: {str(e)}",
                response_time=0,
                details={"url": url, "error": str(e)}
            )

    def check_multiple_services(
        self,
        services: List[Dict]
    ) -> List[HealthCheckResult]:
        """
        Check multiple services

        Args:
            services: List of service configurations
                     Each service should have: port, endpoint (optional), name (optional)

        Returns:
            List of HealthCheckResult objects
        """
        results = []
        for service in services:
            port = service.get("port")
            endpoint = service.get("endpoint", "/health")
            host = service.get("host", "localhost")
            protocol = service.get("protocol", "http")

            if not port:
                logger.warning(f"Service missing port configuration: {service}")
                continue

            result = self.check_service(port, endpoint, host, protocol)
            results.append(result)

        return results

    def get_system_health(self) -> Dict:
        """
        Get system health metrics

        Returns:
            Dictionary with system health information
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            health = {
                "cpu": {
                    "usage_percent": cpu_percent,
                    "count": psutil.cpu_count(),
                    "status": "healthy" if cpu_percent < 80 else "degraded"
                },
                "memory": {
                    "total_gb": round(memory.total / (1024**3), 2),
                    "used_gb": round(memory.used / (1024**3), 2),
                    "available_gb": round(memory.available / (1024**3), 2),
                    "usage_percent": memory.percent,
                    "status": "healthy" if memory.percent < 85 else "degraded"
                },
                "disk": {
                    "total_gb": round(disk.total / (1024**3), 2),
                    "used_gb": round(disk.used / (1024**3), 2),
                    "free_gb": round(disk.free / (1024**3), 2),
                    "usage_percent": disk.percent,
                    "status": "healthy" if disk.percent < 90 else "degraded"
                }
            }

            # Add GPU information if available
            if self.gpu_available:
                health["gpu"] = self.get_gpu_health()

            return health

        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {"error": str(e)}

    def get_gpu_health(self) -> List[Dict]:
        """
        Get GPU health metrics

        Returns:
            List of GPU health information
        """
        if not self.gpu_available:
            return []

        try:
            device_count = pynvml.nvmlDeviceGetCount()
            gpus = []

            for i in range(device_count):
                handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                name = pynvml.nvmlDeviceGetName(handle)

                # Get memory info
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                mem_total = mem_info.total / (1024**3)
                mem_used = mem_info.used / (1024**3)
                mem_free = mem_info.free / (1024**3)
                mem_percent = (mem_used / mem_total) * 100

                # Get utilization
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)

                # Get temperature
                try:
                    temp = pynvml.nvmlDeviceGetTemperature(
                        handle,
                        pynvml.NVML_TEMPERATURE_GPU
                    )
                except:
                    temp = None

                # Get power usage
                try:
                    power = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # mW to W
                except:
                    power = None

                gpu_info = {
                    "id": i,
                    "name": name,
                    "memory": {
                        "total_gb": round(mem_total, 2),
                        "used_gb": round(mem_used, 2),
                        "free_gb": round(mem_free, 2),
                        "usage_percent": round(mem_percent, 2)
                    },
                    "utilization": {
                        "gpu_percent": util.gpu,
                        "memory_percent": util.memory
                    },
                    "temperature_c": temp,
                    "power_watts": round(power, 2) if power else None,
                    "status": self._determine_gpu_status(mem_percent, util.gpu, temp)
                }

                gpus.append(gpu_info)

            return gpus

        except Exception as e:
            logger.error(f"Error getting GPU health: {e}")
            return []

    def _determine_gpu_status(
        self,
        mem_percent: float,
        gpu_util: float,
        temp: Optional[float]
    ) -> str:
        """Determine GPU health status"""
        if temp and temp > 85:
            return "degraded"
        if mem_percent > 95:
            return "degraded"
        return "healthy"

    def comprehensive_health_check(
        self,
        services: List[Dict]
    ) -> Dict:
        """
        Perform comprehensive health check

        Args:
            services: List of services to check

        Returns:
            Dictionary with complete health status
        """
        service_results = self.check_multiple_services(services)
        system_health = self.get_system_health()

        # Determine overall status
        service_statuses = [r.status for r in service_results]
        if all(s == HealthStatus.HEALTHY for s in service_statuses):
            overall_status = HealthStatus.HEALTHY
        elif any(s == HealthStatus.UNHEALTHY for s in service_statuses):
            overall_status = HealthStatus.UNHEALTHY
        else:
            overall_status = HealthStatus.DEGRADED

        return {
            "timestamp": time.time(),
            "overall_status": overall_status.value,
            "services": [r.to_dict() for r in service_results],
            "system": system_health
        }


def main():
    """Main entry point for CLI usage"""
    parser = argparse.ArgumentParser(
        description="DGX Spark Health Check Utility"
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to check"
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        default="/health",
        help="Endpoint to check (default: /health)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Host to check (default: localhost)"
    )
    parser.add_argument(
        "--system",
        action="store_true",
        help="Show system health"
    )
    parser.add_argument(
        "--self-check",
        action="store_true",
        help="Perform self health check"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output in JSON format"
    )

    args = parser.parse_args()

    checker = HealthChecker()

    if args.self_check:
        # Basic self-check
        health = checker.get_system_health()
        if args.json:
            import json
            print(json.dumps(health, indent=2))
        else:
            print(f"System Health: OK")
        sys.exit(0)

    if args.system:
        health = checker.get_system_health()
        if args.json:
            import json
            print(json.dumps(health, indent=2))
        else:
            print("\n=== System Health ===")
            print(f"CPU Usage: {health['cpu']['usage_percent']}%")
            print(f"Memory Usage: {health['memory']['usage_percent']}%")
            print(f"Disk Usage: {health['disk']['usage_percent']}%")
            if 'gpu' in health:
                print(f"\nGPUs: {len(health['gpu'])}")
                for gpu in health['gpu']:
                    print(f"  GPU {gpu['id']}: {gpu['name']}")
                    print(f"    Memory: {gpu['memory']['usage_percent']}%")
                    print(f"    Utilization: {gpu['utilization']['gpu_percent']}%")
        sys.exit(0)

    if args.port:
        result = checker.check_service(args.port, args.endpoint, args.host)
        if args.json:
            import json
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(f"\nService: {result.service}")
            print(f"Status: {result.status.value}")
            print(f"Message: {result.message}")
            print(f"Response Time: {result.response_time*1000:.2f}ms")

        sys.exit(0 if result.status == HealthStatus.HEALTHY else 1)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
