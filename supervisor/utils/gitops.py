#!/usr/bin/env python3
"""
GitOps Utilities
Handles all Git operations for supervisor: branch monitoring, merging, conflict detection
"""

import subprocess
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import git
from git import Repo, GitCommandError


@dataclass
class BranchStatus:
    """Status of an agent branch"""
    name: str
    exists: bool
    commits_ahead: int
    last_commit_sha: str
    last_commit_message: str
    last_commit_date: datetime
    has_conflicts: bool
    conflict_files: List[str]


@dataclass
class MergeResult:
    """Result of a merge operation"""
    success: bool
    branch: str
    commit_sha: Optional[str]
    conflicts: List[str]
    error: Optional[str]


class GitOpsManager:
    """Manages Git operations for supervisor"""

    def __init__(self, repo_path: str = "/home/user/SparkTest"):
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        self.base_branch = "main"

    def fetch_all_branches(self, retry_count: int = 4) -> bool:
        """
        Fetch all remote branches with exponential backoff retry
        Returns True if successful
        """
        backoff_delays = [2, 4, 8, 16]  # seconds

        for attempt in range(retry_count):
            try:
                self.repo.remotes.origin.fetch()
                print(f"✅ Successfully fetched all branches")
                return True
            except GitCommandError as e:
                if attempt < retry_count - 1:
                    delay = backoff_delays[attempt]
                    print(f"⚠️  Fetch failed (attempt {attempt + 1}/{retry_count}), retrying in {delay}s...")
                    import time
                    time.sleep(delay)
                else:
                    print(f"❌ Failed to fetch branches after {retry_count} attempts: {e}")
                    return False
        return False

    def get_agent_branches(self) -> List[str]:
        """
        Get list of all agent branches (both local and remote)
        Returns branches matching pattern: agent[1-10]-*
        """
        branches = set()

        # Local branches
        for branch in self.repo.branches:
            if self._is_agent_branch(branch.name):
                branches.add(branch.name)

        # Remote branches
        for ref in self.repo.remotes.origin.refs:
            branch_name = ref.name.replace('origin/', '')
            if self._is_agent_branch(branch_name):
                branches.add(branch_name)

        return sorted(list(branches))

    def _is_agent_branch(self, branch_name: str) -> bool:
        """Check if branch name matches agent pattern"""
        import re
        return bool(re.match(r'agent([1-9]|10)-', branch_name))

    def get_branch_status(self, branch_name: str) -> BranchStatus:
        """
        Get detailed status of a branch
        """
        # Check if branch exists
        branch_exists = False
        branch_ref = None

        # Check local branches
        if branch_name in [b.name for b in self.repo.branches]:
            branch_exists = True
            branch_ref = self.repo.branches[branch_name]
        # Check remote branches
        elif f'origin/{branch_name}' in [r.name for r in self.repo.remotes.origin.refs]:
            branch_exists = True
            branch_ref = self.repo.remotes.origin.refs[f'origin/{branch_name}']

        if not branch_exists or branch_ref is None:
            return BranchStatus(
                name=branch_name,
                exists=False,
                commits_ahead=0,
                last_commit_sha="",
                last_commit_message="",
                last_commit_date=datetime.now(),
                has_conflicts=False,
                conflict_files=[]
            )

        # Get commits ahead of base branch
        try:
            base_commit = self.repo.heads[self.base_branch].commit
            branch_commit = branch_ref.commit

            commits_ahead = len(list(self.repo.iter_commits(f'{self.base_branch}..{branch_commit.hexsha}')))

            # Check for potential conflicts
            conflicts, conflict_files = self._check_conflicts(branch_name)

            return BranchStatus(
                name=branch_name,
                exists=True,
                commits_ahead=commits_ahead,
                last_commit_sha=branch_commit.hexsha[:8],
                last_commit_message=branch_commit.message.strip(),
                last_commit_date=datetime.fromtimestamp(branch_commit.committed_date),
                has_conflicts=conflicts,
                conflict_files=conflict_files
            )

        except Exception as e:
            print(f"⚠️  Error getting status for {branch_name}: {e}")
            return BranchStatus(
                name=branch_name,
                exists=True,
                commits_ahead=0,
                last_commit_sha="",
                last_commit_message="",
                last_commit_date=datetime.now(),
                has_conflicts=False,
                conflict_files=[]
            )

    def _check_conflicts(self, branch_name: str) -> Tuple[bool, List[str]]:
        """
        Check if merging branch would cause conflicts
        Returns (has_conflicts, list_of_conflicting_files)
        """
        try:
            # Save current branch
            original_branch = self.repo.active_branch.name

            # Create a temporary working directory for merge test
            result = subprocess.run(
                ['git', 'merge-tree', self.base_branch, branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )

            # Check for conflict markers in output
            if '<<<<<<<' in result.stdout or 'CONFLICT' in result.stderr:
                # Parse conflict files
                conflict_files = []
                for line in result.stdout.split('\n'):
                    if line.startswith('CONFLICT'):
                        # Extract filename from conflict message
                        parts = line.split()
                        if len(parts) > 2:
                            conflict_files.append(parts[-1])

                return (True, conflict_files)

            return (False, [])

        except Exception as e:
            print(f"⚠️  Error checking conflicts for {branch_name}: {e}")
            return (False, [])

    def merge_branch(self, branch_name: str, no_ff: bool = True,
                    message: Optional[str] = None) -> MergeResult:
        """
        Merge a branch into the current branch (typically main)

        Args:
            branch_name: Name of branch to merge
            no_ff: Create merge commit even if fast-forward possible
            message: Custom merge commit message

        Returns:
            MergeResult with success status and details
        """
        try:
            # Ensure we're on base branch
            if self.repo.active_branch.name != self.base_branch:
                self.repo.heads[self.base_branch].checkout()

            # Check if branch exists
            if branch_name not in [b.name for b in self.repo.branches]:
                # Try to check out from remote
                try:
                    self.repo.git.checkout('-b', branch_name, f'origin/{branch_name}')
                    self.repo.heads[self.base_branch].checkout()
                except GitCommandError:
                    return MergeResult(
                        success=False,
                        branch=branch_name,
                        commit_sha=None,
                        conflicts=[],
                        error=f"Branch {branch_name} not found"
                    )

            # Prepare merge message
            if message is None:
                message = f"Merge {branch_name} into {self.base_branch}"

            # Attempt merge
            merge_args = ['--no-ff'] if no_ff else []
            merge_args.extend(['-m', message, branch_name])

            self.repo.git.merge(*merge_args)

            # Get merge commit
            merge_commit = self.repo.head.commit

            return MergeResult(
                success=True,
                branch=branch_name,
                commit_sha=merge_commit.hexsha[:8],
                conflicts=[],
                error=None
            )

        except GitCommandError as e:
            # Merge failed - likely conflicts
            conflict_files = self._get_conflicted_files()

            # Abort merge
            try:
                self.repo.git.merge('--abort')
            except:
                pass

            return MergeResult(
                success=False,
                branch=branch_name,
                commit_sha=None,
                conflicts=conflict_files,
                error=str(e)
            )

    def _get_conflicted_files(self) -> List[str]:
        """Get list of files with merge conflicts"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', '--diff-filter=U'],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return [f.strip() for f in result.stdout.split('\n') if f.strip()]
        except:
            return []

    def rollback_merge(self) -> bool:
        """
        Rollback the last merge commit
        Returns True if successful
        """
        try:
            # Reset to previous commit
            self.repo.git.reset('--hard', 'HEAD~1')
            print(f"✅ Successfully rolled back last merge")
            return True
        except GitCommandError as e:
            print(f"❌ Failed to rollback: {e}")
            return False

    def push_branch(self, branch_name: str, retry_count: int = 4) -> bool:
        """
        Push branch to remote with exponential backoff retry
        Returns True if successful
        """
        backoff_delays = [2, 4, 8, 16]

        for attempt in range(retry_count):
            try:
                self.repo.git.push('-u', 'origin', branch_name)
                print(f"✅ Successfully pushed {branch_name}")
                return True
            except GitCommandError as e:
                if '403' in str(e) or 'forbidden' in str(e).lower():
                    print(f"❌ Push forbidden (403). Check branch name starts with 'claude/' and has correct session ID")
                    return False

                if attempt < retry_count - 1:
                    delay = backoff_delays[attempt]
                    print(f"⚠️  Push failed (attempt {attempt + 1}/{retry_count}), retrying in {delay}s...")
                    import time
                    time.sleep(delay)
                else:
                    print(f"❌ Failed to push after {retry_count} attempts: {e}")
                    return False
        return False

    def get_last_commit(self, branch_name: str = None) -> Optional[Dict]:
        """Get information about the last commit"""
        try:
            if branch_name:
                commit = self.repo.branches[branch_name].commit
            else:
                commit = self.repo.head.commit

            return {
                'sha': commit.hexsha[:8],
                'message': commit.message.strip(),
                'author': str(commit.author),
                'date': datetime.fromtimestamp(commit.committed_date)
            }
        except:
            return None

    def get_diff_summary(self, branch_name: str) -> Dict:
        """
        Get summary of changes in a branch compared to base
        """
        try:
            # Get diff stats
            diff = self.repo.git.diff(f'{self.base_branch}...{branch_name}', '--stat')

            # Get list of changed files
            changed_files = self.repo.git.diff(
                f'{self.base_branch}...{branch_name}',
                '--name-only'
            ).split('\n')

            return {
                'diff_stat': diff,
                'files_changed': [f for f in changed_files if f.strip()],
                'num_files': len([f for f in changed_files if f.strip()])
            }
        except Exception as e:
            return {
                'diff_stat': '',
                'files_changed': [],
                'num_files': 0,
                'error': str(e)
            }

    def create_branch(self, branch_name: str, from_branch: str = None) -> bool:
        """
        Create a new branch
        """
        try:
            if from_branch:
                base = self.repo.heads[from_branch]
            else:
                base = self.repo.head

            self.repo.create_head(branch_name, base)
            print(f"✅ Created branch {branch_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to create branch {branch_name}: {e}")
            return False

    def checkout_branch(self, branch_name: str) -> bool:
        """
        Checkout a branch
        """
        try:
            self.repo.heads[branch_name].checkout()
            print(f"✅ Checked out {branch_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to checkout {branch_name}: {e}")
            return False
