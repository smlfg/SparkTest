#!/usr/bin/env python3
"""
Student User Management Tool
Python interface for managing student accounts on Spark cluster
"""

import argparse
import json
import os
import pwd
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class StudentManager:
    """Manage student user accounts"""

    def __init__(self, workspace_base: str = "/workspace"):
        self.workspace_base = Path(workspace_base)
        self.is_root = os.geteuid() == 0

    def list_students(self, output_format: str = "table") -> List[Dict]:
        """
        List all student users

        Args:
            output_format: Output format (table, json, csv)

        Returns:
            List of student user information
        """
        students = []

        if not self.workspace_base.exists():
            return students

        for workspace in self.workspace_base.iterdir():
            if workspace.is_dir():
                username = workspace.name

                try:
                    user_info = pwd.getpwnam(username)

                    student = {
                        "username": username,
                        "uid": user_info.pw_uid,
                        "gid": user_info.pw_gid,
                        "home": user_info.pw_dir,
                        "shell": user_info.pw_shell,
                        "workspace": str(workspace),
                        "quota_used": self._get_quota_usage(username),
                        "quota_limit": self._get_quota_limit(username),
                        "groups": self._get_user_groups(username),
                        "workspace_size": self._get_directory_size(workspace),
                    }

                    students.append(student)
                except KeyError:
                    # User doesn't exist in system
                    continue

        if output_format == "json":
            print(json.dumps(students, indent=2))
        elif output_format == "csv":
            self._print_csv(students)
        else:
            self._print_table(students)

        return students

    def get_student_info(self, username: str) -> Optional[Dict]:
        """Get detailed information about a student"""
        try:
            user_info = pwd.getpwnam(username)
        except KeyError:
            print(f"Error: User {username} does not exist")
            return None

        workspace = self.workspace_base / username

        info = {
            "username": username,
            "uid": user_info.pw_uid,
            "gid": user_info.pw_gid,
            "home": user_info.pw_dir,
            "shell": user_info.pw_shell,
            "workspace": str(workspace),
            "groups": self._get_user_groups(username),
            "quota": self._get_quota_info(username),
            "workspace_structure": self._get_workspace_structure(workspace),
            "processes": self._get_user_processes(username),
            "last_login": self._get_last_login(username),
        }

        return info

    def create_students(self, config_file: str) -> bool:
        """Create students from configuration file"""
        if not self.is_root:
            print("Error: Must run as root to create users")
            return False

        script_path = Path(__file__).parent.parent / "scripts" / "create_student_users.sh"

        if not script_path.exists():
            print(f"Error: Creation script not found: {script_path}")
            return False

        cmd = ["bash", str(script_path), "--config", config_file]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")
            return False

    def remove_student(self, username: str, archive: bool = True) -> bool:
        """Remove a student user"""
        if not self.is_root:
            print("Error: Must run as root to remove users")
            return False

        script_path = Path(__file__).parent.parent / "scripts" / "remove_student_users.sh"

        if not script_path.exists():
            print(f"Error: Removal script not found: {script_path}")
            return False

        env = os.environ.copy()
        env["ARCHIVE_DATA"] = "true" if archive else "false"
        env["FORCE"] = "true"

        cmd = ["bash", str(script_path), username]

        try:
            result = subprocess.run(cmd, env=env, check=True, capture_output=True, text=True)
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error: {e.stderr}")
            return False

    def update_quota(self, username: str, soft_limit: str, hard_limit: str) -> bool:
        """Update user quota"""
        if not self.is_root:
            print("Error: Must run as root to update quotas")
            return False

        try:
            # Convert to MB
            soft_mb = self._parse_size(soft_limit) // (1024 * 1024)
            hard_mb = self._parse_size(hard_limit) // (1024 * 1024)

            cmd = [
                "setquota", "-u", username,
                str(soft_mb), str(hard_mb), "0", "0",
                str(self.workspace_base)
            ]

            subprocess.run(cmd, check=True)
            print(f"✅ Quota updated for {username}: {soft_limit} (soft) / {hard_limit} (hard)")
            return True
        except Exception as e:
            print(f"Error updating quota: {e}")
            return False

    def lock_user(self, username: str) -> bool:
        """Lock user account"""
        if not self.is_root:
            print("Error: Must run as root to lock users")
            return False

        try:
            subprocess.run(["passwd", "-l", username], check=True)
            print(f"✅ User {username} locked")
            return True
        except subprocess.CalledProcessError:
            print(f"Error: Failed to lock user {username}")
            return False

    def unlock_user(self, username: str) -> bool:
        """Unlock user account"""
        if not self.is_root:
            print("Error: Must run as root to unlock users")
            return False

        try:
            subprocess.run(["passwd", "-u", username], check=True)
            print(f"✅ User {username} unlocked")
            return True
        except subprocess.CalledProcessError:
            print(f"Error: Failed to unlock user {username}")
            return False

    def generate_report(self, output_file: str = None) -> Dict:
        """Generate comprehensive student user report"""
        students = self.list_students(output_format="json")

        report = {
            "generated": datetime.now().isoformat(),
            "hostname": subprocess.check_output(["hostname"]).decode().strip(),
            "workspace_base": str(self.workspace_base),
            "total_students": len(students),
            "students": students,
            "statistics": {
                "total_quota_used": sum(s.get("quota_used", 0) for s in students),
                "average_workspace_size": sum(s.get("workspace_size", 0) for s in students) / len(students) if students else 0,
            }
        }

        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to: {output_file}")

        return report

    # Helper methods
    def _get_quota_usage(self, username: str) -> int:
        """Get quota usage in bytes"""
        try:
            result = subprocess.run(
                ["quota", "-u", username],
                capture_output=True,
                text=True,
                timeout=5
            )
            # Parse quota output
            return 0  # Placeholder
        except:
            return 0

    def _get_quota_limit(self, username: str) -> int:
        """Get quota limit in bytes"""
        try:
            result = subprocess.run(
                ["quota", "-u", username],
                capture_output=True,
                text=True,
                timeout=5
            )
            return 0  # Placeholder
        except:
            return 0

    def _get_quota_info(self, username: str) -> Dict:
        """Get detailed quota information"""
        try:
            result = subprocess.run(
                ["quota", "-s", "-u", username],
                capture_output=True,
                text=True,
                timeout=5
            )
            return {"output": result.stdout}
        except:
            return {}

    def _get_user_groups(self, username: str) -> List[str]:
        """Get user's groups"""
        try:
            result = subprocess.run(
                ["id", "-nG", username],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip().split()
        except:
            return []

    def _get_directory_size(self, path: Path) -> int:
        """Get directory size in bytes"""
        try:
            result = subprocess.run(
                ["du", "-sb", str(path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            size = int(result.stdout.split()[0])
            return size
        except:
            return 0

    def _get_workspace_structure(self, workspace: Path) -> Dict:
        """Get workspace directory structure"""
        if not workspace.exists():
            return {}

        structure = {}
        for item in workspace.iterdir():
            if item.is_dir():
                structure[item.name] = {
                    "type": "directory",
                    "size": self._get_directory_size(item),
                    "file_count": len(list(item.rglob("*")))
                }

        return structure

    def _get_user_processes(self, username: str) -> List[Dict]:
        """Get user's running processes"""
        try:
            result = subprocess.run(
                ["ps", "-u", username, "-o", "pid,ppid,%cpu,%mem,cmd", "--no-headers"],
                capture_output=True,
                text=True,
                timeout=5
            )

            processes = []
            for line in result.stdout.strip().split('\n')[:10]:  # Limit to 10
                if line:
                    parts = line.split(None, 4)
                    if len(parts) >= 5:
                        processes.append({
                            "pid": int(parts[0]),
                            "ppid": int(parts[1]),
                            "cpu": float(parts[2]),
                            "mem": float(parts[3]),
                            "cmd": parts[4]
                        })

            return processes
        except:
            return []

    def _get_last_login(self, username: str) -> Optional[str]:
        """Get user's last login"""
        try:
            result = subprocess.run(
                ["last", "-n", "1", username],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip().split('\n')[0] if result.stdout else None
        except:
            return None

    def _parse_size(self, size_str: str) -> int:
        """Parse size string to bytes"""
        units = {'K': 1024, 'M': 1024**2, 'G': 1024**3, 'T': 1024**4}
        size_str = size_str.upper().strip()

        for unit, multiplier in units.items():
            if size_str.endswith(unit):
                return int(float(size_str[:-1]) * multiplier)

        return int(size_str)

    def _print_table(self, students: List[Dict]):
        """Print students in table format"""
        if not students:
            print("No student users found")
            return

        print(f"\n{'Username':<15} {'UID':<8} {'Workspace Size':<15} {'Groups':<20}")
        print("=" * 70)

        for student in students:
            size = student.get('workspace_size', 0)
            size_str = self._format_size(size)
            groups = ','.join(student.get('groups', [])[:3])  # First 3 groups

            print(f"{student['username']:<15} {student['uid']:<8} {size_str:<15} {groups:<20}")

        print(f"\nTotal students: {len(students)}\n")

    def _print_csv(self, students: List[Dict]):
        """Print students in CSV format"""
        if not students:
            return

        headers = ["username", "uid", "gid", "workspace", "workspace_size", "groups"]
        print(",".join(headers))

        for student in students:
            values = [
                student.get('username', ''),
                str(student.get('uid', '')),
                str(student.get('gid', '')),
                student.get('workspace', ''),
                str(student.get('workspace_size', 0)),
                '|'.join(student.get('groups', []))
            ]
            print(",".join(values))

    def _format_size(self, size: int) -> str:
        """Format size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}PB"


def main():
    parser = argparse.ArgumentParser(
        description="Student User Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all students
  %(prog)s list

  # Get student info
  %(prog)s info student01

  # Create students from config
  sudo %(prog)s create --config students.conf

  # Remove student (with archive)
  sudo %(prog)s remove student01

  # Update quota
  sudo %(prog)s quota student01 100G 110G

  # Lock/unlock user
  sudo %(prog)s lock student01
  sudo %(prog)s unlock student01

  # Generate report
  %(prog)s report --output report.json
        """
    )

    parser.add_argument("action", choices=[
        "list", "info", "create", "remove", "quota", "lock", "unlock", "report"
    ], help="Action to perform")
    parser.add_argument("args", nargs="*", help="Action arguments")
    parser.add_argument("--workspace", default="/workspace", help="Workspace base directory")
    parser.add_argument("--config", help="Configuration file")
    parser.add_argument("--output", help="Output file for reports")
    parser.add_argument("--format", choices=["table", "json", "csv"], default="table",
                        help="Output format")
    parser.add_argument("--no-archive", action="store_true", help="Don't archive data when removing")

    args = parser.parse_args()

    manager = StudentManager(args.workspace)

    if args.action == "list":
        manager.list_students(args.format)

    elif args.action == "info":
        if not args.args:
            print("Error: Username required")
            sys.exit(1)
        info = manager.get_student_info(args.args[0])
        if info:
            print(json.dumps(info, indent=2))

    elif args.action == "create":
        if not args.config:
            print("Error: --config required")
            sys.exit(1)
        success = manager.create_students(args.config)
        sys.exit(0 if success else 1)

    elif args.action == "remove":
        if not args.args:
            print("Error: Username required")
            sys.exit(1)
        success = manager.remove_student(args.args[0], not args.no_archive)
        sys.exit(0 if success else 1)

    elif args.action == "quota":
        if len(args.args) < 3:
            print("Error: Usage: quota <username> <soft> <hard>")
            sys.exit(1)
        success = manager.update_quota(args.args[0], args.args[1], args.args[2])
        sys.exit(0 if success else 1)

    elif args.action == "lock":
        if not args.args:
            print("Error: Username required")
            sys.exit(1)
        success = manager.lock_user(args.args[0])
        sys.exit(0 if success else 1)

    elif args.action == "unlock":
        if not args.args:
            print("Error: Username required")
            sys.exit(1)
        success = manager.unlock_user(args.args[0])
        sys.exit(0 if success else 1)

    elif args.action == "report":
        manager.generate_report(args.output)


if __name__ == "__main__":
    main()
