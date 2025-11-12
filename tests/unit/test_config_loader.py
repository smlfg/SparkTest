#!/usr/bin/env python3
"""
Unit tests for config loader
"""

import pytest
import tempfile
from pathlib import Path
from shared.utils.config_loader import (
    load_config,
    validate_config,
    expand_env_vars,
    merge_configs
)


def test_expand_env_vars_dict():
    """Test environment variable expansion in dict"""
    import os
    os.environ["TEST_VAR"] = "test_value"

    config = {
        "key": "$TEST_VAR",
        "nested": {
            "key2": "$TEST_VAR"
        }
    }

    expanded = expand_env_vars(config)

    assert expanded["key"] == "test_value"
    assert expanded["nested"]["key2"] == "test_value"


def test_expand_env_vars_list():
    """Test environment variable expansion in list"""
    import os
    os.environ["TEST_VAR"] = "test_value"

    config = ["$TEST_VAR", {"key": "$TEST_VAR"}]
    expanded = expand_env_vars(config)

    assert expanded[0] == "test_value"
    assert expanded[1]["key"] == "test_value"


def test_validate_config_valid():
    """Test config validation with valid config"""
    config = {
        "name": "test-playbook",
        "agent": "agent3",
        "version": "1.0.0"
    }

    assert validate_config(config) is True


def test_validate_config_missing_field():
    """Test config validation with missing required field"""
    config = {
        "name": "test-playbook",
        "agent": "agent3"
        # missing version
    }

    with pytest.raises(ValueError, match="Missing required field"):
        validate_config(config)


def test_validate_config_invalid_version():
    """Test config validation with invalid version format"""
    config = {
        "name": "test-playbook",
        "agent": "agent3",
        "version": "1.0"  # invalid: needs X.Y.Z
    }

    with pytest.raises(ValueError, match="Invalid version format"):
        validate_config(config)


def test_validate_config_invalid_port():
    """Test config validation with invalid port"""
    config = {
        "name": "test-playbook",
        "agent": "agent3",
        "version": "1.0.0",
        "ports": [99999]  # invalid port
    }

    with pytest.raises(ValueError, match="Invalid port"):
        validate_config(config)


def test_merge_configs():
    """Test config merging"""
    base = {
        "key1": "value1",
        "nested": {
            "key2": "value2",
            "key3": "value3"
        }
    }

    override = {
        "key1": "override1",
        "nested": {
            "key3": "override3"
        },
        "key4": "value4"
    }

    result = merge_configs(base, override)

    assert result["key1"] == "override1"
    assert result["nested"]["key2"] == "value2"
    assert result["nested"]["key3"] == "override3"
    assert result["key4"] == "value4"


def test_load_config_file_not_found():
    """Test loading non-existent config file"""
    with pytest.raises(FileNotFoundError):
        load_config("/nonexistent/path/config.yaml")
