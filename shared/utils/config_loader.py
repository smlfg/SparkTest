#!/usr/bin/env python3
"""
Configuration loader and validator for DGX Spark Playbooks
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Configuration loader with validation"""

    def __init__(self, config_path: Optional[str] = None, schema_path: Optional[str] = None):
        """
        Initialize configuration loader

        Args:
            config_path: Path to configuration file
            schema_path: Path to schema file
        """
        self.config_path = config_path
        self.schema_path = schema_path or self._get_default_schema_path()
        self.config = {}
        self.schema = {}

    @staticmethod
    def _get_default_schema_path() -> str:
        """Get default schema path"""
        return os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'config_schema.yaml'
        )

    def load(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration from file

        Args:
            config_path: Path to configuration file

        Returns:
            Configuration dictionary
        """
        path = config_path or self.config_path

        if not path:
            raise ValueError("Configuration path not specified")

        if not os.path.exists(path):
            raise FileNotFoundError(f"Configuration file not found: {path}")

        # Determine file type and load
        file_ext = Path(path).suffix.lower()

        try:
            with open(path, 'r') as f:
                if file_ext in ['.yaml', '.yml']:
                    self.config = yaml.safe_load(f)
                elif file_ext == '.json':
                    self.config = json.load(f)
                else:
                    raise ValueError(f"Unsupported file format: {file_ext}")

            logger.info(f"Loaded configuration from {path}")
            return self.config

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

    def load_schema(self, schema_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Load configuration schema

        Args:
            schema_path: Path to schema file

        Returns:
            Schema dictionary
        """
        path = schema_path or self.schema_path

        if not os.path.exists(path):
            logger.warning(f"Schema file not found: {path}")
            return {}

        try:
            with open(path, 'r') as f:
                self.schema = yaml.safe_load(f)

            logger.info(f"Loaded schema from {path}")
            return self.schema

        except Exception as e:
            logger.error(f"Error loading schema: {e}")
            return {}

    def validate(self, config: Optional[Dict] = None) -> bool:
        """
        Validate configuration against schema

        Args:
            config: Configuration to validate (uses loaded config if not provided)

        Returns:
            True if valid, False otherwise
        """
        cfg = config or self.config

        if not cfg:
            logger.error("No configuration to validate")
            return False

        if not self.schema:
            logger.warning("No schema loaded, skipping validation")
            return True

        # Basic validation - check required fields
        playbook_schema = self.schema.get('playbook', {})

        for field, spec in playbook_schema.items():
            if isinstance(spec, dict) and spec.get('required', False):
                if field not in cfg:
                    logger.error(f"Missing required field: {field}")
                    return False

        logger.info("Configuration validation passed")
        return True

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key

        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value if value is not None else default

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value

        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self.config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def merge(self, other: Dict[str, Any]) -> None:
        """
        Merge another configuration

        Args:
            other: Configuration to merge
        """
        self._deep_merge(self.config, other)

    @staticmethod
    def _deep_merge(base: Dict, other: Dict) -> Dict:
        """Deep merge two dictionaries"""
        for key, value in other.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                ConfigLoader._deep_merge(base[key], value)
            else:
                base[key] = value
        return base

    def save(self, output_path: str, format: str = 'yaml') -> None:
        """
        Save configuration to file

        Args:
            output_path: Output file path
            format: Output format (yaml or json)
        """
        try:
            with open(output_path, 'w') as f:
                if format == 'yaml':
                    yaml.dump(self.config, f, default_flow_style=False)
                elif format == 'json':
                    json.dump(self.config, f, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {format}")

            logger.info(f"Saved configuration to {output_path}")

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise


def load_config(config_path: str, validate: bool = True) -> Dict[str, Any]:
    """
    Convenience function to load and optionally validate configuration

    Args:
        config_path: Path to configuration file
        validate: Whether to validate configuration

    Returns:
        Configuration dictionary
    """
    loader = ConfigLoader(config_path)
    config = loader.load()

    if validate:
        loader.load_schema()
        if not loader.validate():
            raise ValueError("Configuration validation failed")

    return config


def validate_config(config: Dict[str, Any], schema_path: Optional[str] = None) -> bool:
    """
    Validate configuration against schema

    Args:
        config: Configuration dictionary
        schema_path: Path to schema file

    Returns:
        True if valid, False otherwise
    """
    loader = ConfigLoader(schema_path=schema_path)
    loader.config = config
    loader.load_schema()
    return loader.validate()
