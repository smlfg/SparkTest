"""
Configuration Loader Utility
Loads and validates playbook configurations against the unified schema
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


class ConfigLoader:
    """
    Loads and validates playbook configurations
    """

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize config loader

        Args:
            schema_path: Path to config schema YAML file
        """
        if schema_path is None:
            # Default to shared schema
            schema_path = Path(__file__).parent.parent / "config_schema.yaml"

        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()

    def _load_schema(self) -> Dict[str, Any]:
        """Load the configuration schema"""
        try:
            with open(self.schema_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            return {}

    def load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load a playbook configuration file

        Args:
            config_path: Path to configuration file (YAML or JSON)

        Returns:
            Configuration dictionary

        Raises:
            ConfigValidationError: If configuration is invalid
        """
        config_path = Path(config_path)

        if not config_path.exists():
            raise ConfigValidationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, 'r') as f:
                if config_path.suffix in ['.yaml', '.yml']:
                    config = yaml.safe_load(f)
                elif config_path.suffix == '.json':
                    config = json.load(f)
                else:
                    raise ConfigValidationError(f"Unsupported file format: {config_path.suffix}")

            # Validate configuration
            self.validate_config(config)

            return config

        except yaml.YAMLError as e:
            raise ConfigValidationError(f"YAML parsing error: {e}")
        except json.JSONDecodeError as e:
            raise ConfigValidationError(f"JSON parsing error: {e}")
        except Exception as e:
            raise ConfigValidationError(f"Failed to load config: {e}")

    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate a configuration against the schema

        Args:
            config: Configuration dictionary

        Returns:
            True if valid

        Raises:
            ConfigValidationError: If validation fails
        """
        if "playbook" not in config:
            raise ConfigValidationError("Missing required 'playbook' key")

        playbook = config["playbook"]

        # Validate required fields
        required_fields = ["name", "description", "version", "agent", "dependencies", "ports"]
        for field in required_fields:
            if field not in playbook:
                raise ConfigValidationError(f"Missing required field: playbook.{field}")

        # Validate agent format
        agent = playbook["agent"]
        if not agent.startswith("agent") or not agent[5:].isdigit():
            raise ConfigValidationError(f"Invalid agent format: {agent}")

        # Validate ports
        if not isinstance(playbook["ports"], list):
            raise ConfigValidationError("ports must be a list")

        for port in playbook["ports"]:
            if not isinstance(port, int) or port < 1024 or port > 65535:
                raise ConfigValidationError(f"Invalid port: {port}")

        # Validate dependencies
        if not isinstance(playbook["dependencies"], list):
            raise ConfigValidationError("dependencies must be a list")

        # Validate GPU configuration
        if playbook.get("gpu_required", False):
            gpu_config = playbook.get("gpu_config", {})
            if "count" in gpu_config and gpu_config["count"] < 1:
                raise ConfigValidationError("gpu_config.count must be >= 1")

        logger.info(f"Configuration validated successfully: {playbook['name']}")
        return True

    def get_example_config(self, playbook_name: str) -> Optional[Dict[str, Any]]:
        """
        Get an example configuration for a playbook

        Args:
            playbook_name: Name of the playbook

        Returns:
            Example configuration or None if not found
        """
        examples = self.schema.get("examples", {})
        return examples.get(playbook_name)

    def save_config(self, config: Dict[str, Any], output_path: str):
        """
        Save a configuration to file

        Args:
            config: Configuration dictionary
            output_path: Output file path
        """
        output_path = Path(output_path)

        # Validate before saving
        self.validate_config(config)

        with open(output_path, 'w') as f:
            if output_path.suffix in ['.yaml', '.yml']:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            elif output_path.suffix == '.json':
                json.dump(config, f, indent=2)
            else:
                raise ValueError(f"Unsupported file format: {output_path.suffix}")

        logger.info(f"Configuration saved to: {output_path}")


def load_playbook_config(config_path: str) -> Dict[str, Any]:
    """
    Convenience function to load a playbook configuration

    Args:
        config_path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    loader = ConfigLoader()
    return loader.load_config(config_path)


def create_config_from_template(
    name: str,
    agent: str,
    description: str,
    ports: List[int],
    dependencies: List[str],
    gpu_required: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Create a configuration from template

    Args:
        name: Playbook name
        agent: Agent ID
        description: Playbook description
        ports: List of ports
        dependencies: List of dependencies
        gpu_required: Whether GPU is required
        **kwargs: Additional configuration options

    Returns:
        Configuration dictionary
    """
    config = {
        "playbook": {
            "name": name,
            "description": description,
            "version": kwargs.get("version", "1.0.0"),
            "agent": agent,
            "dependencies": dependencies,
            "ports": ports,
            "gpu_required": gpu_required
        }
    }

    # Add optional fields
    if "volumes" in kwargs:
        config["playbook"]["volumes"] = kwargs["volumes"]

    if "docker" in kwargs:
        config["playbook"]["docker"] = kwargs["docker"]

    if gpu_required and "gpu_config" in kwargs:
        config["playbook"]["gpu_config"] = kwargs["gpu_config"]

    if "resources" in kwargs:
        config["playbook"]["resources"] = kwargs["resources"]

    if "health_check" in kwargs:
        config["playbook"]["health_check"] = kwargs["health_check"]

    return config
