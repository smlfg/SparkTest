"""
Unit tests for config loader module
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from shared.utils.config_loader import (
    load_config,
    validate_config,
    ConfigValidationError,
    get_env_with_default,
    merge_configs
)


class TestConfigLoader:
    """Test cases for configuration loader"""

    def test_load_config_success(self):
        """Test successful configuration loading"""
        config_data = {
            "playbook": {
                "name": "test_agent",
                "version": "1.0.0",
                "description": "Test agent",
                "ports": [8000],
                "gpu_required": True
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config["playbook"]["name"] == "test_agent"
            assert config["playbook"]["ports"] == [8000]
        finally:
            Path(temp_path).unlink()

    def test_load_config_file_not_found(self):
        """Test loading non-existent config file"""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/config.yaml")

    def test_validate_config_success(self):
        """Test successful configuration validation"""
        config = {
            "playbook": {
                "name": "test_agent",
                "version": "1.0.0",
                "description": "Test agent",
                "ports": [8000],
                "gpu_required": True
            }
        }

        # Should not raise any exception
        result = validate_config(config)
        assert result is True

    def test_validate_config_missing_playbook(self):
        """Test validation with missing playbook section"""
        config = {"other": "data"}

        with pytest.raises(ConfigValidationError, match="must contain 'playbook' section"):
            validate_config(config)

    def test_validate_config_missing_required_field(self):
        """Test validation with missing required field"""
        config = {
            "playbook": {
                "name": "test_agent"
                # Missing other required fields
            }
        }

        with pytest.raises(ConfigValidationError):
            validate_config(config)

    def test_validate_config_invalid_port(self):
        """Test validation with invalid port number"""
        config = {
            "playbook": {
                "name": "test_agent",
                "version": "1.0.0",
                "description": "Test agent",
                "ports": [99999],  # Invalid port
                "gpu_required": True
            }
        }

        with pytest.raises(ConfigValidationError, match="Invalid port number"):
            validate_config(config)

    def test_validate_config_gpu_count_invalid(self):
        """Test validation with invalid GPU count"""
        config = {
            "playbook": {
                "name": "test_agent",
                "version": "1.0.0",
                "description": "Test agent",
                "ports": [8000],
                "gpu_required": True,
                "gpu_count": -1  # Invalid GPU count
            }
        }

        with pytest.raises(ConfigValidationError, match="gpu_count must be a positive integer"):
            validate_config(config)

    def test_get_env_with_default_string(self, monkeypatch):
        """Test getting environment variable with string default"""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = get_env_with_default("TEST_VAR", "default")
        assert result == "test_value"

    def test_get_env_with_default_missing(self):
        """Test getting missing environment variable returns default"""
        result = get_env_with_default("NONEXISTENT_VAR", "default_value")
        assert result == "default_value"

    def test_get_env_with_default_bool(self, monkeypatch):
        """Test getting environment variable with bool default"""
        monkeypatch.setenv("TEST_BOOL", "true")
        result = get_env_with_default("TEST_BOOL", False)
        assert result is True

    def test_get_env_with_default_int(self, monkeypatch):
        """Test getting environment variable with int default"""
        monkeypatch.setenv("TEST_INT", "42")
        result = get_env_with_default("TEST_INT", 0)
        assert result == 42

    def test_merge_configs_simple(self):
        """Test merging simple configurations"""
        base = {"a": 1, "b": 2}
        override = {"b": 3, "c": 4}

        result = merge_configs(base, override)

        assert result["a"] == 1
        assert result["b"] == 3
        assert result["c"] == 4

    def test_merge_configs_nested(self):
        """Test merging nested configurations"""
        base = {
            "playbook": {
                "name": "base",
                "resources": {
                    "memory": "4g",
                    "cpus": 2.0
                }
            }
        }

        override = {
            "playbook": {
                "resources": {
                    "memory": "8g"
                }
            }
        }

        result = merge_configs(base, override)

        assert result["playbook"]["name"] == "base"
        assert result["playbook"]["resources"]["memory"] == "8g"
        assert result["playbook"]["resources"]["cpus"] == 2.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
