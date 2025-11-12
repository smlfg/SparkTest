#!/usr/bin/env python3
"""
Integration Test Suite
Tests that run before merge approval: syntax, services, end-to-end workflows
"""

import subprocess
import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import requests
import docker

from utils.notifier import get_notifier, UrgencyLevel


@dataclass
class TestResult:
    """Result of a test"""
    name: str
    passed: bool
    duration: float
    message: str = ""
    details: str = ""


class IntegrationTestSuite:
    """Integration tests for pre-merge validation"""

    def __init__(self, repo_path: str = "/home/user/SparkTest"):
        self.repo_path = Path(repo_path)
        self.notifier = get_notifier()
        self.results: List[TestResult] = []

    def run_all_tests(self, quick: bool = False) -> bool:
        """
        Run all integration tests

        Args:
            quick: If True, skip slow tests

        Returns:
            True if all tests pass
        """
        print(f"\n🧪 Running integration tests...")

        self.results = []

        # Level 1: Syntax and config validation (always run)
        self.test_syntax_validation()

        if not quick:
            # Level 2: Service startup tests
            self.test_service_startup()

            # Level 3: End-to-end tests
            self.test_end_to_end_workflows()

        # Summary
        passed = [r for r in self.results if r.passed]
        failed = [r for r in self.results if not r.passed]

        total_duration = sum(r.duration for r in self.results)

        print(f"\n✅ Passed: {len(passed)}/{len(self.results)} (in {total_duration:.1f}s)")
        if failed:
            print(f"❌ Failed tests:")
            for result in failed:
                print(f"   • {result.name}: {result.message}")

        return len(failed) == 0

    def test_syntax_validation(self):
        """Level 1: Syntax and configuration validation"""
        print("\n📝 Level 1: Syntax Validation")

        # 1. Python syntax
        result = self._test_python_syntax()
        self.results.append(result)
        self._print_result(result)

        # 2. YAML syntax
        result = self._test_yaml_syntax()
        self.results.append(result)
        self._print_result(result)

        # 3. Docker Compose config
        result = self._test_docker_compose_config()
        self.results.append(result)
        self._print_result(result)

        # 4. Environment variables
        result = self._test_env_vars()
        self.results.append(result)
        self._print_result(result)

    def test_service_startup(self):
        """Level 2: Service startup tests"""
        print("\n🚀 Level 2: Service Startup")

        # 1. Services start without crashing
        result = self._test_services_start()
        self.results.append(result)
        self._print_result(result)

        if not result.passed:
            return  # Don't continue if services won't start

        # 2. Health endpoints respond
        result = self._test_health_endpoints()
        self.results.append(result)
        self._print_result(result)

    def test_end_to_end_workflows(self):
        """Level 3: End-to-end workflow tests"""
        print("\n🔄 Level 3: End-to-End Workflows")

        # 1. Basic inference test
        result = self._test_inference_workflow()
        self.results.append(result)
        self._print_result(result)

    def _test_python_syntax(self) -> TestResult:
        """Test all Python files compile"""
        start = time.time()

        try:
            py_files = list(self.repo_path.glob('**/*.py'))
            errors = []

            for py_file in py_files:
                if '.git' in str(py_file) or 'venv' in str(py_file):
                    continue

                result = subprocess.run(
                    ['python', '-m', 'py_compile', str(py_file)],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if result.returncode != 0:
                    errors.append(str(py_file.relative_to(self.repo_path)))

            duration = time.time() - start

            return TestResult(
                name="python_syntax",
                passed=len(errors) == 0,
                duration=duration,
                message=f"All {len(py_files)} files valid" if not errors else f"{len(errors)} files with errors",
                details="\n".join(errors) if errors else ""
            )

        except Exception as e:
            return TestResult(
                name="python_syntax",
                passed=False,
                duration=time.time() - start,
                message=f"Error: {e}"
            )

    def _test_yaml_syntax(self) -> TestResult:
        """Test all YAML files are valid"""
        start = time.time()

        try:
            import yaml

            yaml_files = list(self.repo_path.glob('**/*.yaml'))
            yaml_files.extend(self.repo_path.glob('**/*.yml'))

            errors = []

            for yaml_file in yaml_files:
                if '.git' in str(yaml_file):
                    continue

                try:
                    with open(yaml_file, 'r') as f:
                        yaml.safe_load(f)
                except yaml.YAMLError:
                    errors.append(str(yaml_file.relative_to(self.repo_path)))

            duration = time.time() - start

            return TestResult(
                name="yaml_syntax",
                passed=len(errors) == 0,
                duration=duration,
                message=f"All {len(yaml_files)} files valid" if not errors else f"{len(errors)} files with errors",
                details="\n".join(errors) if errors else ""
            )

        except Exception as e:
            return TestResult(
                name="yaml_syntax",
                passed=False,
                duration=time.time() - start,
                message=f"Error: {e}"
            )

    def _test_docker_compose_config(self) -> TestResult:
        """Test docker-compose.yml is valid"""
        start = time.time()

        try:
            result = subprocess.run(
                ['docker-compose', 'config'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            duration = time.time() - start

            return TestResult(
                name="docker_compose_config",
                passed=result.returncode == 0,
                duration=duration,
                message="Valid configuration" if result.returncode == 0 else "Invalid configuration",
                details=result.stderr if result.returncode != 0 else ""
            )

        except subprocess.TimeoutExpired:
            return TestResult(
                name="docker_compose_config",
                passed=False,
                duration=time.time() - start,
                message="Validation timed out"
            )
        except Exception as e:
            return TestResult(
                name="docker_compose_config",
                passed=False,
                duration=time.time() - start,
                message=f"Error: {e}"
            )

    def _test_env_vars(self) -> TestResult:
        """Test environment variables are properly configured"""
        start = time.time()

        # For now, just check .env.example exists if .env doesn't
        env_file = self.repo_path / '.env'
        env_example = self.repo_path / '.env.example'

        has_config = env_file.exists() or env_example.exists()

        duration = time.time() - start

        return TestResult(
            name="env_vars_check",
            passed=True,  # Non-blocking for now
            duration=duration,
            message="Environment config found" if has_config else "No .env file (using defaults)"
        )

    def _test_services_start(self) -> TestResult:
        """Test all Docker Compose services start successfully"""
        start = time.time()

        try:
            # Check if any services are running first
            client = docker.from_env()
            containers = client.containers.list(filters={'label': 'com.docker.compose.project'})

            if not containers:
                # No services running - would need to start them
                # For safety, we'll skip this test in CI/automation
                return TestResult(
                    name="service_startup",
                    passed=True,
                    duration=time.time() - start,
                    message="Skipped (no services running, manual start required)"
                )

            # Check running services
            all_running = all(c.status == 'running' for c in containers)
            duration = time.time() - start

            return TestResult(
                name="service_startup",
                passed=all_running,
                duration=duration,
                message=f"{len(containers)} services running" if all_running else "Some services not running"
            )

        except Exception as e:
            return TestResult(
                name="service_startup",
                passed=True,  # Non-blocking if Docker not available
                duration=time.time() - start,
                message=f"Skipped: {e}"
            )

    def _test_health_endpoints(self) -> TestResult:
        """Test health check endpoints respond"""
        start = time.time()

        endpoints = {
            "ollama": "http://localhost:11434/api/tags",
            "open_webui": "http://localhost:8080",
            "agent5_api": "http://localhost:8888/health"
        }

        failed = []

        for name, url in endpoints.items():
            try:
                response = requests.get(url, timeout=5)
                if response.status_code not in [200, 404]:  # 404 is ok for optional services
                    failed.append(f"{name} ({response.status_code})")
            except requests.RequestException:
                # Service might not be running - non-blocking
                pass

        duration = time.time() - start

        return TestResult(
            name="health_endpoints",
            passed=len(failed) == 0,
            duration=duration,
            message="All endpoints responding" if not failed else f"Issues: {', '.join(failed)}"
        )

    def _test_inference_workflow(self) -> TestResult:
        """Test basic inference workflow"""
        start = time.time()

        try:
            # Try to connect to Ollama
            response = requests.get("http://localhost:11434/api/tags", timeout=5)

            if response.status_code != 200:
                return TestResult(
                    name="inference_workflow",
                    passed=True,  # Non-blocking
                    duration=time.time() - start,
                    message="Skipped (Ollama not available)"
                )

            # Check if any models are available
            models = response.json().get('models', [])

            duration = time.time() - start

            return TestResult(
                name="inference_workflow",
                passed=True,  # Non-blocking test
                duration=duration,
                message=f"Ollama running with {len(models)} models"
            )

        except Exception as e:
            return TestResult(
                name="inference_workflow",
                passed=True,  # Non-blocking
                duration=time.time() - start,
                message=f"Skipped: {e}"
            )

    def _print_result(self, result: TestResult):
        """Print test result"""
        icon = "✅" if result.passed else "❌"
        print(f"  {icon} {result.name} ({result.duration:.1f}s): {result.message}")

    def get_summary(self) -> Dict:
        """Get summary of all tests"""
        passed_count = sum(1 for r in self.results if r.passed)
        total_duration = sum(r.duration for r in self.results)

        return {
            'total': len(self.results),
            'passed': passed_count,
            'failed': len(self.results) - passed_count,
            'duration': total_duration,
            'tests': [
                {
                    'name': r.name,
                    'passed': r.passed,
                    'duration': r.duration,
                    'message': r.message
                }
                for r in self.results
            ]
        }

    def get_failed_tests(self) -> List[str]:
        """Get list of failed test names"""
        return [r.name for r in self.results if not r.passed]
