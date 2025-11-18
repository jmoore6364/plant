"""Notification manager that coordinates all notification channels."""

from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib
import asyncio

from src.notifications.base import (
    Alert,
    NotificationChannel,
    NotificationResult,
    NotificationPriority,
)
from src.notifications.rules import AlertRuleEngine
from src.models.schemas import SystemMetrics, LogEntry, Anomaly


class AlertDeduplicator:
    """Handles alert deduplication and grouping."""

    def __init__(self, window_minutes: int = 15) -> None:
        """
        Initialize deduplicator.

        Args:
            window_minutes: Time window for deduplication
        """
        self.window_minutes = window_minutes
        self.seen_alerts: Dict[str, datetime] = {}
        self.grouped_alerts: Dict[str, List[Alert]] = defaultdict(list)

    def is_duplicate(self, alert: Alert) -> bool:
        """
        Check if alert is a duplicate within the time window.

        Args:
            alert: Alert to check

        Returns:
            True if duplicate
        """
        # Generate fingerprint if not provided
        fingerprint = alert.fingerprint or self._generate_fingerprint(alert)

        # Check if we've seen this alert recently
        if fingerprint in self.seen_alerts:
            last_seen = self.seen_alerts[fingerprint]
            time_diff = (datetime.utcnow() - last_seen).total_seconds()

            if time_diff < self.window_minutes * 60:
                return True

        # Not a duplicate, record it
        self.seen_alerts[fingerprint] = datetime.utcnow()
        return False

    def add_to_group(self, alert: Alert) -> None:
        """Add alert to its group."""
        group_key = alert.group_key or "default"
        self.grouped_alerts[group_key].append(alert)

    def get_grouped_alerts(self, group_key: str) -> List[Alert]:
        """Get all alerts in a group."""
        return self.grouped_alerts.get(group_key, [])

    def clear_old_alerts(self) -> None:
        """Clear alerts older than the window."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=self.window_minutes)

        # Clear old fingerprints
        self.seen_alerts = {
            fp: ts for fp, ts in self.seen_alerts.items()
            if ts > cutoff_time
        }

        # Clear old grouped alerts
        for group_key in list(self.grouped_alerts.keys()):
            self.grouped_alerts[group_key] = [
                alert for alert in self.grouped_alerts[group_key]
                if alert.timestamp > cutoff_time
            ]
            if not self.grouped_alerts[group_key]:
                del self.grouped_alerts[group_key]

    def _generate_fingerprint(self, alert: Alert) -> str:
        """Generate fingerprint for alert."""
        # Use title, source, and priority for fingerprint
        content = f"{alert.title}:{alert.source}:{alert.priority.value}"
        return hashlib.md5(content.encode()).hexdigest()


class NotificationManager:
    """Manages all notification channels and alert routing."""

    def __init__(self) -> None:
        """Initialize notification manager."""
        self.channels: Dict[str, NotificationChannel] = {}
        self.rule_engine = AlertRuleEngine()
        self.deduplicator = AlertDeduplicator()
        self.alert_history: List[Alert] = []
        self.notification_history: List[NotificationResult] = []

    def add_channel(self, channel: NotificationChannel) -> None:
        """
        Add a notification channel.

        Args:
            channel: Notification channel to add
        """
        self.channels[channel.name] = channel

    def remove_channel(self, channel_name: str) -> bool:
        """
        Remove a notification channel.

        Args:
            channel_name: Name of channel to remove

        Returns:
            True if removed
        """
        if channel_name in self.channels:
            del self.channels[channel_name]
            return True
        return False

    async def send_alert(
        self,
        alert: Alert,
        channels: Optional[List[str]] = None,
        skip_dedup: bool = False,
    ) -> List[NotificationResult]:
        """
        Send alert through specified channels.

        Args:
            alert: Alert to send
            channels: List of channel names (None = all enabled channels)
            skip_dedup: Skip deduplication check

        Returns:
            List of notification results
        """
        # Check for duplicates
        if not skip_dedup and self.deduplicator.is_duplicate(alert):
            return [
                NotificationResult(
                    success=False,
                    channel="deduplicator",
                    status="throttled",
                    message="Alert deduplicated (duplicate within time window)",
                )
            ]

        # Add to history
        self.alert_history.append(alert)
        self.deduplicator.add_to_group(alert)

        # Determine which channels to use
        target_channels = []
        if channels:
            target_channels = [
                self.channels[name] for name in channels
                if name in self.channels
            ]
        else:
            target_channels = [ch for ch in self.channels.values() if ch.enabled]

        # Send to all channels concurrently
        tasks = [channel.send(alert) for channel in target_channels]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle exceptions
        notification_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                notification_results.append(
                    NotificationResult(
                        success=False,
                        channel=target_channels[i].name,
                        status="failed",
                        message=f"Exception: {str(result)}",
                        error=str(result),
                    )
                )
            else:
                notification_results.append(result)

        # Store results
        self.notification_history.extend(notification_results)

        return notification_results

    async def process_metrics(
        self, metrics: SystemMetrics, channels: Optional[List[str]] = None
    ) -> List[NotificationResult]:
        """
        Process metrics and send alerts for any triggered rules.

        Args:
            metrics: System metrics to process
            channels: Target channels (None = all)

        Returns:
            List of notification results
        """
        # Evaluate rules
        alerts = self.rule_engine.evaluate_metrics(metrics)

        # Send all alerts
        all_results = []
        for alert in alerts:
            results = await self.send_alert(alert, channels)
            all_results.extend(results)

        return all_results

    async def process_logs(
        self, logs: List[LogEntry], channels: Optional[List[str]] = None
    ) -> List[NotificationResult]:
        """
        Process logs and send alerts for any triggered rules.

        Args:
            logs: Log entries to process
            channels: Target channels (None = all)

        Returns:
            List of notification results
        """
        # Evaluate rules
        alerts = self.rule_engine.evaluate_logs(logs)

        # Send all alerts
        all_results = []
        for alert in alerts:
            results = await self.send_alert(alert, channels)
            all_results.extend(results)

        return all_results

    async def process_anomaly(
        self, anomaly: Anomaly, channels: Optional[List[str]] = None
    ) -> List[NotificationResult]:
        """
        Process anomaly and send alert.

        Args:
            anomaly: Detected anomaly
            channels: Target channels (None = all)

        Returns:
            List of notification results
        """
        # Convert anomaly to alert
        alerts = self.rule_engine.evaluate_anomaly(anomaly)

        # Send all alerts
        all_results = []
        for alert in alerts:
            results = await self.send_alert(alert, channels)
            all_results.extend(results)

        return all_results

    def test_all_channels(self) -> Dict[str, bool]:
        """
        Test all configured channels.

        Returns:
            Dictionary mapping channel names to test results
        """
        results = {}
        for name, channel in self.channels.items():
            try:
                results[name] = channel.test_connection()
            except Exception:
                results[name] = False
        return results

    def get_channel_status(self) -> Dict[str, Dict]:
        """
        Get status of all channels.

        Returns:
            Dictionary with channel information
        """
        status = {}
        for name, channel in self.channels.items():
            status[name] = {
                "enabled": channel.enabled,
                "type": channel.name,
            }
        return status

    def get_alert_summary(self, hours: int = 24) -> Dict:
        """
        Get summary of recent alerts.

        Args:
            hours: Time window in hours

        Returns:
            Summary statistics
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_alerts = [
            alert for alert in self.alert_history
            if alert.timestamp > cutoff_time
        ]

        # Count by priority
        priority_counts = defaultdict(int)
        for alert in recent_alerts:
            priority_counts[alert.priority.value] += 1

        # Count by source
        source_counts = defaultdict(int)
        for alert in recent_alerts:
            source_counts[alert.source] += 1

        # Success rate
        total_notifications = len(self.notification_history)
        successful = sum(1 for r in self.notification_history if r.success)
        success_rate = (successful / total_notifications * 100) if total_notifications > 0 else 0

        return {
            "time_window_hours": hours,
            "total_alerts": len(recent_alerts),
            "by_priority": dict(priority_counts),
            "by_source": dict(source_counts),
            "notifications_sent": total_notifications,
            "success_rate": f"{success_rate:.1f}%",
        }

    def clear_history(self, keep_hours: int = 24) -> None:
        """
        Clear old alert and notification history.

        Args:
            keep_hours: Hours of history to keep
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=keep_hours)

        self.alert_history = [
            alert for alert in self.alert_history
            if alert.timestamp > cutoff_time
        ]

        self.deduplicator.clear_old_alerts()

    def enable_channel(self, channel_name: str) -> bool:
        """Enable a channel."""
        if channel_name in self.channels:
            self.channels[channel_name].enabled = True
            return True
        return False

    def disable_channel(self, channel_name: str) -> bool:
        """Disable a channel."""
        if channel_name in self.channels:
            self.channels[channel_name].enabled = False
            return True
        return False
