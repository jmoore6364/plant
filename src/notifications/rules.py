"""Alert rules and threshold management."""

from typing import List, Dict, Any, Optional, Callable
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from src.notifications.base import Alert, NotificationPriority
from src.models.schemas import SystemMetrics, LogEntry, LogLevel, Anomaly


class AlertRule(BaseModel):
    """Rule for triggering alerts based on conditions."""

    name: str
    description: str
    enabled: bool = True
    priority: NotificationPriority = NotificationPriority.MEDIUM

    # Conditions
    metric_type: Optional[str] = None  # cpu, memory, disk, etc.
    threshold: Optional[float] = None
    comparison: str = ">"  # >, <, >=, <=, ==, !=

    # Log-based conditions
    log_level: Optional[LogLevel] = None
    log_pattern: Optional[str] = None

    # Time-based
    time_window_minutes: int = 5
    occurrence_count: int = 1  # How many times condition must be met

    # Cooldown to prevent alert spam
    cooldown_minutes: int = 15
    last_triggered: Optional[datetime] = None

    # Tags to add to alerts
    tags: List[str] = Field(default_factory=list)

    # Custom metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AlertRuleEngine:
    """Engine for evaluating alert rules and generating alerts."""

    def __init__(self) -> None:
        """Initialize the rule engine."""
        self.rules: Dict[str, AlertRule] = {}
        self._load_default_rules()

    def _load_default_rules(self) -> None:
        """Load default alerting rules."""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                description="CPU usage above 90%",
                metric_type="cpu",
                threshold=90.0,
                comparison=">=",
                priority=NotificationPriority.HIGH,
                tags=["performance", "cpu"],
            ),
            AlertRule(
                name="critical_cpu_usage",
                description="CPU usage above 95%",
                metric_type="cpu",
                threshold=95.0,
                comparison=">=",
                priority=NotificationPriority.CRITICAL,
                tags=["performance", "cpu", "critical"],
                cooldown_minutes=5,
            ),
            AlertRule(
                name="high_memory_usage",
                description="Memory usage above 85%",
                metric_type="memory",
                threshold=85.0,
                comparison=">=",
                priority=NotificationPriority.HIGH,
                tags=["performance", "memory"],
            ),
            AlertRule(
                name="low_disk_space",
                description="Disk usage above 90%",
                metric_type="disk",
                threshold=90.0,
                comparison=">=",
                priority=NotificationPriority.HIGH,
                tags=["storage", "disk"],
            ),
            AlertRule(
                name="critical_disk_space",
                description="Disk usage above 95%",
                metric_type="disk",
                threshold=95.0,
                comparison=">=",
                priority=NotificationPriority.CRITICAL,
                tags=["storage", "disk", "critical"],
                cooldown_minutes=10,
            ),
            AlertRule(
                name="error_logs",
                description="Error level logs detected",
                log_level=LogLevel.ERROR,
                occurrence_count=5,
                time_window_minutes=5,
                priority=NotificationPriority.MEDIUM,
                tags=["logs", "errors"],
                cooldown_minutes=10,
            ),
            AlertRule(
                name="critical_logs",
                description="Critical level logs detected",
                log_level=LogLevel.CRITICAL,
                occurrence_count=1,
                priority=NotificationPriority.CRITICAL,
                tags=["logs", "critical"],
                cooldown_minutes=5,
            ),
        ]

        for rule in default_rules:
            self.rules[rule.name] = rule

    def add_rule(self, rule: AlertRule) -> None:
        """Add a new alert rule."""
        self.rules[rule.name] = rule

    def remove_rule(self, rule_name: str) -> bool:
        """Remove an alert rule."""
        if rule_name in self.rules:
            del self.rules[rule_name]
            return True
        return False

    def evaluate_metrics(self, metrics: SystemMetrics) -> List[Alert]:
        """
        Evaluate metrics against rules.

        Args:
            metrics: System metrics to evaluate

        Returns:
            List of triggered alerts
        """
        alerts = []

        for rule in self.rules.values():
            if not rule.enabled or not rule.metric_type:
                continue

            # Check cooldown
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    continue

            # Get metric value
            value = self._get_metric_value(metrics, rule.metric_type)
            if value is None:
                continue

            # Evaluate condition
            if self._evaluate_condition(value, rule.threshold, rule.comparison):
                alert = self._create_alert_from_rule(
                    rule,
                    f"{rule.description}: {value:.1f}%",
                    {"metric_type": rule.metric_type, "value": value, "threshold": rule.threshold},
                )
                alerts.append(alert)
                rule.last_triggered = datetime.utcnow()

        return alerts

    def evaluate_logs(self, logs: List[LogEntry]) -> List[Alert]:
        """
        Evaluate logs against rules.

        Args:
            logs: Log entries to evaluate

        Returns:
            List of triggered alerts
        """
        alerts = []

        for rule in self.rules.values():
            if not rule.enabled or not rule.log_level:
                continue

            # Check cooldown
            if rule.last_triggered:
                cooldown_end = rule.last_triggered + timedelta(minutes=rule.cooldown_minutes)
                if datetime.utcnow() < cooldown_end:
                    continue

            # Filter logs by level and time window
            matching_logs = [
                log for log in logs
                if log.level == rule.log_level
                and (datetime.utcnow() - log.timestamp).total_seconds() <= rule.time_window_minutes * 60
            ]

            # Check occurrence count
            if len(matching_logs) >= rule.occurrence_count:
                alert = self._create_alert_from_rule(
                    rule,
                    f"{rule.description}: {len(matching_logs)} occurrences in {rule.time_window_minutes} minutes",
                    {
                        "log_count": len(matching_logs),
                        "time_window": f"{rule.time_window_minutes} minutes",
                        "sample_messages": [log.message[:100] for log in matching_logs[:3]],
                    },
                )
                alerts.append(alert)
                rule.last_triggered = datetime.utcnow()

        return alerts

    def evaluate_anomaly(self, anomaly: Anomaly) -> List[Alert]:
        """
        Convert anomaly to alert.

        Args:
            anomaly: Detected anomaly

        Returns:
            List containing alert for the anomaly
        """
        # Anomalies always generate alerts
        priority = NotificationPriority.MEDIUM
        if anomaly.severity == "critical":
            priority = NotificationPriority.CRITICAL
        elif anomaly.severity == "high":
            priority = NotificationPriority.HIGH

        alert = Alert(
            id=anomaly.id,
            title=f"Anomaly Detected: {anomaly.type.value}",
            message=anomaly.description,
            priority=priority,
            source="anomaly_detector",
            timestamp=anomaly.timestamp,
            metadata={
                "anomaly_type": anomaly.type.value,
                "severity": anomaly.severity,
                "confidence": anomaly.confidence_score,
                "affected_component": anomaly.affected_component,
            },
            tags=["anomaly", anomaly.type.value],
            fingerprint=anomaly.id,
            group_key=anomaly.type.value,
        )

        return [alert]

    def _get_metric_value(self, metrics: SystemMetrics, metric_type: str) -> Optional[float]:
        """Get metric value by type."""
        metric_map = {
            "cpu": metrics.cpu_percent,
            "memory": metrics.memory_percent,
            "disk": metrics.disk_usage_percent,
        }
        return metric_map.get(metric_type)

    def _evaluate_condition(
        self, value: float, threshold: Optional[float], comparison: str
    ) -> bool:
        """Evaluate a comparison condition."""
        if threshold is None:
            return False

        comparisons = {
            ">": lambda v, t: v > t,
            ">=": lambda v, t: v >= t,
            "<": lambda v, t: v < t,
            "<=": lambda v, t: v <= t,
            "==": lambda v, t: v == t,
            "!=": lambda v, t: v != t,
        }

        comparator = comparisons.get(comparison)
        if not comparator:
            return False

        return comparator(value, threshold)

    def _create_alert_from_rule(
        self, rule: AlertRule, message: str, metadata: Dict[str, Any]
    ) -> Alert:
        """Create an alert from a triggered rule."""
        return Alert(
            id=f"{rule.name}_{datetime.utcnow().isoformat()}",
            title=rule.name.replace("_", " ").title(),
            message=message,
            priority=rule.priority,
            source="alert_rules",
            tags=rule.tags,
            metadata={**rule.metadata, **metadata},
            fingerprint=rule.name,  # Same rule = same fingerprint for dedup
            group_key=rule.name,
        )

    def get_rule(self, rule_name: str) -> Optional[AlertRule]:
        """Get a rule by name."""
        return self.rules.get(rule_name)

    def list_rules(self, enabled_only: bool = False) -> List[AlertRule]:
        """List all rules."""
        rules = list(self.rules.values())
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return rules

    def enable_rule(self, rule_name: str) -> bool:
        """Enable a rule."""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = True
            return True
        return False

    def disable_rule(self, rule_name: str) -> bool:
        """Disable a rule."""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = False
            return True
        return False
