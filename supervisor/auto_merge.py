#!/usr/bin/env python3
"""
Automated Merge Orchestration
Main supervisor script - runs every 10 minutes to integrate agent branches
"""

import sys
import os
from pathlib import Path

# Add supervisor to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.gitops import GitOpsManager, BranchStatus
from utils.config_loader import get_config_loader
from utils.notifier import get_notifier, UrgencyLevel
from conflict_resolver import ConflictResolver
from quality_gates import QualityGate
from integration_tests import IntegrationTestSuite
from typing import List, Dict
from datetime import datetime


class AutoMergeOrchestrator:
    """Orchestrates automated merge workflow"""

    def __init__(self, repo_path: str = "/home/user/SparkTest"):
        self.repo_path = repo_path
        self.git = GitOpsManager(repo_path)
        self.config = get_config_loader()
        self.notifier = get_notifier()
        self.conflict_resolver = ConflictResolver(repo_path)
        self.merge_log = []

    def run(self):
        """Main orchestration loop"""
        print("=" * 80)
        print(f"🤖 SUPERVISOR AUTO-MERGE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        # Step 1: Fetch all branches
        print("\n📥 Fetching remote branches...")
        if not self.git.fetch_all_branches():
            print("⚠️  Failed to fetch branches. Will retry next cycle.")
            return

        # Step 2: Get list of agent branches
        agent_branches = self.git.get_agent_branches()
        print(f"\n📋 Found {len(agent_branches)} agent branches:")
        for branch in agent_branches:
            print(f"   • {branch}")

        if not agent_branches:
            print("\n✅ No agent branches found. Nothing to merge.")
            return

        # Step 3: Get branches in dependency order
        ordered_branches = self._get_ordered_branches(agent_branches)

        # Step 4: Process each branch
        merged_count = 0
        blocked_count = 0
        failed_count = 0

        for branch in ordered_branches:
            result = self._process_branch(branch)

            if result == "merged":
                merged_count += 1
            elif result == "blocked":
                blocked_count += 1
            elif result == "failed":
                failed_count += 1

        # Step 5: Summary
        print("\n" + "=" * 80)
        print(f"📊 SUMMARY")
        print("=" * 80)
        print(f"✅ Merged: {merged_count}")
        print(f"⏳ Blocked: {blocked_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📝 Total: {len(ordered_branches)}")

        if merged_count > 0:
            self.notifier.integration_complete(merged_count, len(ordered_branches))

    def _get_ordered_branches(self, agent_branches: List[str]) -> List[str]:
        """
        Get branches ordered by dependency graph

        Returns branches that exist from the dependency order
        """
        dependency_order = self.config.get_dependency_order()

        # Filter to only branches that exist
        ordered = [b for b in dependency_order if b in agent_branches]

        # Add any remaining branches not in dependency graph
        remaining = [b for b in agent_branches if b not in ordered]
        ordered.extend(sorted(remaining))

        return ordered

    def _process_branch(self, branch_name: str) -> str:
        """
        Process a single branch for merging

        Returns:
            "merged" - successfully merged
            "blocked" - blocked by dependency or conflict
            "failed" - merge failed
            "skipped" - nothing to merge
        """
        print("\n" + "-" * 80)
        print(f"🔍 Processing: {branch_name}")
        print("-" * 80)

        # Get branch status
        status = self.git.get_branch_status(branch_name)

        if not status.exists:
            print(f"⚠️  Branch does not exist (skipped)")
            return "skipped"

        if status.commits_ahead == 0:
            print(f"✅ Already up to date (0 commits ahead)")
            return "skipped"

        print(f"📊 Status:")
        print(f"   • Commits ahead: {status.commits_ahead}")
        print(f"   • Last commit: {status.last_commit_sha}")
        print(f"   • Message: {status.last_commit_message}")

        # Check dependencies
        if not self._check_dependencies(branch_name):
            print(f"🚧 BLOCKED: Dependencies not merged yet")
            return "blocked"

        # Check for conflicts
        if status.has_conflicts:
            print(f"⚠️  Conflicts detected in {len(status.conflict_files)} files")
            return self._handle_conflicts(branch_name, status.conflict_files)

        # Run quality gates
        print(f"\n🔍 Running quality gates...")
        gate = QualityGate(self.repo_path)

        if not gate.run_all_checks(branch_name):
            print(f"❌ Quality gates FAILED")
            self.notifier.quality_gate_failed(
                branch_name,
                [c.name for c in gate.checks if not c.passed]
            )
            return "failed"

        print(f"✅ Quality gates PASSED")

        # Attempt merge
        print(f"\n🔀 Attempting merge...")
        merge_result = self.git.merge_branch(
            branch_name,
            message=f"Merge {branch_name} - Auto-integrated by supervisor"
        )

        if not merge_result.success:
            print(f"❌ Merge FAILED: {merge_result.error}")

            if merge_result.conflicts:
                return self._handle_conflicts(branch_name, merge_result.conflicts)

            return "failed"

        print(f"✅ Merge successful: {merge_result.commit_sha}")

        # Run integration tests
        print(f"\n🧪 Running integration tests...")
        test_suite = IntegrationTestSuite(self.repo_path)

        if not test_suite.run_all_tests(quick=True):
            print(f"🔥 Integration tests FAILED - Rolling back...")

            failed_tests = test_suite.get_failed_tests()
            self.notifier.test_failure(branch_name, failed_tests)

            # Rollback merge
            if self.git.rollback_merge():
                print(f"✅ Rollback successful")
            else:
                print(f"❌ Rollback FAILED - Manual intervention required!")
                self.notifier.notify(
                    f"CRITICAL: Failed to rollback {branch_name}. Manual intervention required!",
                    UrgencyLevel.CRITICAL
                )

            return "failed"

        print(f"✅ Integration tests PASSED")

        # Push to remote
        print(f"\n📤 Pushing to remote...")
        if self.git.push_branch('main'):
            print(f"✅ Push successful")
            self.notifier.merge_success(branch_name, merge_result.commit_sha)
            self._log_merge(branch_name, merge_result.commit_sha, True)
            return "merged"
        else:
            print(f"⚠️  Push failed - Merge successful locally but not pushed")
            self._log_merge(branch_name, merge_result.commit_sha, False)
            return "merged"  # Still count as merged locally

    def _check_dependencies(self, branch_name: str) -> bool:
        """
        Check if all dependencies for a branch are merged

        Returns True if all dependencies are satisfied
        """
        agent_info = self.config.get_agent_info(branch_name)

        if not agent_info:
            # No dependency info - assume can merge
            return True

        # Get dependency layer
        layers = self.config.load_agent_dependencies().get('dependency_layers', {})

        for layer_name, layer_info in layers.items():
            if branch_name in layer_info.get('agents', []):
                # Check if this layer has dependencies
                depends_on = layer_info.get('depends_on', [])

                for dep_agent in depends_on:
                    # Check if dependency is merged (has 0 commits ahead)
                    dep_status = self.git.get_branch_status(dep_agent)

                    if dep_status.exists and dep_status.commits_ahead > 0:
                        print(f"   ⚠️  Waiting for {dep_agent} to be merged first")
                        self.notifier.blocker_detected(
                            branch_name,
                            "dependency",
                            f"Waiting for {dep_agent} to merge first"
                        )
                        return False

                return True

        return True

    def _handle_conflicts(self, branch_name: str, conflict_files: List[str]) -> str:
        """
        Handle merge conflicts

        Returns "merged" if resolved, "blocked" otherwise
        """
        print(f"\n🔧 Attempting to resolve conflicts...")

        resolutions = self.conflict_resolver.resolve_conflicts(conflict_files)

        resolved = [r for r in resolutions if r.success and r.auto_resolved]
        unresolved = [r for r in resolutions if not r.success or not r.auto_resolved]

        if unresolved:
            print(f"\n⚠️  {len(unresolved)} conflicts require manual resolution:")
            for r in unresolved:
                print(f"   • {r.file} ({r.strategy})")

            # Create issue for manual resolution
            self.conflict_resolver.create_conflict_issue(
                branch_name,
                [r.file for r in unresolved]
            )

            return "blocked"

        print(f"✅ All conflicts auto-resolved")

        # Try merge again
        merge_result = self.git.merge_branch(branch_name)

        if merge_result.success:
            return "merged"
        else:
            print(f"❌ Merge still failed after conflict resolution")
            return "failed"

    def _log_merge(self, branch_name: str, commit_sha: str, pushed: bool):
        """Log merge event"""
        self.merge_log.append({
            'timestamp': datetime.now().isoformat(),
            'branch': branch_name,
            'commit': commit_sha,
            'pushed': pushed
        })


def main():
    """Main entry point"""
    orchestrator = AutoMergeOrchestrator()
    orchestrator.run()


if __name__ == "__main__":
    main()
