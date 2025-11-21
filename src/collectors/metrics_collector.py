"""System metrics collection module."""

import psutil
from datetime import datetime
from typing import Optional, List, Dict, Any
import time
import asyncio

from src.models.schemas import SystemMetrics


class MetricsCollector:
    """Collects system resource metrics using psutil."""

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self.baseline_network = psutil.net_io_counters()
        self.history: List[SystemMetrics] = []

    def collect(self) -> SystemMetrics:
        """
        Collect current system metrics.

        Returns:
            SystemMetrics object with current readings
        """
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_mb = memory.available / (1024 * 1024)

        # Disk metrics
        disk = psutil.disk_usage("/")
        disk_usage_percent = disk.percent
        disk_free_gb = disk.free / (1024 * 1024 * 1024)

        # Network metrics
        network = psutil.net_io_counters()
        network_bytes_sent = network.bytes_sent
        network_bytes_recv = network.bytes_recv

        # Process count
        process_count = len(psutil.pids())

        # Load average (Unix-like systems)
        load_average = None
        if hasattr(psutil, "getloadavg"):
            try:
                load_average = list(psutil.getloadavg())
            except (AttributeError, OSError):
                pass

        metrics = SystemMetrics(
            timestamp=datetime.utcnow(),
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_mb=memory_available_mb,
            disk_usage_percent=disk_usage_percent,
            disk_free_gb=disk_free_gb,
            network_bytes_sent=network_bytes_sent,
            network_bytes_recv=network_bytes_recv,
            process_count=process_count,
            load_average=load_average,
        )

        self.history.append(metrics)
        return metrics

    def collect_detailed(self) -> dict:
        """
        Collect detailed system metrics including per-process information.

        Returns:
            Dictionary with comprehensive system metrics
        """
        base_metrics = self.collect()

        # Top CPU processes
        top_cpu_processes = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                top_cpu_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        top_cpu_processes.sort(key=lambda x: x.get("cpu_percent", 0), reverse=True)
        top_cpu_processes = top_cpu_processes[:10]

        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_io_info = {
            "read_bytes": disk_io.read_bytes,
            "write_bytes": disk_io.write_bytes,
            "read_count": disk_io.read_count,
            "write_count": disk_io.write_count,
        } if disk_io else {}

        # Network connections
        try:
            connections = psutil.net_connections()
            connection_states = {}
            for conn in connections:
                state = conn.status
                connection_states[state] = connection_states.get(state, 0) + 1
        except (psutil.AccessDenied, AttributeError):
            connection_states = {}

        return {
            "base_metrics": base_metrics.model_dump(),
            "top_cpu_processes": top_cpu_processes,
            "disk_io": disk_io_info,
            "network_connections": connection_states,
        }

    def monitor_continuously(
        self, interval: int = 60, duration: Optional[int] = None
    ) -> List[SystemMetrics]:
        """
        Monitor system metrics continuously.

        Args:
            interval: Seconds between collections
            duration: Total monitoring duration in seconds (None for infinite)

        Returns:
            List of collected metrics
        """
        start_time = time.time()
        collected = []

        while True:
            metrics = self.collect()
            collected.append(metrics)

            if duration and (time.time() - start_time) >= duration:
                break

            time.sleep(interval)

        return collected

    def get_averages(self, window: int = 5) -> dict:
        """
        Calculate average metrics over recent history.

        Args:
            window: Number of recent samples to average

        Returns:
            Dictionary with average metrics
        """
        if not self.history:
            return {}

        recent = self.history[-window:]
        if not recent:
            return {}

        return {
            "avg_cpu_percent": sum(m.cpu_percent for m in recent) / len(recent),
            "avg_memory_percent": sum(m.memory_percent for m in recent) / len(recent),
            "avg_disk_usage_percent": sum(m.disk_usage_percent for m in recent) / len(recent),
            "sample_count": len(recent),
        }

    def detect_resource_issues(self, metrics: Optional[SystemMetrics] = None) -> List[dict]:
        """
        Detect potential resource issues from metrics.

        Args:
            metrics: Metrics to analyze (uses latest if not provided)

        Returns:
            List of detected issues
        """
        if metrics is None:
            if not self.history:
                return []
            metrics = self.history[-1]

        issues = []

        # High CPU usage
        if metrics.cpu_percent > 90:
            issues.append({
                "type": "cpu_high",
                "severity": "critical" if metrics.cpu_percent > 95 else "high",
                "message": f"CPU usage is {metrics.cpu_percent:.1f}%",
                "value": metrics.cpu_percent,
            })

        # High memory usage
        if metrics.memory_percent > 85:
            issues.append({
                "type": "memory_high",
                "severity": "critical" if metrics.memory_percent > 95 else "high",
                "message": f"Memory usage is {metrics.memory_percent:.1f}%",
                "value": metrics.memory_percent,
            })

        # Low disk space
        if metrics.disk_usage_percent > 90:
            issues.append({
                "type": "disk_full",
                "severity": "critical" if metrics.disk_usage_percent > 95 else "high",
                "message": f"Disk usage is {metrics.disk_usage_percent:.1f}% ({metrics.disk_free_gb:.2f} GB free)",
                "value": metrics.disk_usage_percent,
            })

        # Very low available memory
        if metrics.memory_available_mb < 500:
            issues.append({
                "type": "memory_low",
                "severity": "critical",
                "message": f"Only {metrics.memory_available_mb:.0f} MB memory available",
                "value": metrics.memory_available_mb,
            })

        return issues

    def get_trend_analysis(self, window: int = 10) -> dict:
        """
        Analyze trends in metrics over time.

        Args:
            window: Number of samples to analyze

        Returns:
            Dictionary with trend information
        """
        if len(self.history) < 2:
            return {"status": "insufficient_data"}

        recent = self.history[-window:]
        if len(recent) < 2:
            return {"status": "insufficient_data"}

        # Calculate simple trends
        cpu_trend = recent[-1].cpu_percent - recent[0].cpu_percent
        memory_trend = recent[-1].memory_percent - recent[0].memory_percent
        disk_trend = recent[-1].disk_usage_percent - recent[0].disk_usage_percent

        return {
            "status": "ok",
            "window_size": len(recent),
            "duration_seconds": (recent[-1].timestamp - recent[0].timestamp).total_seconds(),
            "cpu_trend": {
                "change": cpu_trend,
                "direction": "increasing" if cpu_trend > 5 else "decreasing" if cpu_trend < -5 else "stable",
            },
            "memory_trend": {
                "change": memory_trend,
                "direction": "increasing" if memory_trend > 5 else "decreasing" if memory_trend < -5 else "stable",
                "potential_leak": memory_trend > 10,  # Memory increasing significantly
            },
            "disk_trend": {
                "change": disk_trend,
                "direction": "increasing" if disk_trend > 1 else "decreasing" if disk_trend < -1 else "stable",
            },
        }

    async def collect_all(self) -> Dict[str, Any]:
        """
        Collect all system metrics in a structured format.

        This is an async version that returns a comprehensive dictionary
        of all system metrics, suitable for storage and analysis.

        Returns:
            Dictionary with structured metrics data
        """
        # Run psutil operations in executor to avoid blocking
        loop = asyncio.get_event_loop()

        # Collect all metrics
        cpu_percent = await loop.run_in_executor(None, lambda: psutil.cpu_percent(interval=0.1))
        cpu_count = psutil.cpu_count()

        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        network = psutil.net_io_counters()

        return {
            "cpu": {
                "percent": cpu_percent,
                "count": cpu_count,
            },
            "memory": {
                "percent": memory.percent,
                "available": memory.available,
                "total": memory.total,
                "used": memory.used,
            },
            "disk": {
                "percent": disk.percent,
                "free": disk.free,
                "total": disk.total,
                "used": disk.used,
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    def clear_history(self) -> None:
        """Clear metrics history."""
        self.history.clear()
