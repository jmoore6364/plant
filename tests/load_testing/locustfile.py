"""
Load testing suite for API endpoints using Locust.

Run with: locust -f tests/load_testing/locustfile.py --host=http://localhost:8000
"""

from locust import HttpUser, task, between, tag
import random
import json
from datetime import datetime, timedelta


class SystemHealthAnalyzerUser(HttpUser):
    """Simulate a user interacting with the System Health Analyzer API."""

    wait_time = between(1, 3)  # Wait 1-3 seconds between requests

    def on_start(self):
        """Called when a simulated user starts."""
        self.analysis_run_id = None
        self.alert_ids = []
        self.fix_ids = []

    @task(10)
    @tag('health')
    def health_check(self):
        """Test the health endpoint."""
        self.client.get("/health")

    @task(5)
    @tag('metrics')
    def get_metrics(self):
        """Test metrics collection endpoint."""
        self.client.get("/api/metrics")

    @task(8)
    @tag('analysis')
    def trigger_analysis(self):
        """Test analysis trigger endpoint."""
        response = self.client.post("/api/analyze", json={
            "trigger": "manual",
            "components": ["logs", "metrics", "anomalies"]
        })

        if response.status_code == 200:
            data = response.json()
            self.analysis_run_id = data.get("run_id")

    @task(3)
    @tag('analysis')
    def get_analysis_status(self):
        """Test getting analysis status."""
        if self.analysis_run_id:
            self.client.get(f"/api/analyze/{self.analysis_run_id}")

    @task(6)
    @tag('history')
    def get_recent_analyses(self):
        """Test getting recent analyses."""
        hours = random.choice([1, 6, 12, 24])
        self.client.get(f"/history/analyses?hours={hours}&limit=20")

    @task(7)
    @tag('history', 'metrics')
    def get_metrics_history(self):
        """Test getting metrics history."""
        hours = random.choice([1, 6, 24])
        self.client.get(f"/history/metrics?hours={hours}&limit=100")

    @task(4)
    @tag('history', 'alerts')
    def get_alert_history(self):
        """Test getting alert history."""
        hours = random.choice([6, 24, 72])
        self.client.get(f"/history/alerts?hours={hours}&limit=50")

    @task(3)
    @tag('analytics')
    def get_health_score(self):
        """Test health score analytics."""
        self.client.get("/history/analytics/health-score")

    @task(3)
    @tag('analytics')
    def get_trends(self):
        """Test trends analytics."""
        self.client.get("/history/analytics/trends?hours=24")

    @task(2)
    @tag('analytics')
    def get_mttr(self):
        """Test MTTR analytics."""
        hours = random.choice([24, 72, 168])
        self.client.get(f"/history/analytics/mttr?hours={hours}")

    @task(2)
    @tag('recurring')
    def get_recurring_issues(self):
        """Test recurring issues endpoint."""
        days = random.choice([7, 14, 30])
        self.client.get(f"/history/recurring-issues?days={days}&min_occurrences=2")

    @task(1)
    @tag('alerts')
    def create_alert(self):
        """Test creating an alert."""
        alert_data = {
            "title": f"Test Alert {random.randint(1000, 9999)}",
            "message": "This is a test alert from load testing",
            "priority": random.choice(["low", "medium", "high"]),
            "source": "load_test",
            "channels": random.sample(["slack", "email"], k=random.randint(1, 2))
        }

        response = self.client.post("/api/alerts", json=alert_data)
        if response.status_code == 200:
            data = response.json()
            self.alert_ids.append(data.get("alert_id"))

    @task(1)
    @tag('notifications')
    def send_notification(self):
        """Test sending a notification."""
        notification_data = {
            "title": f"Load Test Notification {random.randint(1000, 9999)}",
            "message": "Testing notification system under load",
            "priority": random.choice(["low", "medium", "high"]),
            "channels": ["slack"]
        }

        self.client.post("/api/notifications/send", json=notification_data)


class AdminUser(HttpUser):
    """Simulate an admin user performing maintenance tasks."""

    wait_time = between(5, 10)

    @task(1)
    @tag('admin', 'cleanup')
    def cleanup_old_metrics(self):
        """Test data cleanup endpoint."""
        self.client.post("/retention/cleanup/metrics_snapshots?retention_days=30")

    @task(1)
    @tag('admin', 'export')
    def export_data(self):
        """Test data export endpoint."""
        self.client.post("/retention/export/alerts?hours=168")

    @task(2)
    @tag('admin', 'stats')
    def get_alert_stats(self):
        """Test alert statistics."""
        hours = random.choice([24, 72, 168])
        self.client.get(f"/history/alerts/stats?hours={hours}")


class HeavyUser(HttpUser):
    """Simulate a heavy user creating load with large requests."""

    wait_time = between(2, 5)

    @task(3)
    @tag('heavy')
    def bulk_metrics_query(self):
        """Test querying large amounts of metrics."""
        self.client.get("/history/metrics?hours=168&limit=1000")

    @task(2)
    @tag('heavy')
    def complex_analytics(self):
        """Test complex analytics queries."""
        self.client.get("/history/analytics/trends?hours=168")

    @task(2)
    @tag('heavy')
    def large_timerange_query(self):
        """Test queries over large time ranges."""
        self.client.get("/history/analyses?hours=720&limit=500")


# Custom load shapes for different scenarios
from locust import LoadTestShape


class StepLoadShape(LoadTestShape):
    """
    Step load pattern - gradually increase load.

    Steps:
    1. 10 users for 60 seconds
    2. 25 users for 60 seconds
    3. 50 users for 60 seconds
    4. 100 users for 60 seconds
    5. Stay at 100 users
    """

    step_time = 60
    step_load = 10
    spawn_rate = 5
    time_limit = 300

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        current_step = run_time // self.step_time
        return (self.step_load * (current_step + 1), self.spawn_rate)


class SpikeLoadShape(LoadTestShape):
    """
    Spike load pattern - sudden spike in traffic.

    Pattern:
    1. Start with 10 users
    2. Spike to 200 users at 60s
    3. Drop back to 10 users at 90s
    4. Repeat
    """

    time_limit = 300

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        # Calculate position in cycle (120s per cycle)
        cycle_time = run_time % 120

        if cycle_time < 60:
            # Normal load
            return (10, 2)
        elif cycle_time < 90:
            # Spike
            return (200, 20)
        else:
            # Cool down
            return (10, 5)


class WaveLoadShape(LoadTestShape):
    """
    Wave load pattern - sinusoidal load variation.
    """

    import math

    time_limit = 600
    min_users = 10
    max_users = 100

    def tick(self):
        run_time = self.get_run_time()

        if run_time > self.time_limit:
            return None

        # Calculate user count using sine wave
        user_count = int(
            self.min_users +
            (self.max_users - self.min_users) *
            (1 + self.math.sin(run_time / 60)) / 2
        )

        return (user_count, 10)
