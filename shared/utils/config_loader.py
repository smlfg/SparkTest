"""
shared/utils/config_loader.py
Configuration loader and validator for agent playbooks
"""

import yaml
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load YAML configuration file.

    Args:
        config_path: Path to the YAML configuration file

    Returns:
        Dict containing the configuration

    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If YAML parsing fails
    """
    config_file = Path(config_path)

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    logger.info(f"Loading configuration from {config_path}")

    with open(config_file, 'r') as f:
        try:
            config = yaml.safe_load(f)
            logger.info("Configuration loaded successfully")
            return config
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML configuration: {e}")
            raise


def validate_config(config: Dict[str, Any], schema_path: Optional[str] = None) -> bool:
    """
    Validate configuration against the schema.

    Args:
        config: Configuration dictionary to validate
        schema_path: Optional path to schema file (uses default if not provided)

    Returns:
        bool: True if validation passes

    Raises:
        ConfigValidationError: If validation fails
    """
    if schema_path is None:
        # Use default schema path
        schema_path = Path(__file__).parent.parent / "config_schema.yaml"

    logger.info(f"Validating configuration against schema: {schema_path}")

    # Load schema
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    if "playbook" not in config:
        raise ConfigValidationError("Configuration must contain 'playbook' section")

    playbook = config["playbook"]
    schema_def = schema["playbook"]

    # Validate required fields
    required_fields = {
        field: spec for field, spec in schema_def.items()
        if isinstance(spec, dict) and spec.get("required", False)
    }

    for field, spec in required_fields.items():
        if field not in playbook:
            raise ConfigValidationError(
                f"Required field '{field}' is missing from playbook configuration"
            )

    # Validate field types
    type_mapping = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "list": list,
        "object": dict
    }

    for field, value in playbook.items():
        if field not in schema_def:
            logger.warning(f"Unknown field '{field}' in playbook configuration")
            continue

        field_spec = schema_def[field]
        if not isinstance(field_spec, dict):
            continue

        expected_type_str = field_spec.get("type")
        if expected_type_str and expected_type_str in type_mapping:
            expected_type = type_mapping[expected_type_str]
            if not isinstance(value, expected_type):
                raise ConfigValidationError(
                    f"Field '{field}' has invalid type. "
                    f"Expected {expected_type_str}, got {type(value).__name__}"
                )

    # Validate GPU configuration
    if playbook.get("gpu_required", False):
        gpu_count = playbook.get("gpu_count", 1)
        if not isinstance(gpu_count, int) or gpu_count < 1:
            raise ConfigValidationError(
                "gpu_count must be a positive integer when gpu_required is true"
            )

    # Validate ports
    ports = playbook.get("ports", [])
    if not ports:
        raise ConfigValidationError("At least one port must be specified")

    for port in ports:
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ConfigValidationError(
                f"Invalid port number: {port}. Must be between 1 and 65535"
            )

    logger.info("Configuration validation passed")
    return True


def get_env_with_default(key: str, default: Any) -> Any:
    """
    Get environment variable with default value.

    Args:
        key: Environment variable key
        default: Default value if key not found

    Returns:
        Environment variable value or default
    """
    value = os.getenv(key)
    if value is None:
        return default

    # Try to convert to same type as default
    if isinstance(default, bool):
        return value.lower() in ("true", "1", "yes")
    elif isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            logger.warning(f"Cannot convert {key}={value} to int, using default")
            return default
    elif isinstance(default, float):
        try:
            return float(value)
        except ValueError:
            logger.warning(f"Cannot convert {key}={value} to float, using default")
            return default

    return value


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configurations, with override_config taking precedence.

    Args:
        base_config: Base configuration
        override_config: Override configuration

    Returns:
        Merged configuration dictionary
    """
    merged = base_config.copy()

    for key, value in override_config.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value

    return merged


if __name__ == "__main__":
    # Example usage
    print("Configuration loader utility")
    print("This module provides functions to load and validate agent configurations")
