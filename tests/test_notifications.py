"""Tests for notification system."""

import pytest
from datetime import datetime
from src.notifications.base import (
    Alert,
    NotificationPriority,
    NotificationChannel,
    NotificationResult,
    NotificationStatus,
)
from src.notifications.rules import AlertRule, AlertRuleEngine
from src.notifications.manager import NotificationManager, AlertDeduplicator
from src.models.schemas import SystemMetrics, LogEntry, LogLevel


# Mock notification channel for testing
class MockNotificationChannel(NotificationChannel):
    """Mock channel for testing."""

    def __init__(self):
        super().__init__("mock", enabled=True)
        self.sent_alerts = []

    async def send(self, alert: Alert) -> NotificationResult:
        """Mock send implementation."""
        self.sent_alerts.append(alert)
        return NotificationResult(
            success=True,
            channel=self.name,
            status=NotificationStatus.SENT,
            message="Mock send successful",
            sent_at=datetime.utcnow(),
        )

    def test_connection(self) -> bool:
        """Mock test connection."""
        return True


def test_alert_creation():
    """Test creating an alert."""
    alert = Alert(
        id="test_alert",
        title="Test Alert",
        message="This is a test alert",
        priority=NotificationPriority.HIGH,
        source="test",
    )

    assert alert.id == "test_alert"
    assert alert.title == "Test Alert"
    assert alert.priority == NotificationPriority.HIGH


def test_alert_deduplication():
    """Test alert deduplication."""
    dedup = AlertDeduplicator(window_minutes=5)

    alert1 = Alert(
        id="alert1",
        title="High CPU",
        message="CPU at 90%",
        priority=NotificationPriority.HIGH,
        source="metrics",
        fingerprint="high_cpu",
    )

    alert2 = Alert(
        id="alert2",
        title="High CPU",
        message="CPU at 91%",
        priority=NotificationPriority.HIGH,
        source="metrics",
        fingerprint="high_cpu",
    )

    # First alert should not be duplicate
    assert not dedup.is_duplicate(alert1)

    # Second alert with same fingerprint should be duplicate
    assert dedup.is_duplicate(alert2)


def test_alert_rule_cpu():
    """Test CPU alert rule."""
    rule_engine = AlertRuleEngine()

    metrics = SystemMetrics(
        timestamp=datetime.utcnow(),
        cpu_percent=92.0,
        memory_percent=50.0,
        memory_available_mb=4000.0,
        disk_usage_percent=70.0,
        disk_free_gb=100.0,
        network_bytes_sent=1000000,
        network_bytes_recv=2000000,
        process_count=150,
    )

    alerts = rule_engine.evaluate_metrics(metrics)

    # Should trigger high_cpu_usage rule
    assert len(alerts) > 0
    assert any("cpu" in alert.title.lower() for alert in alerts)


def test_alert_rule_logs():
    """Test log-based alert rules."""
    rule_engine = AlertRuleEngine()

    logs = [
        LogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.ERROR,
            message="Error 1",
            source="app",
            raw_line="Error 1",
        ),
        LogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.ERROR,
            message="Error 2",
            source="app",
            raw_line="Error 2",
        ),
        LogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.ERROR,
            message="Error 3",
            source="app",
            raw_line="Error 3",
        ),
        LogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.ERROR,
            message="Error 4",
            source="app",
            raw_line="Error 4",
        ),
        LogEntry(
            timestamp=datetime.utcnow(),
            level=LogLevel.ERROR,
            message="Error 5",
            source="app",
            raw_line="Error 5",
        ),
    ]

    alerts = rule_engine.evaluate_logs(logs)

    # Should trigger error_logs rule (requires 5 errors)
    assert len(alerts) > 0


@pytest.mark.asyncio
async def test_notification_manager():
    """Test notification manager."""
    manager = NotificationManager()
    mock_channel = MockNotificationChannel()
    manager.add_channel(mock_channel)

    alert = Alert(
        id="test",
        title="Test Alert",
        message="Testing notification manager",
        priority=NotificationPriority.MEDIUM,
        source="test",
    )

    results = await manager.send_alert(alert)

    assert len(results) == 1
    assert results[0].success
    assert len(mock_channel.sent_alerts) == 1


@pytest.mark.asyncio
async def test_process_metrics():
    """Test processing metrics through notification manager."""
    manager = NotificationManager()
    mock_channel = MockNotificationChannel()
    manager.add_channel(mock_channel)

    metrics = SystemMetrics(
        timestamp=datetime.utcnow(),
        cpu_percent=96.0,  # Should trigger critical alert
        memory_percent=50.0,
        memory_available_mb=4000.0,
        disk_usage_percent=70.0,
        disk_free_gb=100.0,
        network_bytes_sent=1000000,
        network_bytes_recv=2000000,
        process_count=150,
    )

    results = await manager.process_metrics(metrics)

    # Should have sent alert for critical CPU
    assert len(mock_channel.sent_alerts) > 0
    sent_alert = mock_channel.sent_alerts[0]
    assert "cpu" in sent_alert.title.lower()


def test_alert_rule_engine():
    """Test alert rule engine."""
    engine = AlertRuleEngine()

    # Test adding custom rule
    custom_rule = AlertRule(
        name="test_rule",
        description="Test rule",
        metric_type="memory",
        threshold=80.0,
        comparison=">=",
        priority=NotificationPriority.HIGH,
    )

    engine.add_rule(custom_rule)
    assert "test_rule" in engine.rules

    # Test enabling/disabling rules
    engine.disable_rule("test_rule")
    assert not engine.rules["test_rule"].enabled

    engine.enable_rule("test_rule")
    assert engine.rules["test_rule"].enabled

    # Test removing rule
    engine.remove_rule("test_rule")
    assert "test_rule" not in engine.rules


def test_notification_channel_formatting():
    """Test channel formatting of alerts."""
    mock_channel = MockNotificationChannel()

    alert = Alert(
        id="test",
        title="Test Alert",
        message="Test message",
        priority=NotificationPriority.CRITICAL,
        source="test",
        tags=["urgent", "test"],
        metadata={"cpu": "95%", "memory": "80%"},
    )

    formatted = mock_channel.format_alert(alert)

    assert "Test Alert" in formatted
    assert "Test message" in formatted
    assert "CRITICAL" in formatted
    assert "urgent" in formatted


def test_notification_manager_channel_management():
    """Test channel management in notification manager."""
    manager = NotificationManager()
    mock_channel = MockNotificationChannel()

    # Add channel
    manager.add_channel(mock_channel)
    assert "mock" in manager.channels

    # Enable/disable channel
    manager.disable_channel("mock")
    assert not manager.channels["mock"].enabled

    manager.enable_channel("mock")
    assert manager.channels["mock"].enabled

    # Remove channel
    manager.remove_channel("mock")
    assert "mock" not in manager.channels


def test_alert_grouping():
    """Test alert grouping."""
    dedup = AlertDeduplicator()

    alert1 = Alert(
        id="1",
        title="CPU High",
        message="CPU at 90%",
        priority=NotificationPriority.HIGH,
        source="metrics",
        group_key="cpu_alerts",
    )

    alert2 = Alert(
        id="2",
        title="CPU High",
        message="CPU at 91%",
        priority=NotificationPriority.HIGH,
        source="metrics",
        group_key="cpu_alerts",
    )

    dedup.add_to_group(alert1)
    dedup.add_to_group(alert2)

    grouped = dedup.get_grouped_alerts("cpu_alerts")
    assert len(grouped) == 2
