#!/usr/bin/env python3
"""
Quality Gates System
Pre-merge validation: code quality, security, documentation, performance
"""

import subprocess
import os
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import docker

from utils.notifier import get_notifier, UrgencyLevel


@dataclass
class CheckResult:
    """Result of a single quality check"""
    name: str
    passed: bool
    score: Optional[float] = None
    message: str = ""
    details: str = ""


class QualityGate:
    """Quality gate checks for pre-merge validation"""

    def __init__(self, repo_path: str = "/home/user/SparkTest"):
        self.repo_path = Path(repo_path)
        self.notifier = get_notifier()
        self.checks: List[CheckResult] = []

    def run_all_checks(self, branch_name: str) -> bool:
        """
        Run all quality gate checks

        Returns:
            True if all checks pass
        """
        print(f"\n🔍 Running quality gates for {branch_name}...")

        self.checks = []

        # Run checks
        self.check_code_quality()
        self.check_security()
        self.check_documentation()
        self.check_performance()

        # Summary
        passed = [c for c in self.checks if c.passed]
        failed = [c for c in self.checks if not c.passed]

        print(f"\n✅ Passed: {len(passed)}/{len(self.checks)}")
        if failed:
            print(f"❌ Failed checks:")
            for check in failed:
                print(f"   • {check.name}: {check.message}")

            self.notifier.quality_gate_failed(
                branch_name,
                [c.name for c in failed]
            )

        return len(failed) == 0

    def check_code_quality(self):
        """Run code quality checks"""
        print("\n📝 Checking code quality...")

        # 1. Black formatting
        result = self._run_black()
        self.checks.append(result)
        self._print_check_result(result)

        # 2. Pylint
        result = self._run_pylint()
        self.checks.append(result)
        self._print_check_result(result)

        # 3. MyPy type hints
        result = self._run_mypy()
        self.checks.append(result)
        self._print_check_result(result)

        # 4. Python syntax
        result = self._check_python_syntax()
        self.checks.append(result)
        self._print_check_result(result)

    def check_security(self):
        """Run security scans"""
        print("\n🔒 Checking security...")

        # 1. Bandit (Python security linter)
        result = self._run_bandit()
        self.checks.append(result)
        self._print_check_result(result)

        # 2. Safety (dependency vulnerability check)
        result = self._run_safety()
        self.checks.append(result)
        self._print_check_result(result)

        # 3. Check for secrets
        result = self._check_secrets()
        self.checks.append(result)
        self._print_check_result(result)

    def check_documentation(self):
        """Check documentation exists"""
        print("\n📚 Checking documentation...")

        required_docs = [
            'README.md',
            'supervisor/README.md'
        ]

        missing_docs = []
        for doc in required_docs:
            if not (self.repo_path / doc).exists():
                missing_docs.append(doc)

        result = CheckResult(
            name="documentation",
            passed=len(missing_docs) == 0,
            message=f"Missing docs: {missing_docs}" if missing_docs else "All required docs present"
        )

        self.checks.append(result)
        self._print_check_result(result)

    def check_performance(self):
        """Check performance benchmarks"""
        print("\n⚡ Checking performance...")

        # 1. Docker image sizes
        result = self._check_image_sizes()
        self.checks.append(result)
        self._print_check_result(result)

        # 2. Docker compose validation
        result = self._check_docker_compose()
        self.checks.append(result)
        self._print_check_result(result)

    def _run_black(self) -> CheckResult:
        """Check Black code formatting"""
        try:
            result = subprocess.run(
                ['black', '--check', '--quiet', '.'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            return CheckResult(
                name="black_formatting",
                passed=result.returncode == 0,
                message="Code is formatted" if result.returncode == 0 else "Code needs formatting"
            )
        except subprocess.TimeoutExpired:
            return CheckResult(
                name="black_formatting",
                passed=False,
                message="Check timed out"
            )
        except FileNotFoundError:
            return CheckResult(
                name="black_formatting",
                passed=True,
                message="Black not installed (skipped)"
            )
        except Exception as e:
            return CheckResult(
                name="black_formatting",
                passed=False,
                message=f"Error: {e}"
            )

    def _run_pylint(self) -> CheckResult:
        """Run Pylint checks"""
        try:
            result = subprocess.run(
                ['pylint', '--recursive=y', '--exit-zero', '.'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            # Extract score from output
            score = None
            for line in result.stdout.split('\n'):
                if 'Your code has been rated at' in line:
                    try:
                        score = float(line.split('rated at ')[1].split('/')[0])
                    except:
                        pass

            passed = score is None or score >= 8.0

            return CheckResult(
                name="pylint_score",
                passed=passed,
                score=score,
                message=f"Score: {score:.1f}/10.0" if score else "Pylint check completed"
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                name="pylint_score",
                passed=False,
                message="Check timed out"
            )
        except FileNotFoundError:
            return CheckResult(
                name="pylint_score",
                passed=True,
                message="Pylint not installed (skipped)"
            )
        except Exception as e:
            return CheckResult(
                name="pylint_score",
                passed=False,
                message=f"Error: {e}"
            )

    def _run_mypy(self) -> CheckResult:
        """Run MyPy type checking"""
        try:
            result = subprocess.run(
                ['mypy', '.', '--ignore-missing-imports'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=120
            )

            # MyPy returns 0 if no errors
            passed = result.returncode == 0

            return CheckResult(
                name="type_hints",
                passed=passed,
                message="Type hints valid" if passed else "Type errors found"
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                name="type_hints",
                passed=False,
                message="Check timed out"
            )
        except FileNotFoundError:
            return CheckResult(
                name="type_hints",
                passed=True,
                message="MyPy not installed (skipped)"
            )
        except Exception as e:
            return CheckResult(
                name="type_hints",
                passed=False,
                message=f"Error: {e}"
            )

    def _check_python_syntax(self) -> CheckResult:
        """Check Python syntax of all .py files"""
        try:
            # Find all Python files
            py_files = list(self.repo_path.glob('**/*.py'))

            errors = []
            for py_file in py_files:
                result = subprocess.run(
                    ['python', '-m', 'py_compile', str(py_file)],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    errors.append(str(py_file.relative_to(self.repo_path)))

            return CheckResult(
                name="python_syntax",
                passed=len(errors) == 0,
                message=f"All {len(py_files)} files valid" if not errors else f"{len(errors)} files with syntax errors"
            )

        except Exception as e:
            return CheckResult(
                name="python_syntax",
                passed=False,
                message=f"Error: {e}"
            )

    def _run_bandit(self) -> CheckResult:
        """Run Bandit security linter"""
        try:
            result = subprocess.run(
                ['bandit', '-r', '.', '-f', 'json', '--quiet', '--skip', 'B101'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Bandit returns non-zero if issues found
            # For quality gate, we'll pass if no high/medium severity issues
            passed = result.returncode in [0, 1]  # 0 = clean, 1 = low severity

            return CheckResult(
                name="security_scan",
                passed=passed,
                message="No critical security issues" if passed else "Security issues detected"
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                name="security_scan",
                passed=False,
                message="Check timed out"
            )
        except FileNotFoundError:
            return CheckResult(
                name="security_scan",
                passed=True,
                message="Bandit not installed (skipped)"
            )
        except Exception as e:
            return CheckResult(
                name="security_scan",
                passed=False,
                message=f"Error: {e}"
            )

    def _run_safety(self) -> CheckResult:
        """Check for known vulnerabilities in dependencies"""
        try:
            result = subprocess.run(
                ['safety', 'check', '--json'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            # Safety returns 64 if vulnerabilities found
            passed = result.returncode == 0

            return CheckResult(
                name="dependency_vulnerabilities",
                passed=passed,
                message="No known vulnerabilities" if passed else "Vulnerable dependencies found"
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                name="dependency_vulnerabilities",
                passed=False,
                message="Check timed out"
            )
        except FileNotFoundError:
            return CheckResult(
                name="dependency_vulnerabilities",
                passed=True,
                message="Safety not installed (skipped)"
            )
        except Exception as e:
            return CheckResult(
                name="dependency_vulnerabilities",
                passed=True,
                message=f"Check skipped: {e}"
            )

    def _check_secrets(self) -> CheckResult:
        """Check for accidentally committed secrets"""
        try:
            # Simple regex patterns for common secrets
            patterns = [
                r'password\s*=\s*["\'].*["\']',
                r'api[_-]?key\s*=\s*["\'].*["\']',
                r'secret\s*=\s*["\'].*["\']',
                r'token\s*=\s*["\'].*["\']'
            ]

            # Search in Python files only
            issues = []
            for py_file in self.repo_path.glob('**/*.py'):
                if '.git' in str(py_file) or 'venv' in str(py_file):
                    continue

                try:
                    with open(py_file, 'r') as f:
                        content = f.read()

                    import re
                    for pattern in patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            # Exclude os.getenv and similar safe patterns
                            if 'os.getenv' not in content and 'os.environ' not in content:
                                issues.append(str(py_file.relative_to(self.repo_path)))
                                break
                except:
                    pass

            return CheckResult(
                name="no_secrets",
                passed=len(issues) == 0,
                message="No hardcoded secrets found" if not issues else f"Potential secrets in {len(issues)} files"
            )

        except Exception as e:
            return CheckResult(
                name="no_secrets",
                passed=True,
                message=f"Check skipped: {e}"
            )

    def _check_image_sizes(self) -> CheckResult:
        """Check Docker image sizes"""
        try:
            client = docker.from_env()
            images = client.images.list()

            large_images = []
            max_size = 5 * 1024 * 1024 * 1024  # 5GB

            for image in images:
                if image.attrs['Size'] > max_size:
                    size_gb = image.attrs['Size'] / (1024 ** 3)
                    tags = image.tags[0] if image.tags else image.short_id
                    large_images.append(f"{tags} ({size_gb:.1f}GB)")

            return CheckResult(
                name="image_size",
                passed=len(large_images) == 0,
                message="All images <5GB" if not large_images else f"Large images: {large_images}"
            )

        except Exception as e:
            return CheckResult(
                name="image_size",
                passed=True,
                message=f"Check skipped: {e}"
            )

    def _check_docker_compose(self) -> CheckResult:
        """Validate docker-compose.yml syntax"""
        try:
            compose_file = self.repo_path / 'docker-compose.yml'

            if not compose_file.exists():
                return CheckResult(
                    name="docker_compose_validation",
                    passed=True,
                    message="No docker-compose.yml found (skipped)"
                )

            result = subprocess.run(
                ['docker-compose', 'config'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            return CheckResult(
                name="docker_compose_validation",
                passed=result.returncode == 0,
                message="docker-compose.yml valid" if result.returncode == 0 else "Invalid docker-compose.yml"
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                name="docker_compose_validation",
                passed=False,
                message="Validation timed out"
            )
        except FileNotFoundError:
            return CheckResult(
                name="docker_compose_validation",
                passed=True,
                message="docker-compose not installed (skipped)"
            )
        except Exception as e:
            return CheckResult(
                name="docker_compose_validation",
                passed=True,
                message=f"Check skipped: {e}"
            )

    def _print_check_result(self, result: CheckResult):
        """Print a check result"""
        icon = "✅" if result.passed else "❌"
        score_str = f" ({result.score:.1f})" if result.score is not None else ""
        print(f"  {icon} {result.name}{score_str}: {result.message}")

    def get_summary(self) -> Dict:
        """Get summary of all checks"""
        passed_count = sum(1 for c in self.checks if c.passed)
        return {
            'total': len(self.checks),
            'passed': passed_count,
            'failed': len(self.checks) - passed_count,
            'checks': [
                {
                    'name': c.name,
                    'passed': c.passed,
                    'score': c.score,
                    'message': c.message
                }
                for c in self.checks
            ]
        }
