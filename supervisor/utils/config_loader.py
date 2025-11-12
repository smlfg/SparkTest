#!/usr/bin/env python3
"""
Configuration Loader
Loads and validates YAML configurations for supervisor
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """Loads supervisor configuration files"""

    def __init__(self, config_dir: str = "/home/user/SparkTest/supervisor/configs"):
        self.config_dir = Path(config_dir)

    def load_yaml(self, filename: str) -> Optional[Dict[str, Any]]:
        """
        Load a YAML configuration file

        Args:
            filename: Name of config file (e.g., 'conflict_resolution_rules.yaml')

        Returns:
            Dict containing configuration, or None if error
        """
        filepath = self.config_dir / filename

        if not filepath.exists():
            print(f"⚠️  Config file not found: {filepath}")
            return None

        try:
            with open(filepath, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except yaml.YAMLError as e:
            print(f"❌ Failed to parse YAML file {filename}: {e}")
            return None
        except Exception as e:
            print(f"❌ Error loading config {filename}: {e}")
            return None

    def load_conflict_rules(self) -> Dict[str, Any]:
        """Load conflict resolution rules"""
        return self.load_yaml('conflict_resolution_rules.yaml') or {}

    def load_agent_dependencies(self) -> Dict[str, Any]:
        """Load agent dependency graph"""
        return self.load_yaml('agent_dependencies.yaml') or {}

    def get_dependency_order(self) -> list:
        """
        Get agents in dependency order (topological sort)

        Returns:
            List of agent branch names in order they should be merged
        """
        config = self.load_agent_dependencies()
        if not config:
            return []

        layers = config.get('dependency_layers', {})
        sorted_agents = []

        # Sort layers by layer number
        layer_nums = sorted([int(k.replace('layer_', '')) for k in layers.keys()])

        for layer_num in layer_nums:
            layer_key = f'layer_{layer_num}'
            layer = layers[layer_key]
            sorted_agents.extend(layer.get('agents', []))

        return sorted_agents

    def get_agent_info(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific agent"""
        config = self.load_agent_dependencies()
        if not config:
            return None

        agents = config.get('agents', {})
        return agents.get(agent_id)

    def get_port_allocation(self, agent_id: str) -> list:
        """Get allocated ports for an agent"""
        config = self.load_agent_dependencies()
        if not config:
            return []

        port_allocations = config.get('port_allocations', {})
        return port_allocations.get(agent_id, [])

    def get_conflict_rule(self, filepath: str) -> Optional[Dict[str, Any]]:
        """
        Get conflict resolution rule for a specific file

        Args:
            filepath: Path to the file (relative to repo root)

        Returns:
            Dict with resolution strategy, or default rule
        """
        rules = self.load_conflict_rules()
        if not rules:
            return None

        # Try exact match first
        if filepath in rules:
            return rules[filepath]

        # Try pattern matching
        import fnmatch
        for pattern, rule in rules.items():
            if pattern == 'default':
                continue
            if fnmatch.fnmatch(filepath, pattern):
                return rule

        # Return default rule
        return rules.get('default', {
            'strategy': 'fail_on_conflict',
            'auto_resolve': False,
            'priority': 'medium'
        })


# Global config loader instance
_config_loader = None


def get_config_loader() -> ConfigLoader:
    """Get or create global config loader instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader
