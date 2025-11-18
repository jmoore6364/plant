"""Slack notification channel."""

from typing import Optional, Dict, Any
import httpx
from datetime import datetime

from src.notifications.base import (
    NotificationChannel,
    Alert,
    NotificationResult,
    NotificationStatus,
    NotificationPriority,
)


class SlackNotifier(NotificationChannel):
    """Send notifications to Slack via webhooks or API."""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        api_token: Optional[str] = None,
        channel: Optional[str] = None,
        username: str = "Plant AI Monitor",
        icon_emoji: str = ":robot_face:",
        enabled: bool = True,
    ) -> None:
        """
        Initialize Slack notifier.

        Args:
            webhook_url: Slack webhook URL (for simple notifications)
            api_token: Slack API token (for advanced features)
            channel: Default channel to post to (if using API token)
            username: Bot username
            icon_emoji: Bot emoji icon
            enabled: Whether channel is enabled
        """
        super().__init__("slack", enabled)
        self.webhook_url = webhook_url
        self.api_token = api_token
        self.channel = channel
        self.username = username
        self.icon_emoji = icon_emoji

        if not webhook_url and not api_token:
            raise ValueError("Either webhook_url or api_token must be provided")

    async def send(self, alert: Alert) -> NotificationResult:
        """Send alert to Slack."""
        if not self.should_send(alert):
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.THROTTLED,
                message="Alert not sent (channel disabled or filtered)",
            )

        try:
            if self.webhook_url:
                result = await self._send_via_webhook(alert)
            else:
                result = await self._send_via_api(alert)

            return result

        except Exception as e:
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.FAILED,
                message=f"Failed to send to Slack: {str(e)}",
                error=str(e),
            )

    async def _send_via_webhook(self, alert: Alert) -> NotificationResult:
        """Send notification via webhook."""
        payload = self._build_slack_message(alert)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.webhook_url,
                json=payload,
                timeout=10.0,
            )

        if response.status_code == 200:
            return NotificationResult(
                success=True,
                channel=self.name,
                status=NotificationStatus.SENT,
                message="Alert sent to Slack successfully",
                sent_at=datetime.utcnow(),
            )
        else:
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.FAILED,
                message=f"Slack webhook returned {response.status_code}",
                error=response.text,
            )

    async def _send_via_api(self, alert: Alert) -> NotificationResult:
        """Send notification via Slack API."""
        payload = self._build_slack_message(alert)
        payload["channel"] = self.channel

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={"Authorization": f"Bearer {self.api_token}"},
                json=payload,
                timeout=10.0,
            )

        data = response.json()

        if data.get("ok"):
            return NotificationResult(
                success=True,
                channel=self.name,
                status=NotificationStatus.SENT,
                message="Alert sent to Slack successfully",
                sent_at=datetime.utcnow(),
                metadata={"ts": data.get("ts"), "channel": data.get("channel")},
            )
        else:
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.FAILED,
                message=f"Slack API error: {data.get('error')}",
                error=data.get("error"),
            )

    def _build_slack_message(self, alert: Alert) -> Dict[str, Any]:
        """Build Slack message payload."""
        color = self._get_color(alert.priority)

        # Build attachment
        attachment = {
            "color": color,
            "title": alert.title,
            "text": alert.message,
            "fields": [
                {
                    "title": "Priority",
                    "value": alert.priority.value.upper(),
                    "short": True,
                },
                {
                    "title": "Source",
                    "value": alert.source,
                    "short": True,
                },
                {
                    "title": "Time",
                    "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "short": True,
                },
            ],
            "footer": "Plant AI System Analyzer",
            "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
            "ts": int(alert.timestamp.timestamp()),
        }

        # Add tags if present
        if alert.tags:
            attachment["fields"].append({
                "title": "Tags",
                "value": ", ".join(alert.tags),
                "short": False,
            })

        # Add metadata fields
        for key, value in alert.metadata.items():
            attachment["fields"].append({
                "title": key.replace("_", " ").title(),
                "value": str(value),
                "short": True,
            })

        payload = {
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [attachment],
        }

        return payload

    def _get_color(self, priority: NotificationPriority) -> str:
        """Get Slack color for priority level."""
        colors = {
            NotificationPriority.LOW: "#36a64f",      # Green
            NotificationPriority.MEDIUM: "#ff9900",   # Orange
            NotificationPriority.HIGH: "#ff0000",     # Red
            NotificationPriority.CRITICAL: "#8b0000", # Dark Red
        }
        return colors.get(priority, "#808080")

    def test_connection(self) -> bool:
        """Test Slack connection."""
        try:
            import asyncio
            test_alert = Alert(
                id="test",
                title="Test Alert",
                message="This is a test notification from Plant AI",
                priority=NotificationPriority.LOW,
                source="test",
            )
            result = asyncio.run(self.send(test_alert))
            return result.success
        except Exception:
            return False
