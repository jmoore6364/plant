"""Log analysis and pattern detection."""

from typing import List, Dict, Optional, Any
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re

from src.models.schemas import LogEntry, LogLevel, Anomaly, AnomalyType


class LogAnalyzer:
    """Analyzes logs for patterns, errors, and anomalies."""

    def __init__(self) -> None:
        """Initialize the log analyzer."""
        self.error_patterns = {
            "out_of_memory": re.compile(r"out of memory|oom|memory.*(exhausted|limit)", re.IGNORECASE),
            "connection_refused": re.compile(r"connection refused|econnrefused", re.IGNORECASE),
            "timeout": re.compile(r"timeout|timed out", re.IGNORECASE),
            "null_pointer": re.compile(r"null pointer|nullpointerexception|segfault", re.IGNORECASE),
            "permission_denied": re.compile(r"permission denied|access denied|forbidden", re.IGNORECASE),
            "file_not_found": re.compile(r"file not found|no such file", re.IGNORECASE),
            "database_error": re.compile(r"database.*error|sql.*error|deadlock", re.IGNORECASE),
        }

    async def analyze(
        self,
        logs: Optional[List[LogEntry]] = None,
        metrics: Optional[Dict[str, Any]] = None,
        anomalies: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """
        Perform comprehensive log analysis with optional metrics and anomalies.

        Args:
            logs: List of log entries to analyze (optional)
            metrics: System metrics data (optional)
            anomalies: Detected anomalies (optional)

        Returns:
            Dictionary with analysis results
        """
        if logs is None:
            logs = []

        result = {}

        # Analyze logs if provided
        if logs:
            result.update({
                "total_logs": len(logs),
                "time_range": self._get_time_range(logs),
                "level_distribution": self._get_level_distribution(logs),
                "error_patterns": self._find_error_patterns(logs),
                "anomalies": self._detect_anomalies(logs),
                "top_sources": self._get_top_sources(logs),
                "error_timeline": self._create_error_timeline(logs),
            })
        else:
            result["total_logs"] = 0

        # Include metrics if provided
        if metrics:
            result["metrics_summary"] = metrics

        # Include anomalies if provided
        if anomalies:
            result["detected_anomalies"] = anomalies

        return result

    def _get_time_range(self, logs: List[LogEntry]) -> Dict:
        """Get time range of logs."""
        timestamps = [log.timestamp for log in logs]
        return {
            "start": min(timestamps).isoformat(),
            "end": max(timestamps).isoformat(),
            "duration_seconds": (max(timestamps) - min(timestamps)).total_seconds(),
        }

    def _get_level_distribution(self, logs: List[LogEntry]) -> Dict:
        """Get distribution of log levels."""
        counter = Counter(log.level for log in logs)
        total = len(logs)

        return {
            level.value: {
                "count": counter.get(level, 0),
                "percentage": (counter.get(level, 0) / total * 100) if total > 0 else 0,
            }
            for level in LogLevel
        }

    def _find_error_patterns(self, logs: List[LogEntry]) -> Dict:
        """Find common error patterns in logs."""
        pattern_matches = defaultdict(list)

        error_logs = [log for log in logs if log.level in (LogLevel.ERROR, LogLevel.CRITICAL)]

        for log in error_logs:
            for pattern_name, pattern in self.error_patterns.items():
                if pattern.search(log.message):
                    pattern_matches[pattern_name].append({
                        "timestamp": log.timestamp.isoformat(),
                        "message": log.message[:200],  # Truncate long messages
                        "source": log.source,
                        "line_number": log.line_number,
                    })

        return {
            pattern: {
                "count": len(matches),
                "examples": matches[:5],  # First 5 examples
            }
            for pattern, matches in pattern_matches.items()
        }

    def _detect_anomalies(self, logs: List[LogEntry]) -> List[Anomaly]:
        """Detect anomalous patterns in logs."""
        anomalies = []

        # Detect error bursts
        error_burst = self._detect_error_burst(logs)
        if error_burst:
            anomalies.append(error_burst)

        # Detect repeating errors
        repeating = self._detect_repeating_errors(logs)
        if repeating:
            anomalies.append(repeating)

        # Detect crash patterns
        crash = self._detect_crash_pattern(logs)
        if crash:
            anomalies.append(crash)

        return anomalies

    def _detect_error_burst(self, logs: List[LogEntry]) -> Optional[Anomaly]:
        """Detect sudden burst of errors."""
        error_logs = [log for log in logs if log.level in (LogLevel.ERROR, LogLevel.CRITICAL)]

        if len(error_logs) < 10:
            return None

        # Check for time windows with high error rate
        window_minutes = 5
        error_counts = defaultdict(int)

        for log in error_logs:
            # Round to nearest N minutes
            window_start = log.timestamp.replace(second=0, microsecond=0)
            window_start = window_start.replace(
                minute=(window_start.minute // window_minutes) * window_minutes
            )
            error_counts[window_start] += 1

        # Find windows with > 10 errors
        for window_start, count in error_counts.items():
            if count > 10:
                window_logs = [
                    log for log in error_logs
                    if window_start <= log.timestamp < window_start + timedelta(minutes=window_minutes)
                ]

                return Anomaly(
                    id=f"error_burst_{window_start.isoformat()}",
                    type=AnomalyType.ERROR_BURST,
                    severity="high",
                    timestamp=window_start,
                    description=f"Detected {count} errors within {window_minutes} minutes",
                    affected_component="system",
                    confidence_score=min(count / 20.0, 1.0),
                    evidence=[log.message[:100] for log in window_logs[:5]],
                    logs=window_logs[:10],
                )

        return None

    def _detect_repeating_errors(self, logs: List[LogEntry]) -> Optional[Anomaly]:
        """Detect the same error repeating many times."""
        error_logs = [log for log in logs if log.level in (LogLevel.ERROR, LogLevel.CRITICAL)]

        if len(error_logs) < 5:
            return None

        # Simplify messages for comparison (remove timestamps, IDs, etc.)
        simplified = defaultdict(list)
        for log in error_logs:
            # Remove numbers and common variable parts
            simple_msg = re.sub(r'\d+', 'N', log.message)
            simple_msg = re.sub(r'[0-9a-f]{8,}', 'ID', simple_msg)
            simplified[simple_msg].append(log)

        # Find most common error
        for simple_msg, matching_logs in simplified.items():
            if len(matching_logs) >= 5:
                return Anomaly(
                    id=f"repeating_error_{hash(simple_msg)}",
                    type=AnomalyType.ERROR_BURST,
                    severity="medium",
                    timestamp=matching_logs[0].timestamp,
                    description=f"Same error repeated {len(matching_logs)} times",
                    affected_component="application",
                    confidence_score=0.9,
                    evidence=[simple_msg[:200]],
                    logs=matching_logs[:10],
                )

        return None

    def _detect_crash_pattern(self, logs: List[LogEntry]) -> Optional[Anomaly]:
        """Detect application crash patterns."""
        crash_keywords = [
            "fatal error", "segmentation fault", "core dumped",
            "uncaught exception", "process terminated", "killed"
        ]

        crash_pattern = re.compile("|".join(crash_keywords), re.IGNORECASE)
        crashes = [log for log in logs if crash_pattern.search(log.message)]

        if crashes:
            return Anomaly(
                id=f"crash_pattern_{crashes[0].timestamp.isoformat()}",
                type=AnomalyType.CRASH_PATTERN,
                severity="critical",
                timestamp=crashes[0].timestamp,
                description=f"Detected {len(crashes)} potential crash(es)",
                affected_component="application",
                confidence_score=0.95,
                evidence=[log.message[:150] for log in crashes[:3]],
                logs=crashes[:5],
            )

        return None

    def _get_top_sources(self, logs: List[LogEntry], limit: int = 10) -> List[Dict]:
        """Get top log sources by volume."""
        counter = Counter(log.source for log in logs)
        total = len(logs)

        return [
            {
                "source": source,
                "count": count,
                "percentage": (count / total * 100) if total > 0 else 0,
            }
            for source, count in counter.most_common(limit)
        ]

    def _create_error_timeline(self, logs: List[LogEntry], bucket_minutes: int = 10) -> List[Dict]:
        """Create timeline of errors."""
        error_logs = [log for log in logs if log.level in (LogLevel.ERROR, LogLevel.CRITICAL)]

        if not error_logs:
            return []

        # Group errors by time bucket
        buckets = defaultdict(int)
        for log in error_logs:
            bucket_time = log.timestamp.replace(second=0, microsecond=0)
            bucket_time = bucket_time.replace(
                minute=(bucket_time.minute // bucket_minutes) * bucket_minutes
            )
            buckets[bucket_time] += 1

        # Convert to sorted list
        timeline = [
            {
                "timestamp": timestamp.isoformat(),
                "error_count": count,
            }
            for timestamp, count in sorted(buckets.items())
        ]

        return timeline

    def find_correlations(self, logs: List[LogEntry], window_seconds: int = 60) -> List[Dict]:
        """
        Find correlated events in logs.

        Args:
            logs: Log entries to analyze
            window_seconds: Time window for correlation

        Returns:
            List of correlated event groups
        """
        correlations = []
        error_logs = [log for log in logs if log.level in (LogLevel.ERROR, LogLevel.CRITICAL)]

        # Sort by timestamp
        sorted_logs = sorted(error_logs, key=lambda x: x.timestamp)

        # Find groups of errors within time window
        i = 0
        while i < len(sorted_logs):
            group = [sorted_logs[i]]
            j = i + 1

            while j < len(sorted_logs):
                time_diff = (sorted_logs[j].timestamp - sorted_logs[i].timestamp).total_seconds()
                if time_diff <= window_seconds:
                    group.append(sorted_logs[j])
                    j += 1
                else:
                    break

            if len(group) >= 3:  # At least 3 correlated errors
                correlations.append({
                    "start_time": group[0].timestamp.isoformat(),
                    "end_time": group[-1].timestamp.isoformat(),
                    "event_count": len(group),
                    "messages": [log.message[:100] for log in group[:5]],
                })

            i = j if j > i + 1 else i + 1

        return correlations
