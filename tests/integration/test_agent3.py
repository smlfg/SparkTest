#!/usr/bin/env python3
"""
Integration tests for Agent 3: Development Environments
"""

import pytest
import subprocess
import time
from shared.health_check import check_service, wait_for_service
from shared.utils.docker_utils import is_container_running, check_docker


@pytest.fixture(scope="module")
def docker_available():
    """Check if Docker is available"""
    return check_docker()


class TestAgent3Integration:
    """Integration tests for Agent 3"""

    def test_docker_available(self, docker_available):
        """Test that Docker is available"""
        assert docker_available, "Docker is not available"

    def test_launch_script_exists(self):
        """Test that launch script exists and is executable"""
        import os
        script_path = "agents/agent3_dev_environments/agent3_launch.sh"
        assert os.path.exists(script_path), f"Launch script not found: {script_path}"
        assert os.access(script_path, os.X_OK), f"Launch script not executable: {script_path}"

    def test_launch_script_help(self):
        """Test launch script help command"""
        result = subprocess.run(
            ["./agents/agent3_dev_environments/agent3_launch.sh", "help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "Commands:" in result.stdout

    def test_launch_script_status(self):
        """Test launch script status command"""
        result = subprocess.run(
            ["./agents/agent3_dev_environments/agent3_launch.sh", "status"],
            capture_output=True,
            text=True,
            timeout=10
        )
        # Should succeed regardless of service status
        assert result.returncode == 0

    @pytest.mark.slow
    @pytest.mark.skipif(not check_docker(), reason="Docker not available")
    def test_jax_container_launch(self):
        """Test JAX container launch"""
        # This is a placeholder for actual container testing
        # In real environment, would launch container and verify
        pass

    def test_templates_exist(self):
        """Test that development templates exist"""
        import os
        templates_dir = "agents/agent3_dev_environments/templates"
        expected_templates = [
            "python-ml.env",
            "rust-dev.env",
            "go-dev.env",
            "cpp-dev.env",
            "devcontainer.json"
        ]

        for template in expected_templates:
            template_path = os.path.join(templates_dir, template)
            assert os.path.exists(template_path), f"Template not found: {template}"

    def test_playbooks_exist(self):
        """Test that playbooks exist"""
        import os
        playbooks_dir = "agents/agent3_dev_environments/playbooks"
        expected_playbooks = [
            "vscode.sh",
            "vscode.yml",
            "jax.sh",
            "jax.yml"
        ]

        for playbook in expected_playbooks:
            playbook_path = os.path.join(playbooks_dir, playbook)
            assert os.path.exists(playbook_path), f"Playbook not found: {playbook}"

    def test_dockerfile_exists(self):
        """Test that Dockerfile exists"""
        import os
        dockerfile = "agents/agent3_dev_environments/containers/jax-arm64.Dockerfile"
        assert os.path.exists(dockerfile), f"Dockerfile not found: {dockerfile}"
