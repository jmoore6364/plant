"""Base classes for notification system."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationStatus(str, Enum):
    """Status of notification delivery."""

    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    THROTTLED = "throttled"


class Alert(BaseModel):
    """Alert to be sent via notifications."""

    id: str
    title: str
    message: str
    priority: NotificationPriority
    source: str  # e.g., "log_analyzer", "anomaly_detector"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)

    # Grouping and deduplication
    fingerprint: Optional[str] = None  # For deduplication
    group_key: Optional[str] = None    # For grouping similar alerts


class NotificationResult(BaseModel):
    """Result of sending a notification."""

    success: bool
    channel: str  # slack, discord, email, pagerduty
    status: NotificationStatus
    message: str
    sent_at: Optional[datetime] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NotificationChannel(ABC):
    """Base class for notification channels."""

    def __init__(self, name: str, enabled: bool = True) -> None:
        """
        Initialize notification channel.

        Args:
            name: Channel name (e.g., "slack", "discord")
            enabled: Whether channel is enabled
        """
        self.name = name
        self.enabled = enabled

    @abstractmethod
    async def send(self, alert: Alert) -> NotificationResult:
        """
        Send an alert through this channel.

        Args:
            alert: Alert to send

        Returns:
            NotificationResult with delivery status
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if the channel is properly configured.

        Returns:
            True if connection test successful
        """
        pass

    def format_alert(self, alert: Alert) -> str:
        """
        Format alert for this channel.

        Args:
            alert: Alert to format

        Returns:
            Formatted message string
        """
        priority_emoji = {
            NotificationPriority.LOW: "ℹ️",
            NotificationPriority.MEDIUM: "⚠️",
            NotificationPriority.HIGH: "🔥",
            NotificationPriority.CRITICAL: "🚨",
        }

        emoji = priority_emoji.get(alert.priority, "📢")

        formatted = f"{emoji} **{alert.title}** [{alert.priority.value.upper()}]\n\n"
        formatted += f"{alert.message}\n\n"
        formatted += f"**Source:** {alert.source}\n"
        formatted += f"**Time:** {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"

        if alert.tags:
            formatted += f"**Tags:** {', '.join(alert.tags)}\n"

        if alert.metadata:
            formatted += "\n**Details:**\n"
            for key, value in alert.metadata.items():
                formatted += f"- {key}: {value}\n"

        return formatted

    def should_send(self, alert: Alert) -> bool:
        """
        Check if alert should be sent through this channel.

        Args:
            alert: Alert to check

        Returns:
            True if alert should be sent
        """
        if not self.enabled:
            return False

        # Can be overridden by subclasses for channel-specific logic
        return True


class NotificationTemplate(BaseModel):
    """Template for formatting notifications."""

    name: str
    subject_template: str
    body_template: str
    format: str = "markdown"  # markdown, html, plain

    def render_subject(self, alert: Alert) -> str:
        """Render subject line."""
        return self.subject_template.format(
            title=alert.title,
            priority=alert.priority.value.upper(),
            source=alert.source,
            **alert.metadata
        )

    def render_body(self, alert: Alert) -> str:
        """Render message body."""
        return self.body_template.format(
            title=alert.title,
            message=alert.message,
            priority=alert.priority.value.upper(),
            source=alert.source,
            timestamp=alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
            tags=', '.join(alert.tags) if alert.tags else 'None',
            **alert.metadata
        )
