"""Discord notification channel."""

from typing import Optional, Dict, Any, List
import httpx
from datetime import datetime

from src.notifications.base import (
    NotificationChannel,
    Alert,
    NotificationResult,
    NotificationStatus,
    NotificationPriority,
)


class DiscordNotifier(NotificationChannel):
    """Send notifications to Discord via webhooks."""

    def __init__(
        self,
        webhook_url: str,
        username: str = "Plant AI Monitor",
        avatar_url: Optional[str] = None,
        enabled: bool = True,
    ) -> None:
        """
        Initialize Discord notifier.

        Args:
            webhook_url: Discord webhook URL
            username: Bot username
            avatar_url: Bot avatar URL
            enabled: Whether channel is enabled
        """
        super().__init__("discord", enabled)
        self.webhook_url = webhook_url
        self.username = username
        self.avatar_url = avatar_url

    async def send(self, alert: Alert) -> NotificationResult:
        """Send alert to Discord."""
        if not self.should_send(alert):
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.THROTTLED,
                message="Alert not sent (channel disabled or filtered)",
            )

        try:
            payload = self._build_discord_message(alert)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    timeout=10.0,
                )

            if response.status_code == 204:  # Discord returns 204 on success
                return NotificationResult(
                    success=True,
                    channel=self.name,
                    status=NotificationStatus.SENT,
                    message="Alert sent to Discord successfully",
                    sent_at=datetime.utcnow(),
                )
            else:
                return NotificationResult(
                    success=False,
                    channel=self.name,
                    status=NotificationStatus.FAILED,
                    message=f"Discord webhook returned {response.status_code}",
                    error=response.text,
                )

        except Exception as e:
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.FAILED,
                message=f"Failed to send to Discord: {str(e)}",
                error=str(e),
            )

    def _build_discord_message(self, alert: Alert) -> Dict[str, Any]:
        """Build Discord message payload with embeds."""
        color = self._get_color(alert.priority)

        # Build embed
        embed = {
            "title": alert.title,
            "description": alert.message,
            "color": color,
            "timestamp": alert.timestamp.isoformat(),
            "footer": {
                "text": "Plant AI System Analyzer",
            },
            "fields": [
                {
                    "name": "Priority",
                    "value": alert.priority.value.upper(),
                    "inline": True,
                },
                {
                    "name": "Source",
                    "value": alert.source,
                    "inline": True,
                },
            ],
        }

        # Add tags if present
        if alert.tags:
            embed["fields"].append({
                "name": "Tags",
                "value": ", ".join(alert.tags),
                "inline": False,
            })

        # Add metadata fields
        for key, value in alert.metadata.items():
            embed["fields"].append({
                "name": key.replace("_", " ").title(),
                "value": str(value)[:1024],  # Discord has field value limit
                "inline": True,
            })

        payload = {
            "username": self.username,
            "embeds": [embed],
        }

        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url

        return payload

    def _get_color(self, priority: NotificationPriority) -> int:
        """Get Discord color for priority level (as decimal)."""
        colors = {
            NotificationPriority.LOW: 3447003,      # Blue
            NotificationPriority.MEDIUM: 16776960,  # Yellow
            NotificationPriority.HIGH: 16711680,    # Red
            NotificationPriority.CRITICAL: 9109504, # Dark Red
        }
        return colors.get(priority, 8421504)  # Gray default

    def test_connection(self) -> bool:
        """Test Discord connection."""
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
