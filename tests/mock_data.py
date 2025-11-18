"""
Mock data generators for testing.

Provides realistic test data for all system components including
logs, metrics, alerts, diagnoses, fixes, and PRs.
"""

import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json


class MockLogGenerator:
    """Generate realistic log entries for testing."""

    LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    COMPONENTS = ["api", "database", "cache", "worker", "scheduler", "auth"]
    ERROR_MESSAGES = [
        "Connection timeout to database",
        "Failed to acquire lock",
        "API rate limit exceeded",
        "Memory allocation failed",
        "Disk space low",
        "Cache miss rate high",
        "Authentication failed",
        "Permission denied",
        "Resource not found",
        "Invalid request format",
    ]
    INFO_MESSAGES = [
        "Request completed successfully",
        "Cache hit",
        "Connection established",
        "Task scheduled",
        "User authenticated",
        "Data synchronized",
        "Backup completed",
        "Health check passed",
    ]

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_entry(
        self,
        timestamp: Optional[datetime] = None,
        level: Optional[str] = None,
        component: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a single log entry."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        if level is None:
            # Weight towards INFO/WARNING, fewer errors
            level = random.choices(
                self.LOG_LEVELS,
                weights=[10, 50, 25, 10, 5]
            )[0]

        if component is None:
            component = random.choice(self.COMPONENTS)

        if level in ["ERROR", "CRITICAL"]:
            message = random.choice(self.ERROR_MESSAGES)
        else:
            message = random.choice(self.INFO_MESSAGES)

        return {
            "timestamp": timestamp.isoformat(),
            "level": level,
            "component": component,
            "message": message,
            "metadata": {
                "request_id": f"req_{random.randint(1000, 9999)}",
                "user_id": random.randint(1, 1000),
                "duration_ms": random.randint(10, 5000)
            }
        }

    def generate_batch(
        self,
        count: int,
        start_time: Optional[datetime] = None,
        duration_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """Generate a batch of log entries over a time period."""
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(minutes=duration_minutes)

        entries = []
        for i in range(count):
            # Distribute entries evenly over the duration
            offset = (duration_minutes * 60 * i) / count
            timestamp = start_time + timedelta(seconds=offset)
            entries.append(self.generate_entry(timestamp=timestamp))

        return entries

    def generate_log_file(self, file_path: str, count: int = 100):
        """Generate a log file with entries."""
        entries = self.generate_batch(count)
        with open(file_path, 'w') as f:
            for entry in entries:
                timestamp = entry["timestamp"]
                level = entry["level"]
                component = entry["component"]
                message = entry["message"]
                f.write(f"{timestamp} [{level}] {component}: {message}\n")


class MockMetricsGenerator:
    """Generate realistic system metrics for testing."""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_snapshot(
        self,
        timestamp: Optional[datetime] = None,
        baseline_cpu: float = 30.0,
        baseline_memory: float = 50.0,
        baseline_disk: float = 60.0,
        anomaly: bool = False
    ) -> Dict[str, Any]:
        """Generate a metrics snapshot."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        # Add some noise
        cpu = baseline_cpu + random.gauss(0, 10)
        memory = baseline_memory + random.gauss(0, 15)
        disk = baseline_disk + random.gauss(0, 5)

        # Create anomalies
        if anomaly:
            cpu = min(95, cpu + random.uniform(30, 50))
            memory = min(95, memory + random.uniform(20, 40))

        return {
            "timestamp": timestamp.isoformat(),
            "cpu": {
                "percent": max(0, min(100, cpu)),
                "count": 8,
                "frequency": 2400
            },
            "memory": {
                "percent": max(0, min(100, memory)),
                "total": 16 * 1024**3,
                "available": int(16 * 1024**3 * (100 - memory) / 100),
                "used": int(16 * 1024**3 * memory / 100)
            },
            "disk": {
                "percent": max(0, min(100, disk)),
                "total": 500 * 1024**3,
                "free": int(500 * 1024**3 * (100 - disk) / 100),
                "used": int(500 * 1024**3 * disk / 100)
            },
            "network": {
                "bytes_sent": random.randint(1000000, 10000000),
                "bytes_recv": random.randint(5000000, 50000000),
                "packets_sent": random.randint(1000, 10000),
                "packets_recv": random.randint(5000, 50000)
            }
        }

    def generate_timeseries(
        self,
        count: int,
        interval_seconds: int = 60,
        start_time: Optional[datetime] = None,
        include_anomalies: bool = False,
        anomaly_probability: float = 0.1
    ) -> List[Dict[str, Any]]:
        """Generate a time series of metrics."""
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(seconds=interval_seconds * count)

        snapshots = []
        for i in range(count):
            timestamp = start_time + timedelta(seconds=interval_seconds * i)
            anomaly = include_anomalies and random.random() < anomaly_probability

            snapshots.append(self.generate_snapshot(
                timestamp=timestamp,
                anomaly=anomaly
            ))

        return snapshots


class MockAlertGenerator:
    """Generate realistic alerts for testing."""

    ALERT_TITLES = [
        "High CPU Usage Detected",
        "Memory Usage Critical",
        "Disk Space Low",
        "API Response Time Degraded",
        "Database Connection Pool Exhausted",
        "Cache Hit Rate Low",
        "Error Rate Spike",
        "Security: Multiple Failed Login Attempts",
    ]

    PRIORITIES = ["low", "medium", "high", "critical"]

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_alert(
        self,
        timestamp: Optional[datetime] = None,
        priority: Optional[str] = None,
        resolved: bool = False
    ) -> Dict[str, Any]:
        """Generate a single alert."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        if priority is None:
            priority = random.choices(
                self.PRIORITIES,
                weights=[20, 40, 30, 10]
            )[0]

        title = random.choice(self.ALERT_TITLES)
        alert_id = f"alert_{int(timestamp.timestamp())}_{random.randint(1000, 9999)}"

        alert = {
            "alert_id": alert_id,
            "timestamp": timestamp.isoformat(),
            "title": title,
            "message": f"Alert triggered: {title}",
            "priority": priority,
            "source": random.choice(["metrics_collector", "log_analyzer", "anomaly_detector"]),
            "channels_sent": random.sample(["slack", "email", "pagerduty", "discord"], k=random.randint(1, 3)),
            "resolved": resolved,
            "metadata": {
                "threshold": random.uniform(80, 95),
                "current_value": random.uniform(85, 100),
                "duration_minutes": random.randint(1, 30)
            }
        }

        if resolved:
            resolution_time = random.uniform(5, 120)
            alert["resolved_at"] = (timestamp + timedelta(minutes=resolution_time)).isoformat()
            alert["resolution_time_minutes"] = resolution_time

        return alert

    def generate_batch(
        self,
        count: int,
        start_time: Optional[datetime] = None,
        duration_hours: int = 24,
        resolution_rate: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Generate a batch of alerts."""
        if start_time is None:
            start_time = datetime.utcnow() - timedelta(hours=duration_hours)

        alerts = []
        for i in range(count):
            offset = (duration_hours * 3600 * i) / count
            timestamp = start_time + timedelta(seconds=offset)
            resolved = random.random() < resolution_rate

            alerts.append(self.generate_alert(
                timestamp=timestamp,
                resolved=resolved
            ))

        return alerts


class MockDiagnosisGenerator:
    """Generate realistic AI diagnoses for testing."""

    CATEGORIES = ["performance", "security", "database", "network", "application"]
    SEVERITIES = ["low", "medium", "high", "critical"]

    ROOT_CAUSES = {
        "performance": [
            "N+1 query problem",
            "Missing database indexes",
            "Memory leak in application",
            "CPU-intensive operation in hot path",
        ],
        "security": [
            "SQL injection vulnerability",
            "Missing authentication check",
            "Insecure password storage",
            "CORS misconfiguration",
        ],
        "database": [
            "Connection pool exhausted",
            "Deadlock detected",
            "Slow query performance",
            "Replication lag",
        ],
        "network": [
            "DNS resolution failure",
            "Load balancer misconfiguration",
            "Network timeout",
            "SSL certificate expired",
        ],
        "application": [
            "Unhandled exception",
            "Resource cleanup failure",
            "Race condition",
            "Invalid state transition",
        ]
    }

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_diagnosis(
        self,
        timestamp: Optional[datetime] = None,
        category: Optional[str] = None,
        severity: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a diagnosis."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        if category is None:
            category = random.choice(self.CATEGORIES)

        if severity is None:
            severity = random.choice(self.SEVERITIES)

        root_cause = random.choice(self.ROOT_CAUSES[category])

        return {
            "diagnosis_id": f"diag_{int(timestamp.timestamp())}_{random.randint(1000, 9999)}",
            "timestamp": timestamp.isoformat(),
            "category": category,
            "severity": severity,
            "root_cause": root_cause,
            "impact": f"Potential {category} degradation",
            "confidence_score": random.uniform(0.7, 0.99),
            "recommendations": [
                f"Fix {root_cause.lower()}",
                "Monitor for improvements",
                "Run validation tests"
            ],
            "affected_components": random.sample(
                ["api", "database", "cache", "worker", "frontend"],
                k=random.randint(1, 3)
            )
        }


class MockFixGenerator:
    """Generate realistic fix proposals for testing."""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_fix(
        self,
        diagnosis: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate a fix proposal."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        fix_id = f"fix_{int(timestamp.timestamp())}_{random.randint(1000, 9999)}"

        return {
            "fix_id": fix_id,
            "timestamp": timestamp.isoformat(),
            "diagnosis_id": diagnosis.get("diagnosis_id"),
            "proposed_changes": [
                {
                    "file_path": f"src/{random.choice(['api', 'core', 'database'])}/service.py",
                    "description": f"Fix for {diagnosis.get('root_cause', 'issue')}",
                    "changes": "Add proper error handling and validation",
                    "confidence": random.uniform(0.8, 0.95)
                }
            ],
            "test_commands": ["pytest tests/", "mypy src/"],
            "validation_steps": [
                "Run unit tests",
                "Check metrics",
                "Monitor for 24 hours"
            ],
            "confidence_score": random.uniform(0.75, 0.95),
            "status": random.choice(["proposed", "applied", "validated", "rejected"]),
            "applied": random.choice([True, False])
        }


class MockPRGenerator:
    """Generate realistic PR data for testing."""

    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)

    def generate_pr(
        self,
        fix: Dict[str, Any],
        timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Generate a PR."""
        if timestamp is None:
            timestamp = datetime.utcnow()

        pr_number = random.randint(100, 9999)
        merged = random.choice([True, False, None])

        pr = {
            "pr_id": f"pr_{pr_number}",
            "timestamp": timestamp.isoformat(),
            "fix_id": fix.get("fix_id"),
            "pr_number": pr_number,
            "title": f"Fix: {fix.get('proposed_changes', [{}])[0].get('description', 'Issue')}",
            "url": f"https://github.com/org/repo/pull/{pr_number}",
            "branch_name": f"auto-fix-{fix.get('fix_id', 'unknown')}",
            "status": random.choice(["open", "merged", "closed"]),
            "merged": merged
        }

        if merged:
            merge_time = random.uniform(1, 48)
            pr["merged_at"] = (timestamp + timedelta(hours=merge_time)).isoformat()
            pr["time_to_merge_hours"] = merge_time

        return pr


# Helper function to generate complete mock dataset
def generate_mock_dataset(
    days: int = 7,
    metrics_per_day: int = 1440,  # Every minute
    logs_per_day: int = 10000,
    alerts_per_day: int = 10
) -> Dict[str, Any]:
    """Generate a complete mock dataset for testing."""
    start_time = datetime.utcnow() - timedelta(days=days)

    metrics_gen = MockMetricsGenerator()
    logs_gen = MockLogGenerator()
    alerts_gen = MockAlertGenerator()
    diagnosis_gen = MockDiagnosisGenerator()
    fix_gen = MockFixGenerator()
    pr_gen = MockPRGenerator()

    # Generate metrics
    metrics = metrics_gen.generate_timeseries(
        count=metrics_per_day * days,
        interval_seconds=60,
        start_time=start_time,
        include_anomalies=True,
        anomaly_probability=0.05
    )

    # Generate logs
    logs = logs_gen.generate_batch(
        count=logs_per_day * days,
        start_time=start_time,
        duration_minutes=days * 24 * 60
    )

    # Generate alerts
    alerts = alerts_gen.generate_batch(
        count=alerts_per_day * days,
        start_time=start_time,
        duration_hours=days * 24,
        resolution_rate=0.7
    )

    # Generate diagnoses for high-priority alerts
    diagnoses = []
    fixes = []
    prs = []

    for alert in alerts:
        if alert["priority"] in ["high", "critical"]:
            diagnosis = diagnosis_gen.generate_diagnosis(
                timestamp=datetime.fromisoformat(alert["timestamp"]),
                severity=alert["priority"]
            )
            diagnoses.append(diagnosis)

            # 60% of diagnoses get fixes
            if random.random() < 0.6:
                fix = fix_gen.generate_fix(diagnosis)
                fixes.append(fix)

                # 50% of fixes get PRs
                if random.random() < 0.5:
                    pr = pr_gen.generate_pr(fix)
                    prs.append(pr)

    return {
        "metrics": metrics,
        "logs": logs,
        "alerts": alerts,
        "diagnoses": diagnoses,
        "fixes": fixes,
        "prs": prs,
        "summary": {
            "days": days,
            "total_metrics": len(metrics),
            "total_logs": len(logs),
            "total_alerts": len(alerts),
            "total_diagnoses": len(diagnoses),
            "total_fixes": len(fixes),
            "total_prs": len(prs),
            "start_time": start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat()
        }
    }


if __name__ == "__main__":
    # Example usage
    dataset = generate_mock_dataset(days=7)
    print(json.dumps(dataset["summary"], indent=2))
