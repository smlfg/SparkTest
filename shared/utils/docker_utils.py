#!/usr/bin/env python3
"""
Docker management utilities for DGX Spark Playbooks
"""

import os
import logging
from typing import Dict, List, Optional

try:
    import docker
    from docker.errors import DockerException, APIError
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

logger = logging.getLogger(__name__)


class DockerManager:
    """Docker container management utility"""

    def __init__(self):
        """Initialize Docker manager"""
        if not DOCKER_AVAILABLE:
            raise ImportError("docker package not installed. Run: pip install docker")

        try:
            self.client = docker.from_env()
            self.api_client = docker.APIClient()
            logger.info("Docker client initialized")
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def list_containers(
        self,
        all: bool = False,
        filters: Optional[Dict] = None
    ) -> List[Dict]:
        """
        List Docker containers

        Args:
            all: Include stopped containers
            filters: Filter conditions

        Returns:
            List of container information
        """
        try:
            containers = self.client.containers.list(all=all, filters=filters)
            return [
                {
                    'id': c.id[:12],
                    'name': c.name,
                    'image': c.image.tags[0] if c.image.tags else c.image.id,
                    'status': c.status,
                    'ports': c.ports,
                    'labels': c.labels
                }
                for c in containers
            ]
        except APIError as e:
            logger.error(f"Error listing containers: {e}")
            return []

    def get_container_stats(self, container_id: str) -> Dict:
        """
        Get container statistics

        Args:
            container_id: Container ID or name

        Returns:
            Container statistics
        """
        try:
            container = self.client.containers.get(container_id)
            stats = container.stats(stream=False)
            return stats
        except APIError as e:
            logger.error(f"Error getting container stats: {e}")
            return {}

    def check_container_health(self, container_id: str) -> str:
        """
        Check container health status

        Args:
            container_id: Container ID or name

        Returns:
            Health status (healthy, unhealthy, starting, none)
        """
        try:
            container = self.client.containers.get(container_id)
            health = container.attrs.get('State', {}).get('Health', {})
            return health.get('Status', 'none')
        except APIError as e:
            logger.error(f"Error checking container health: {e}")
            return 'unknown'

    def restart_container(self, container_id: str, timeout: int = 10) -> bool:
        """
        Restart a container

        Args:
            container_id: Container ID or name
            timeout: Timeout in seconds

        Returns:
            True if successful, False otherwise
        """
        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=timeout)
            logger.info(f"Restarted container: {container_id}")
            return True
        except APIError as e:
            logger.error(f"Error restarting container: {e}")
            return False

    def get_container_logs(
        self,
        container_id: str,
        tail: int = 100,
        follow: bool = False
    ) -> str:
        """
        Get container logs

        Args:
            container_id: Container ID or name
            tail: Number of lines to retrieve
            follow: Follow log output

        Returns:
            Container logs
        """
        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail, follow=follow)
            return logs.decode('utf-8') if isinstance(logs, bytes) else logs
        except APIError as e:
            logger.error(f"Error getting container logs: {e}")
            return ""

    def inspect_network(self, network_name: str) -> Dict:
        """
        Inspect Docker network

        Args:
            network_name: Network name

        Returns:
            Network information
        """
        try:
            network = self.client.networks.get(network_name)
            return {
                'id': network.id,
                'name': network.name,
                'driver': network.attrs.get('Driver'),
                'containers': list(network.attrs.get('Containers', {}).keys())
            }
        except APIError as e:
            logger.error(f"Error inspecting network: {e}")
            return {}

    def check_gpu_support(self) -> bool:
        """
        Check if NVIDIA GPU support is available

        Returns:
            True if GPU support is available
        """
        try:
            info = self.client.info()
            runtimes = info.get('Runtimes', {})
            return 'nvidia' in runtimes
        except APIError as e:
            logger.error(f"Error checking GPU support: {e}")
            return False

    def cleanup_unused(self) -> Dict:
        """
        Clean up unused Docker resources

        Returns:
            Cleanup statistics
        """
        try:
            result = {
                'containers': self.client.containers.prune(),
                'images': self.client.images.prune(),
                'volumes': self.client.volumes.prune(),
                'networks': self.client.networks.prune()
            }
            logger.info("Cleanup completed")
            return result
        except APIError as e:
            logger.error(f"Error during cleanup: {e}")
            return {}
