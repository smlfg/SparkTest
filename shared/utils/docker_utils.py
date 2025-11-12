#!/usr/bin/env python3
"""
Docker Utilities
Common Docker operations for all agents
"""

import subprocess
from typing import Dict, List, Optional


def check_docker() -> bool:
    """
    Check if Docker is installed and running

    Returns:
        True if Docker is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def is_container_running(container_name: str) -> bool:
    """
    Check if a container is running

    Args:
        container_name: Name of the container

    Returns:
        True if running, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={container_name}"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return bool(result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_container_status(container_name: str) -> Optional[str]:
    """
    Get container status

    Args:
        container_name: Name of the container

    Returns:
        Container status (running, exited, etc.) or None if not found
    """
    try:
        result = subprocess.run(
            [
                "docker", "ps", "-a",
                "-f", f"name={container_name}",
                "--format", "{{.Status}}"
            ],
            capture_output=True,
            text=True,
            timeout=5
        )

        status = result.stdout.strip()
        return status if status else None

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def list_containers(all_containers: bool = False) -> List[Dict[str, str]]:
    """
    List Docker containers

    Args:
        all_containers: Include stopped containers

    Returns:
        List of container information dictionaries
    """
    cmd = ["docker", "ps", "--format", "{{.Names}}\t{{.Status}}\t{{.Ports}}"]
    if all_containers:
        cmd.append("-a")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        containers = []
        for line in result.stdout.strip().split("\n"):
            if line:
                parts = line.split("\t")
                containers.append({
                    "name": parts[0] if len(parts) > 0 else "",
                    "status": parts[1] if len(parts) > 1 else "",
                    "ports": parts[2] if len(parts) > 2 else ""
                })

        return containers

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return []


def get_container_ip(container_name: str) -> Optional[str]:
    """
    Get container IP address

    Args:
        container_name: Name of the container

    Returns:
        IP address or None if not found
    """
    try:
        result = subprocess.run(
            [
                "docker", "inspect",
                "-f", "{{range.NetworkSettings.Networks}}{{.IPAddress}}{{end}}",
                container_name
            ],
            capture_output=True,
            text=True,
            timeout=5
        )

        ip = result.stdout.strip()
        return ip if ip else None

    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def check_nvidia_docker() -> bool:
    """
    Check if NVIDIA Docker runtime is available

    Returns:
        True if nvidia-docker is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--gpus", "all", "nvidia/cuda:12.0.0-base-ubuntu22.04", "nvidia-smi"],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
