"""
Pytest configuration and fixtures
"""

import pytest
import os


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


@pytest.fixture(scope="session")
def api_url():
    """API URL fixture"""
    return os.getenv('API_URL', 'http://localhost:8888')


@pytest.fixture(scope="session")
def ollama_url():
    """Ollama URL fixture"""
    return os.getenv('OLLAMA_URL', 'http://localhost:11434')


@pytest.fixture(scope="session")
def test_timeout():
    """Test timeout fixture"""
    return int(os.getenv('TEST_TIMEOUT', '10'))
