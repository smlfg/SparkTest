#!/usr/bin/env python3
"""
Conflict Resolver
Automated conflict resolution based on configurable rules
"""

import os
import subprocess
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import yaml

from utils.config_loader import get_config_loader
from utils.notifier import get_notifier, UrgencyLevel


@dataclass
class ConflictResolution:
    """Result of conflict resolution attempt"""
    success: bool
    file: str
    strategy: str
    auto_resolved: bool
    error: Optional[str] = None


class ConflictResolver:
    """Resolves merge conflicts automatically when possible"""

    def __init__(self, repo_path: str = "/home/user/SparkTest"):
        self.repo_path = Path(repo_path)
        self.config_loader = get_config_loader()
        self.notifier = get_notifier()

    def resolve_conflicts(self, conflict_files: List[str]) -> List[ConflictResolution]:
        """
        Attempt to resolve list of conflicting files

        Args:
            conflict_files: List of file paths with conflicts

        Returns:
            List of ConflictResolution results
        """
        results = []

        for filepath in conflict_files:
            result = self.resolve_file(filepath)
            results.append(result)

            if result.success and result.auto_resolved:
                print(f"  ✅ Auto-resolved {filepath} using {result.strategy}")
            elif result.success:
                print(f"  ℹ️  Resolved {filepath} using {result.strategy}")
            else:
                print(f"  ❌ Failed to resolve {filepath}: {result.error}")

        return results

    def resolve_file(self, filepath: str) -> ConflictResolution:
        """
        Attempt to resolve a single conflicting file

        Args:
            filepath: Path to conflicting file (relative to repo root)

        Returns:
            ConflictResolution result
        """
        # Get resolution rule for this file
        rule = self.config_loader.get_conflict_rule(filepath)

        if not rule:
            return ConflictResolution(
                success=False,
                file=filepath,
                strategy="unknown",
                auto_resolved=False,
                error="No resolution rule found"
            )

        strategy = rule.get('strategy', 'fail_on_conflict')
        auto_resolve = rule.get('auto_resolve', False)

        # If auto-resolve is disabled, don't attempt resolution
        if not auto_resolve:
            return ConflictResolution(
                success=False,
                file=filepath,
                strategy=strategy,
                auto_resolved=False,
                error="Manual resolution required per policy"
            )

        # Apply resolution strategy
        if strategy == 'merge_all_services':
            return self._merge_docker_compose(filepath)
        elif strategy == 'union_and_dedupe':
            return self._union_and_dedupe(filepath)
        elif strategy == 'merge_with_namespace':
            return self._merge_with_namespace(filepath)
        elif strategy == 'append_both':
            return self._append_both(filepath)
        elif strategy == 'union':
            return self._union_lines(filepath)
        elif strategy == 'keep_theirs':
            return self._keep_theirs(filepath)
        elif strategy == 'merge_sections':
            return self._merge_sections(filepath)
        else:
            return ConflictResolution(
                success=False,
                file=filepath,
                strategy=strategy,
                auto_resolved=False,
                error=f"Unknown strategy: {strategy}"
            )

    def _merge_docker_compose(self, filepath: str) -> ConflictResolution:
        """
        Merge docker-compose.yml: combine all services from both versions
        """
        try:
            full_path = self.repo_path / filepath

            # Extract conflicting sections
            with open(full_path, 'r') as f:
                content = f.read()

            # Parse conflict markers
            ours, theirs = self._extract_conflict_sections(content)

            # Parse both YAML sections
            ours_yaml = yaml.safe_load(ours)
            theirs_yaml = yaml.safe_load(theirs)

            # Merge services
            merged = {
                'version': ours_yaml.get('version', '3.8'),
                'services': {}
            }

            # Combine services from both
            if 'services' in ours_yaml:
                merged['services'].update(ours_yaml['services'])
            if 'services' in theirs_yaml:
                merged['services'].update(theirs_yaml['services'])

            # Combine volumes
            if 'volumes' in ours_yaml or 'volumes' in theirs_yaml:
                merged['volumes'] = {}
                if 'volumes' in ours_yaml:
                    merged['volumes'].update(ours_yaml.get('volumes', {}))
                if 'volumes' in theirs_yaml:
                    merged['volumes'].update(theirs_yaml.get('volumes', {}))

            # Combine networks
            if 'networks' in ours_yaml or 'networks' in theirs_yaml:
                merged['networks'] = {}
                if 'networks' in ours_yaml:
                    merged['networks'].update(ours_yaml.get('networks', {}))
                if 'networks' in theirs_yaml:
                    merged['networks'].update(theirs_yaml.get('networks', {}))

            # Write merged version
            with open(full_path, 'w') as f:
                yaml.dump(merged, f, default_flow_style=False, sort_keys=False)

            # Validate
            validation_result = subprocess.run(
                ['docker-compose', 'config'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if validation_result.returncode != 0:
                return ConflictResolution(
                    success=False,
                    file=filepath,
                    strategy='merge_all_services',
                    auto_resolved=False,
                    error=f"Validation failed: {validation_result.stderr}"
                )

            # Mark as resolved in git
            subprocess.run(['git', 'add', filepath], cwd=self.repo_path, check=True)

            return ConflictResolution(
                success=True,
                file=filepath,
                strategy='merge_all_services',
                auto_resolved=True
            )

        except Exception as e:
            return ConflictResolution(
                success=False,
                file=filepath,
                strategy='merge_all_services',
                auto_resolved=False,
                error=str(e)
            )

    def _union_and_dedupe(self, filepath: str) -> ConflictResolution:
        """
        Union of lines with deduplication (for requirements.txt, etc.)
        """
        try:
            full_path = self.repo_path / filepath

            with open(full_path, 'r') as f:
                content = f.read()

            ours, theirs = self._extract_conflict_sections(content)

            # Split into lines and dedupe
            ours_lines = set(line.strip() for line in ours.split('\n') if line.strip())
            theirs_lines = set(line.strip() for line in theirs.split('\n') if line.strip())

            # Union
            all_lines = sorted(ours_lines | theirs_lines)

            # Write merged version
            with open(full_path, 'w') as f:
                f.write('\n'.join(all_lines) + '\n')

            # Mark as resolved
            subprocess.run(['git', 'add', filepath], cwd=self.repo_path, check=True)

            return ConflictResolution(
                success=True,
                file=filepath,
                strategy='union_and_dedupe',
                auto_resolved=True
            )

        except Exception as e:
            return ConflictResolution(
                success=False,
                file=filepath,
                strategy='union_and_dedupe',
                auto_resolved=False,
                error=str(e)
            )

    def _merge_with_namespace(self, filepath: str) -> ConflictResolution:
        """
        Merge .env files by prefixing variables with agent names
        """
        try:
            full_path = self.repo_path / filepath

            with open(full_path, 'r') as f:
                content = f.read()

            ours, theirs = self._extract_conflict_sections(content)

            # For now, just keep both sections separated by comments
            merged = f"# Variables from main branch\n{ours}\n\n# Variables from merge branch\n{theirs}\n"

            with open(full_path, 'w') as f:
                f.write(merged)

            subprocess.run(['git', 'add', filepath], cwd=self.repo_path, check=True)

            return ConflictResolution(
                success=True,
                file=filepath,
                strategy='merge_with_namespace',
                auto_resolved=True
            )

        except Exception as e:
            return ConflictResolution(
                success=False,
                file=filepath,
                strategy='merge_with_namespace',
                auto_resolved=False,
                error=str(e)
            )

    def _append_both(self, filepath: str) -> ConflictResolution:
        """
        Append content from both branches (for markdown, docs)
        """
        try:
            full_path = self.repo_path / filepath

            with open(full_path, 'r') as f:
                content = f.read()

            ours, theirs = self._extract_conflict_sections(content)

            merged = f"{ours}\n\n{theirs}\n"

            with open(full_path, 'w') as f:
                f.write(merged)

            subprocess.run(['git', 'add', filepath], cwd=self.repo_path, check=True)

            return ConflictResolution(
                success=True,
                file=filepath,
                strategy='append_both',
                auto_resolved=True
            )

        except Exception as e:
            return ConflictResolution(
                success=False,
                file=filepath,
                strategy='append_both',
                auto_resolved=False,
                error=str(e)
            )

    def _union_lines(self, filepath: str) -> ConflictResolution:
        """
        Union of all lines (for .gitignore, etc.)
        """
        return self._union_and_dedupe(filepath)

    def _keep_theirs(self, filepath: str) -> ConflictResolution:
        """
        Keep the version from the branch being merged
        """
        try:
            # Use git checkout --theirs
            result = subprocess.run(
                ['git', 'checkout', '--theirs', filepath],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                return ConflictResolution(
                    success=False,
                    file=filepath,
                    strategy='keep_theirs',
                    auto_resolved=False,
                    error=result.stderr
                )

            subprocess.run(['git', 'add', filepath], cwd=self.repo_path, check=True)

            return ConflictResolution(
                success=True,
                file=filepath,
                strategy='keep_theirs',
                auto_resolved=True
            )

        except Exception as e:
            return ConflictResolution(
                success=False,
                file=filepath,
                strategy='keep_theirs',
                auto_resolved=False,
                error=str(e)
            )

    def _merge_sections(self, filepath: str) -> ConflictResolution:
        """
        Merge configuration sections (for pytest.ini, etc.)
        """
        try:
            full_path = self.repo_path / filepath

            with open(full_path, 'r') as f:
                content = f.read()

            ours, theirs = self._extract_conflict_sections(content)

            # For INI files, just combine both sections
            merged = f"{ours}\n{theirs}\n"

            with open(full_path, 'w') as f:
                f.write(merged)

            subprocess.run(['git', 'add', filepath], cwd=self.repo_path, check=True)

            return ConflictResolution(
                success=True,
                file=filepath,
                strategy='merge_sections',
                auto_resolved=True
            )

        except Exception as e:
            return ConflictResolution(
                success=False,
                file=filepath,
                strategy='merge_sections',
                auto_resolved=False,
                error=str(e)
            )

    def _extract_conflict_sections(self, content: str) -> Tuple[str, str]:
        """
        Extract 'ours' and 'theirs' sections from conflict markers

        Returns:
            (ours_content, theirs_content)
        """
        lines = content.split('\n')
        ours_lines = []
        theirs_lines = []
        current_section = None

        for line in lines:
            if line.startswith('<<<<<<<'):
                current_section = 'ours'
            elif line.startswith('======='):
                current_section = 'theirs'
            elif line.startswith('>>>>>>>'):
                current_section = None
            elif current_section == 'ours':
                ours_lines.append(line)
            elif current_section == 'theirs':
                theirs_lines.append(line)
            elif current_section is None:
                # Lines outside conflicts - include in both
                ours_lines.append(line)
                theirs_lines.append(line)

        return ('\n'.join(ours_lines), '\n'.join(theirs_lines))

    def create_conflict_issue(self, branch: str, conflict_files: List[str]) -> Optional[int]:
        """
        Create GitHub issue for manual conflict resolution

        Args:
            branch: Branch name with conflicts
            conflict_files: List of conflicting files

        Returns:
            Issue number if created, None otherwise
        """
        # For now, just notify
        self.notifier.merge_conflict(branch, conflict_files)

        # TODO: Implement GitHub issue creation via API
        # This would require GitHub token and API integration
        print(f"\n⚠️  Manual conflict resolution required for {branch}")
        print(f"   Conflicting files:")
        for f in conflict_files:
            rule = self.config_loader.get_conflict_rule(f)
            print(f"     • {f} (strategy: {rule.get('strategy', 'unknown')})")

        return None
