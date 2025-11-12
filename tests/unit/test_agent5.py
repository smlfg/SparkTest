#!/usr/bin/env python3
"""
Unit tests for Agent 5: Inference Engine
"""

import pytest
import sys
import os

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../shared'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../agents/agent5_inference/api'))

from shared.health_check import HealthChecker, HealthStatus
from shared.utils.config_loader import ConfigLoader


class TestHealthCheck:
    """Test health check functionality"""

    def test_health_checker_init(self):
        """Test HealthChecker initialization"""
        checker = HealthChecker(timeout=5)
        assert checker.timeout == 5
        assert checker.session is not None

    def test_system_health(self):
        """Test system health check"""
        checker = HealthChecker()
        health = checker.get_system_health()

        assert 'cpu' in health
        assert 'memory' in health
        assert 'disk' in health

        assert 'usage_percent' in health['cpu']
        assert 'usage_percent' in health['memory']
        assert 'usage_percent' in health['disk']


class TestConfigLoader:
    """Test configuration loader"""

    def test_config_loader_init(self):
        """Test ConfigLoader initialization"""
        loader = ConfigLoader()
        assert loader.config == {}
        assert loader.schema == {}

    def test_get_default(self):
        """Test get with default value"""
        loader = ConfigLoader()
        loader.config = {'key': 'value'}

        assert loader.get('key') == 'value'
        assert loader.get('nonexistent', 'default') == 'default'

    def test_set_value(self):
        """Test setting configuration value"""
        loader = ConfigLoader()
        loader.set('key', 'value')

        assert loader.get('key') == 'value'

    def test_nested_get(self):
        """Test nested key access"""
        loader = ConfigLoader()
        loader.config = {
            'level1': {
                'level2': {
                    'level3': 'value'
                }
            }
        }

        assert loader.get('level1.level2.level3') == 'value'
        assert loader.get('level1.level2.nonexistent', 'default') == 'default'


class TestModelRegistry:
    """Test model registry functionality"""

    def test_model_registry_structure(self):
        """Test model registry has correct structure"""
        try:
            from agent5_model_api import MODEL_REGISTRY

            assert 'ollama_models' in MODEL_REGISTRY
            assert 'nim_endpoints' in MODEL_REGISTRY

            assert isinstance(MODEL_REGISTRY['ollama_models'], list)
            assert isinstance(MODEL_REGISTRY['nim_endpoints'], list)

            assert len(MODEL_REGISTRY['ollama_models']) > 0
            assert len(MODEL_REGISTRY['nim_endpoints']) > 0

        except ImportError:
            pytest.skip("agent5_model_api not available")


@pytest.mark.asyncio
class TestAsyncOperations:
    """Test async operations"""

    async def test_async_placeholder(self):
        """Placeholder for async tests"""
        # Add async tests here when needed
        assert True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
