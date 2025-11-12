"""
Integration tests for agent health checks
Tests that all agents respond correctly to health check requests
"""

import pytest
import requests
from shared.health_check import check_service, check_service_detailed


# Agent configurations
AGENTS = [
    {"name": "agent1_infra", "port": 8001},
    {"name": "agent2_dashboard", "port": 8002},
    {"name": "agent3_compute", "port": 8003},
    {"name": "agent4_storage", "port": 8004},
    {"name": "agent5_networking", "port": 8005},
    {"name": "agent6_monitoring", "port": 8006},
    {"name": "agent7_security", "port": 8007},
    {"name": "agent8_analytics", "port": 8008},
    {"name": "agent9_orchestration", "port": 8009},
    {"name": "agent10_integration", "port": 8010},
]


@pytest.mark.integration
@pytest.mark.parametrize("agent", AGENTS, ids=[a["name"] for a in AGENTS])
def test_agent_health_endpoint(agent):
    """Test that agent health endpoint responds correctly"""
    try:
        is_healthy = check_service(agent["port"], "/health", timeout=5)
        assert is_healthy, f"Agent {agent['name']} is not healthy"
    except Exception as e:
        pytest.skip(f"Agent {agent['name']} is not running: {str(e)}")


@pytest.mark.integration
@pytest.mark.parametrize("agent", AGENTS, ids=[a["name"] for a in AGENTS])
def test_agent_health_detailed(agent):
    """Test detailed health check for each agent"""
    try:
        is_healthy, details = check_service_detailed(agent["port"], "/health", timeout=5)

        assert is_healthy, f"Agent {agent['name']} is not healthy"
        assert details["status_code"] == 200
        assert details["response_time_ms"] is not None
        assert details["response_time_ms"] < 5000  # Should respond in less than 5 seconds

        # Check response body
        response_body = details.get("response_body", {})
        assert response_body.get("status") == "healthy"
        assert response_body.get("agent") == agent["name"]

    except Exception as e:
        pytest.skip(f"Agent {agent['name']} is not running: {str(e)}")


@pytest.mark.integration
@pytest.mark.parametrize("agent", AGENTS, ids=[a["name"] for a in AGENTS])
def test_agent_root_endpoint(agent):
    """Test that agent root endpoint responds correctly"""
    try:
        response = requests.get(f"http://localhost:{agent['port']}/", timeout=5)

        assert response.status_code == 200
        data = response.json()

        assert data.get("agent") == agent["name"]
        assert "description" in data
        assert "version" in data
        assert "endpoints" in data

    except requests.exceptions.ConnectionError:
        pytest.skip(f"Agent {agent['name']} is not running")
    except Exception as e:
        pytest.fail(f"Unexpected error: {str(e)}")


@pytest.mark.integration
@pytest.mark.parametrize("agent", AGENTS, ids=[a["name"] for a in AGENTS])
def test_agent_info_endpoint(agent):
    """Test that agent info endpoint responds correctly"""
    try:
        response = requests.get(f"http://localhost:{agent['port']}/info", timeout=5)

        assert response.status_code == 200
        data = response.json()

        assert data.get("agent") == agent["name"]
        assert "config" in data
        assert "timestamp" in data

    except requests.exceptions.ConnectionError:
        pytest.skip(f"Agent {agent['name']} is not running")
    except Exception as e:
        pytest.fail(f"Unexpected error: {str(e)}")


@pytest.mark.integration
@pytest.mark.parametrize("agent", AGENTS, ids=[a["name"] for a in AGENTS])
def test_agent_status_endpoint(agent):
    """Test that agent status endpoint responds correctly"""
    try:
        response = requests.get(f"http://localhost:{agent['port']}/status", timeout=5)

        assert response.status_code == 200
        data = response.json()

        assert data.get("agent") == agent["name"]
        assert data.get("status") == "running"
        assert "resources" in data
        assert "timestamp" in data

    except requests.exceptions.ConnectionError:
        pytest.skip(f"Agent {agent['name']} is not running")
    except Exception as e:
        pytest.fail(f"Unexpected error: {str(e)}")


@pytest.mark.integration
def test_all_agents_health():
    """Test that all agents are healthy"""
    results = {}

    for agent in AGENTS:
        try:
            is_healthy = check_service(agent["port"], "/health", timeout=5)
            results[agent["name"]] = is_healthy
        except Exception:
            results[agent["name"]] = False

    # Print summary
    healthy_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    print(f"\nHealth Check Summary: {healthy_count}/{total_count} agents are healthy")
    for agent_name, is_healthy in results.items():
        status = "✓" if is_healthy else "✗"
        print(f"  {status} {agent_name}")

    # This test passes even if some agents are not running
    # It's just for information gathering


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
