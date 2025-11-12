#!/usr/bin/env python3
"""
Notification System
Sends notifications to Slack, Discord, or other webhook endpoints
"""

import os
import time
from typing import Optional, Dict
from enum import Enum
import requests


class UrgencyLevel(Enum):
    """Notification urgency levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Notifier:
    """Handles notifications to various platforms"""

    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_WEBHOOK")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK")
        self.enabled = bool(self.slack_webhook or self.discord_webhook)

        if not self.enabled:
            print("⚠️  No webhook URLs configured. Notifications disabled.")
            print("   Set SLACK_WEBHOOK or DISCORD_WEBHOOK environment variables to enable.")

    def notify(self, message: str, urgency: UrgencyLevel = UrgencyLevel.INFO,
               title: Optional[str] = None, fields: Optional[Dict] = None) -> bool:
        """
        Send notification to configured channels

        Args:
            message: Main notification message
            urgency: Urgency level (info, warning, critical)
            title: Optional title for the notification
            fields: Optional dict of additional fields

        Returns:
            True if at least one notification succeeded
        """
        if not self.enabled:
            # Just log to console
            self._log_to_console(message, urgency, title)
            return True

        success = False

        # Send to Slack
        if self.slack_webhook:
            success = self._send_slack(message, urgency, title, fields) or success

        # Send to Discord
        if self.discord_webhook:
            success = self._send_discord(message, urgency, title, fields) or success

        # Also log to console
        self._log_to_console(message, urgency, title)

        return success

    def _log_to_console(self, message: str, urgency: UrgencyLevel, title: Optional[str] = None):
        """Log notification to console"""
        emoji = {
            UrgencyLevel.INFO: "ℹ️",
            UrgencyLevel.WARNING: "⚠️",
            UrgencyLevel.CRITICAL: "🔥"
        }

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        prefix = f"[{timestamp}] {emoji[urgency]} [{urgency.value.upper()}]"

        if title:
            print(f"{prefix} {title}")
            print(f"  {message}")
        else:
            print(f"{prefix} {message}")

    def _send_slack(self, message: str, urgency: UrgencyLevel,
                    title: Optional[str] = None, fields: Optional[Dict] = None) -> bool:
        """Send notification to Slack"""
        try:
            color = {
                UrgencyLevel.INFO: "#36a64f",
                UrgencyLevel.WARNING: "#ff9900",
                UrgencyLevel.CRITICAL: "#ff0000"
            }

            attachment = {
                "color": color[urgency],
                "title": title or f"[{urgency.value.upper()}] Supervisor Update",
                "text": message,
                "footer": "DGX Spark Integration Supervisor",
                "ts": int(time.time())
            }

            # Add fields if provided
            if fields:
                attachment["fields"] = [
                    {"title": k, "value": str(v), "short": True}
                    for k, v in fields.items()
                ]

            payload = {"attachments": [attachment]}

            response = requests.post(
                self.slack_webhook,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                return True
            else:
                print(f"⚠️  Slack notification failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Failed to send Slack notification: {e}")
            return False

    def _send_discord(self, message: str, urgency: UrgencyLevel,
                     title: Optional[str] = None, fields: Optional[Dict] = None) -> bool:
        """Send notification to Discord"""
        try:
            color = {
                UrgencyLevel.INFO: 0x36a64f,
                UrgencyLevel.WARNING: 0xff9900,
                UrgencyLevel.CRITICAL: 0xff0000
            }

            embed = {
                "title": title or f"[{urgency.value.upper()}] Supervisor Update",
                "description": message,
                "color": color[urgency],
                "footer": {"text": "DGX Spark Integration Supervisor"},
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
            }

            # Add fields if provided
            if fields:
                embed["fields"] = [
                    {"name": k, "value": str(v), "inline": True}
                    for k, v in fields.items()
                ]

            payload = {"embeds": [embed]}

            response = requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10
            )

            if response.status_code in [200, 204]:
                return True
            else:
                print(f"⚠️  Discord notification failed: {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Failed to send Discord notification: {e}")
            return False

    # Convenience methods for common notifications
    def merge_success(self, branch: str, commit_sha: str):
        """Notify about successful merge"""
        self.notify(
            f"Successfully merged `{branch}` to main. All tests passed.",
            UrgencyLevel.INFO,
            title="✅ Merge Successful",
            fields={"Branch": branch, "Commit": commit_sha}
        )

    def merge_conflict(self, branch: str, files: list):
        """Notify about merge conflict"""
        files_str = "\n".join([f"• {f}" for f in files[:5]])
        if len(files) > 5:
            files_str += f"\n• ... and {len(files) - 5} more"

        self.notify(
            f"Merge conflicts detected in `{branch}`:\n{files_str}",
            UrgencyLevel.WARNING,
            title="⚠️ Merge Conflicts Detected",
            fields={"Branch": branch, "Files": len(files)}
        )

    def test_failure(self, branch: str, failed_tests: list):
        """Notify about test failures"""
        tests_str = "\n".join([f"• {t}" for t in failed_tests[:5]])
        if len(failed_tests) > 5:
            tests_str += f"\n• ... and {len(failed_tests) - 5} more"

        self.notify(
            f"Integration tests failed after merging `{branch}`:\n{tests_str}\n\nRolling back merge.",
            UrgencyLevel.CRITICAL,
            title="🔥 Integration Tests Failed",
            fields={"Branch": branch, "Failed Tests": len(failed_tests)}
        )

    def blocker_detected(self, agent: str, blocker_type: str, details: str):
        """Notify about blocker"""
        self.notify(
            f"Agent `{agent}` is blocked:\n{details}",
            UrgencyLevel.WARNING,
            title=f"🚧 Blocker: {blocker_type}",
            fields={"Agent": agent, "Type": blocker_type}
        )

    def service_down(self, service: str, status: str):
        """Notify about service failure"""
        self.notify(
            f"Service `{service}` is {status}. Attempting restart...",
            UrgencyLevel.CRITICAL,
            title="🔥 Service Down",
            fields={"Service": service, "Status": status}
        )

    def quality_gate_failed(self, branch: str, failed_checks: list):
        """Notify about quality gate failures"""
        checks_str = "\n".join([f"• {c}" for c in failed_checks])

        self.notify(
            f"Quality gates failed for `{branch}`:\n{checks_str}",
            UrgencyLevel.WARNING,
            title="⚠️ Quality Gates Failed",
            fields={"Branch": branch, "Failed Checks": len(failed_checks)}
        )

    def integration_complete(self, merged_count: int, total_agents: int):
        """Notify about integration milestone"""
        self.notify(
            f"Integration progress: {merged_count}/{total_agents} agents merged to main.",
            UrgencyLevel.INFO,
            title="📊 Integration Progress",
            fields={
                "Merged": f"{merged_count}/{total_agents}",
                "Remaining": total_agents - merged_count
            }
        )


# Global notifier instance
_notifier = None


def get_notifier() -> Notifier:
    """Get or create global notifier instance"""
    global _notifier
    if _notifier is None:
        _notifier = Notifier()
    return _notifier
