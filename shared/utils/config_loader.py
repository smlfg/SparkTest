#!/usr/bin/env python3
"""
Configuration Loader and Validator
Loads and validates playbook configurations against the schema
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
try:
    from yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper


def load_yaml(file_path: str) -> Dict[str, Any]:
    """
    Load YAML file

    Args:
        file_path: Path to YAML file

    Returns:
        Parsed YAML content as dictionary
    """
    with open(file_path, 'r') as f:
        return yaml.load(f, Loader=Loader)


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load playbook configuration

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config is invalid YAML
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    config = load_yaml(config_path)

    # Expand environment variables in config
    config = expand_env_vars(config)

    return config


def expand_env_vars(config: Any) -> Any:
    """
    Recursively expand environment variables in config

    Args:
        config: Configuration object (dict, list, or str)

    Returns:
        Configuration with expanded environment variables
    """
    if isinstance(config, dict):
        return {k: expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [expand_env_vars(item) for item in config]
    elif isinstance(config, str):
        return os.path.expandvars(config)
    else:
        return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration against schema

    Args:
        config: Configuration dictionary

    Returns:
        True if valid, raises exception otherwise

    Raises:
        ValueError: If configuration is invalid
    """
    # Basic validation
    required_fields = ["name", "agent", "version"]

    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required field: {field}")

    # Validate version format
    version = config["version"]
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(
            f"Invalid version format: {version}. Expected: X.Y.Z"
        )

    # Validate agent format
    agent = config["agent"]
    if not agent.startswith("agent"):
        raise ValueError(
            f"Invalid agent format: {agent}. Expected: agentN"
        )

    # Validate ports if present
    if "ports" in config:
        for port in config["ports"]:
            if not isinstance(port, int) or port < 1 or port > 65535:
                raise ValueError(
                    f"Invalid port: {port}. Must be integer 1-65535"
                )

    # Validate GPU config if present
    if "gpu_config" in config:
        gpu_config = config["gpu_config"]

        if "count" in gpu_config:
            if not isinstance(gpu_config["count"], int) or gpu_config["count"] < 0:
                raise ValueError("GPU count must be non-negative integer")

        if "memory_fraction" in gpu_config:
            frac = gpu_config["memory_fraction"]
            if not (0.0 <= frac <= 1.0):
                raise ValueError("GPU memory_fraction must be between 0.0 and 1.0")

    return True


def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries

    Args:
        base: Base configuration
        override: Override configuration

    Returns:
        Merged configuration
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_configs(result[key], value)
        else:
            result[key] = value

    return result


def save_config(config: Dict[str, Any], output_path: str) -> None:
    """
    Save configuration to file

    Args:
        config: Configuration dictionary
        output_path: Output file path
    """
    with open(output_path, 'w') as f:
        yaml.dump(config, f, Dumper=Dumper, default_flow_style=False, sort_keys=False)
