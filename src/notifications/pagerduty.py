"""PagerDuty notification channel."""

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


class PagerDutyNotifier(NotificationChannel):
    """Send notifications to PagerDuty for incident management."""

    def __init__(
        self,
        integration_key: str,
        enabled: bool = True,
    ) -> None:
        """
        Initialize PagerDuty notifier.

        Args:
            integration_key: PagerDuty Events API v2 integration key
            enabled: Whether channel is enabled
        """
        super().__init__("pagerduty", enabled)
        self.integration_key = integration_key
        self.api_url = "https://events.pagerduty.com/v2/enqueue"

    async def send(self, alert: Alert) -> NotificationResult:
        """Send alert to PagerDuty."""
        if not self.should_send(alert):
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.THROTTLED,
                message="Alert not sent (channel disabled or filtered)",
            )

        try:
            payload = self._build_pagerduty_event(alert)

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    timeout=10.0,
                )

            data = response.json()

            if response.status_code == 202:  # PagerDuty returns 202 on success
                return NotificationResult(
                    success=True,
                    channel=self.name,
                    status=NotificationStatus.SENT,
                    message="Incident created in PagerDuty successfully",
                    sent_at=datetime.utcnow(),
                    metadata={
                        "dedup_key": data.get("dedup_key"),
                        "status": data.get("status"),
                    },
                )
            else:
                return NotificationResult(
                    success=False,
                    channel=self.name,
                    status=NotificationStatus.FAILED,
                    message=f"PagerDuty API returned {response.status_code}",
                    error=data.get("message", response.text),
                )

        except Exception as e:
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.FAILED,
                message=f"Failed to send to PagerDuty: {str(e)}",
                error=str(e),
            )

    def _build_pagerduty_event(self, alert: Alert) -> Dict[str, Any]:
        """Build PagerDuty event payload."""
        severity = self._map_priority_to_severity(alert.priority)

        # Use fingerprint for deduplication if available
        dedup_key = alert.fingerprint or alert.id

        payload = {
            "routing_key": self.integration_key,
            "event_action": "trigger",
            "dedup_key": dedup_key,
            "payload": {
                "summary": alert.title,
                "source": alert.source,
                "severity": severity,
                "timestamp": alert.timestamp.isoformat(),
                "custom_details": {
                    "message": alert.message,
                    "tags": alert.tags,
                    **alert.metadata,
                },
            },
        }

        # Add links if available
        if "url" in alert.metadata:
            payload["payload"]["custom_details"]["related_url"] = alert.metadata["url"]

        return payload

    async def resolve(self, dedup_key: str) -> NotificationResult:
        """
        Resolve a PagerDuty incident.

        Args:
            dedup_key: Deduplication key of the incident to resolve

        Returns:
            NotificationResult with resolution status
        """
        payload = {
            "routing_key": self.integration_key,
            "event_action": "resolve",
            "dedup_key": dedup_key,
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    timeout=10.0,
                )

            if response.status_code == 202:
                return NotificationResult(
                    success=True,
                    channel=self.name,
                    status=NotificationStatus.SENT,
                    message="Incident resolved in PagerDuty",
                    sent_at=datetime.utcnow(),
                )
            else:
                return NotificationResult(
                    success=False,
                    channel=self.name,
                    status=NotificationStatus.FAILED,
                    message=f"Failed to resolve incident: {response.status_code}",
                    error=response.text,
                )

        except Exception as e:
            return NotificationResult(
                success=False,
                channel=self.name,
                status=NotificationStatus.FAILED,
                message=f"Error resolving incident: {str(e)}",
                error=str(e),
            )

    def _map_priority_to_severity(self, priority: NotificationPriority) -> str:
        """Map alert priority to PagerDuty severity."""
        mapping = {
            NotificationPriority.LOW: "info",
            NotificationPriority.MEDIUM: "warning",
            NotificationPriority.HIGH: "error",
            NotificationPriority.CRITICAL: "critical",
        }
        return mapping.get(priority, "info")

    def test_connection(self) -> bool:
        """Test PagerDuty connection."""
        try:
            import asyncio
            test_alert = Alert(
                id="test",
                title="Test Alert - Please Ignore",
                message="This is a test notification from Plant AI",
                priority=NotificationPriority.LOW,
                source="test",
            )
            result = asyncio.run(self.send(test_alert))

            # Immediately resolve it
            if result.success and result.metadata.get("dedup_key"):
                asyncio.run(self.resolve(result.metadata["dedup_key"]))

            return result.success
        except Exception:
            return False

    def should_send(self, alert: Alert) -> bool:
        """Only send high and critical alerts to PagerDuty."""
        if not super().should_send(alert):
            return False

        # PagerDuty is typically for high-priority incidents only
        return alert.priority in (NotificationPriority.HIGH, NotificationPriority.CRITICAL)
