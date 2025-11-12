#!/usr/bin/env python3
"""
Health Monitor
Continuous monitoring daemon for services, GPU, disk space, etc.
"""

import sys
import os
import time
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import subprocess

# Add supervisor to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.notifier import get_notifier, UrgencyLevel

try:
    import docker
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    print("⚠️  Docker SDK not available - container monitoring disabled")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("⚠️  psutil not available - system monitoring limited")


class HealthMonitor:
    """Monitors system and service health"""

    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.notifier = get_notifier()
        self.alert_cooldown = {}  # Prevent alert spam
        self.cooldown_period = 300  # 5 minutes

        if DOCKER_AVAILABLE:
            try:
                self.docker_client = docker.from_env()
            except Exception as e:
                print(f"⚠️  Failed to connect to Docker: {e}")
                self.docker_client = None
        else:
            self.docker_client = None

    def run(self):
        """Main monitoring loop"""
        print("=" * 80)
        print("🔍 SUPERVISOR HEALTH MONITOR")
        print("=" * 80)
        print(f"Check interval: {self.check_interval}s")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        iteration = 0

        try:
            while True:
                iteration += 1
                print(f"\n[Check #{iteration}] {datetime.now().strftime('%H:%M:%S')}")

                # Run all checks
                self.check_docker_services()
                self.check_gpu_status()
                self.check_disk_space()
                self.check_zombie_containers()

                # Wait for next check
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            print("\n\n⏹️  Health monitor stopped by user")

    def check_docker_services(self):
        """Check status of Docker services"""
        if not self.docker_client:
            return

        try:
            # Get all containers from docker-compose project
            containers = self.docker_client.containers.list(
                all=True,
                filters={'label': 'com.docker.compose.project'}
            )

            if not containers:
                # No compose services found
                return

            print(f"\n🐳 Docker Services ({len(containers)} containers):")

            issues = []

            for container in containers:
                service_name = container.labels.get('com.docker.compose.service', container.name)
                status = container.status

                if status == 'running':
                    # Check if container is healthy
                    health = container.attrs.get('State', {}).get('Health', {})
                    health_status = health.get('Status', 'unknown')

                    if health_status == 'unhealthy':
                        print(f"   ⚠️  {service_name}: running but unhealthy")
                        issues.append(f"{service_name} (unhealthy)")
                    else:
                        print(f"   ✅ {service_name}: running")
                else:
                    print(f"   ❌ {service_name}: {status}")
                    issues.append(f"{service_name} ({status})")

                    # Try to restart if not running
                    if status in ['exited', 'dead']:
                        self._try_restart_container(container, service_name)

            # Alert if issues found (with cooldown)
            if issues:
                self._alert_if_not_on_cooldown(
                    'docker_services',
                    f"Docker service issues: {', '.join(issues)}",
                    UrgencyLevel.CRITICAL
                )

        except Exception as e:
            print(f"   ⚠️  Error checking Docker services: {e}")

    def check_gpu_status(self):
        """Check GPU memory and utilization"""
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=memory.used,memory.total,utilization.gpu',
                 '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return

            # Parse GPU stats
            line = result.stdout.strip()
            if not line:
                return

            parts = line.split(',')
            if len(parts) >= 3:
                mem_used = float(parts[0].strip())
                mem_total = float(parts[1].strip())
                gpu_util = float(parts[2].strip())

                mem_percent = (mem_used / mem_total) * 100

                print(f"\n🎮 GPU Status:")
                print(f"   Memory: {mem_used:.0f}MB / {mem_total:.0f}MB ({mem_percent:.1f}%)")
                print(f"   Utilization: {gpu_util:.1f}%")

                # Alert if memory usage very high
                if mem_percent > 95:
                    self._alert_if_not_on_cooldown(
                        'gpu_memory',
                        f"GPU memory at {mem_percent:.1f}% - potential OOM risk",
                        UrgencyLevel.WARNING
                    )

        except FileNotFoundError:
            # nvidia-smi not available
            pass
        except Exception as e:
            print(f"   ⚠️  Error checking GPU: {e}")

    def check_disk_space(self):
        """Check disk space usage"""
        if not PSUTIL_AVAILABLE:
            return

        try:
            disk = psutil.disk_usage('/')

            print(f"\n💾 Disk Space:")
            print(f"   Used: {disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB ({disk.percent}%)")

            if disk.percent > 90:
                self._alert_if_not_on_cooldown(
                    'disk_space',
                    f"Disk usage at {disk.percent}% - running low on space",
                    UrgencyLevel.WARNING
                )
            elif disk.percent > 95:
                self._alert_if_not_on_cooldown(
                    'disk_space_critical',
                    f"Disk usage at {disk.percent}% - CRITICAL",
                    UrgencyLevel.CRITICAL
                )

        except Exception as e:
            print(f"   ⚠️  Error checking disk space: {e}")

    def check_zombie_containers(self):
        """Check for zombie/dangling containers"""
        if not self.docker_client:
            return

        try:
            # Get containers that are in bad states
            containers = self.docker_client.containers.list(
                all=True,
                filters={'status': 'exited'}
            )

            # Filter to old containers (more than 1 hour old)
            import datetime as dt
            zombies = []

            for container in containers:
                finished_at = container.attrs.get('State', {}).get('FinishedAt', '')
                if finished_at and finished_at != '0001-01-01T00:00:00Z':
                    try:
                        finished_time = dt.datetime.fromisoformat(finished_at.replace('Z', '+00:00'))
                        age = dt.datetime.now(dt.timezone.utc) - finished_time

                        if age.total_seconds() > 3600:  # 1 hour
                            zombies.append(container)
                    except:
                        pass

            if zombies:
                print(f"\n🧟 Zombie Containers: {len(zombies)}")

                # Clean up zombies
                for container in zombies[:5]:  # Limit to 5 at a time
                    try:
                        print(f"   🧹 Removing {container.name}...")
                        container.remove()
                    except Exception as e:
                        print(f"   ⚠️  Failed to remove {container.name}: {e}")

                if len(zombies) > 5:
                    print(f"   ... and {len(zombies) - 5} more")

        except Exception as e:
            print(f"   ⚠️  Error checking zombie containers: {e}")

    def _try_restart_container(self, container, service_name: str):
        """Try to restart a stopped container"""
        try:
            print(f"   🔄 Attempting to restart {service_name}...")
            container.restart()

            # Wait a bit and check if it's running
            time.sleep(5)
            container.reload()

            if container.status == 'running':
                print(f"   ✅ Successfully restarted {service_name}")
                self.notifier.notify(
                    f"Successfully restarted service: {service_name}",
                    UrgencyLevel.INFO
                )
            else:
                print(f"   ❌ Restart failed - still {container.status}")
                self.notifier.service_down(service_name, container.status)

        except Exception as e:
            print(f"   ❌ Failed to restart {service_name}: {e}")
            self.notifier.service_down(service_name, f"restart failed: {e}")

    def _alert_if_not_on_cooldown(self, alert_key: str, message: str, urgency: UrgencyLevel):
        """Send alert if not on cooldown"""
        now = time.time()
        last_alert = self.alert_cooldown.get(alert_key, 0)

        if now - last_alert > self.cooldown_period:
            self.notifier.notify(message, urgency)
            self.alert_cooldown[alert_key] = now


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Health monitoring daemon')
    parser.add_argument(
        '--interval',
        type=int,
        default=60,
        help='Check interval in seconds (default: 60)'
    )

    args = parser.parse_args()

    monitor = HealthMonitor(check_interval=args.interval)
    monitor.run()


if __name__ == "__main__":
    main()
