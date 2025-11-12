#!/usr/bin/env python3
"""
Supervisor Startup Script
Starts all supervisor components
"""

import sys
import subprocess
import time
from pathlib import Path
import argparse


def print_banner():
    """Print startup banner"""
    print("=" * 80)
    print("🤖 SUPERVISOR - Multi-Agent Integration System")
    print("=" * 80)
    print()


def check_dependencies():
    """Check if required dependencies are installed"""
    print("📦 Checking dependencies...")

    required = [
        'fastapi',
        'uvicorn',
        'gitpython',
        'requests',
        'pyyaml',
        'docker',
        'psutil'
    ]

    missing = []

    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (missing)")
            missing.append(package)

    if missing:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing)}")
        print(f"   Install with: pip install {' '.join(missing)}")
        return False

    print("   ✅ All dependencies installed")
    return True


def start_dashboard():
    """Start the web dashboard"""
    print("\n🌐 Starting dashboard...")
    print("   URL: http://localhost:9999")

    subprocess.Popen(
        ['python', 'dashboard.py'],
        cwd=Path(__file__).parent,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait a bit for dashboard to start
    time.sleep(2)

    print("   ✅ Dashboard started")


def start_health_monitor():
    """Start the health monitor"""
    print("\n🔍 Starting health monitor...")

    subprocess.Popen(
        ['python', 'health_monitor.py', '--interval', '60'],
        cwd=Path(__file__).parent,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    print("   ✅ Health monitor started")


def run_single_merge():
    """Run a single merge cycle"""
    print("\n🔀 Running merge cycle...")

    result = subprocess.run(
        ['python', 'auto_merge.py'],
        cwd=Path(__file__).parent
    )

    if result.returncode == 0:
        print("   ✅ Merge cycle completed")
    else:
        print("   ⚠️  Merge cycle completed with warnings")


def show_status():
    """Show quick status"""
    print("\n📊 Current Status:")

    try:
        from utils.gitops import GitOpsManager

        git = GitOpsManager()
        branches = git.get_agent_branches()

        print(f"   Agent branches: {len(branches)}")

        if branches:
            merged = 0
            for branch in branches:
                status = git.get_branch_status(branch)
                if status.exists and status.commits_ahead == 0:
                    merged += 1

            print(f"   Merged: {merged}/{len(branches)}")
            print(f"   Pending: {len(branches) - merged}")
        else:
            print("   No agent branches found yet")

    except Exception as e:
        print(f"   ⚠️  Could not fetch status: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Supervisor startup script')
    parser.add_argument('--dashboard-only', action='store_true',
                       help='Only start dashboard')
    parser.add_argument('--merge-only', action='store_true',
                       help='Only run merge cycle')
    parser.add_argument('--no-monitor', action='store_true',
                       help='Do not start health monitor')

    args = parser.parse_args()

    print_banner()

    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install missing dependencies first")
        return 1

    # Show current status
    show_status()

    if args.merge_only:
        # Just run merge cycle
        run_single_merge()
    elif args.dashboard_only:
        # Just start dashboard
        start_dashboard()
        print("\n✅ Dashboard running at http://localhost:9999")
        print("   Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️  Stopped")
    else:
        # Start everything
        start_dashboard()

        if not args.no_monitor:
            start_health_monitor()

        # Run initial merge
        run_single_merge()

        print("\n" + "=" * 80)
        print("✅ Supervisor Started Successfully")
        print("=" * 80)
        print()
        print("📍 Access Points:")
        print("   Dashboard:  http://localhost:9999")
        print("   API:        http://localhost:9999/api/status")
        print("   API Docs:   http://localhost:9999/docs")
        print()
        print("🔄 Automation:")
        print("   To enable periodic merging, add to crontab:")
        print("   */10 * * * * cd /home/user/SparkTest/supervisor && python auto_merge.py")
        print()
        print("⏹️  To stop: pkill -f 'python.*supervisor'")
        print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
