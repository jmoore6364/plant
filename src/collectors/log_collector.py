"""Log collection and parsing module."""

import re
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import json

from src.models.schemas import LogEntry, LogLevel, LogFormat


class LogCollector:
    """Collects and parses log files in various formats."""

    # Common log patterns
    SYSLOG_PATTERN = re.compile(
        r"(?P<timestamp>\w+\s+\d+\s+\d+:\d+:\d+)\s+"
        r"(?P<host>\S+)\s+"
        r"(?P<process>\S+?)(\[(?P<pid>\d+)\])?\s*:\s*"
        r"(?P<message>.*)"
    )

    APACHE_PATTERN = re.compile(
        r'(?P<ip>\S+)\s+\S+\s+\S+\s+'
        r'\[(?P<timestamp>[^\]]+)\]\s+'
        r'"(?P<method>\S+)\s+(?P<path>\S+)\s+(?P<protocol>\S+)"\s+'
        r'(?P<status>\d+)\s+(?P<size>\S+)'
    )

    LEVEL_PATTERNS = {
        LogLevel.DEBUG: re.compile(r"\b(DEBUG|TRACE)\b", re.IGNORECASE),
        LogLevel.INFO: re.compile(r"\b(INFO|INFORMATION)\b", re.IGNORECASE),
        LogLevel.WARNING: re.compile(r"\b(WARN|WARNING)\b", re.IGNORECASE),
        LogLevel.ERROR: re.compile(r"\b(ERROR|ERR)\b", re.IGNORECASE),
        LogLevel.CRITICAL: re.compile(r"\b(CRITICAL|FATAL|SEVERE)\b", re.IGNORECASE),
    }

    def __init__(self) -> None:
        """Initialize the log collector."""
        self.entries: List[LogEntry] = []

    def parse_file(
        self, file_path: str, log_format: LogFormat = LogFormat.CUSTOM, limit: Optional[int] = None
    ) -> List[LogEntry]:
        """
        Parse a log file and extract log entries.

        Args:
            file_path: Path to the log file
            log_format: Expected log format
            limit: Maximum number of lines to parse

        Returns:
            List of parsed log entries
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Log file not found: {file_path}")

        entries = []
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, line in enumerate(f, 1):
                if limit and line_num > limit:
                    break

                line = line.strip()
                if not line:
                    continue

                entry = self._parse_line(line, log_format, str(path), line_num)
                if entry:
                    entries.append(entry)

        self.entries.extend(entries)
        return entries

    def parse_string(self, content: str, log_format: LogFormat = LogFormat.CUSTOM) -> List[LogEntry]:
        """
        Parse log content from a string.

        Args:
            content: Log content as string
            log_format: Expected log format

        Returns:
            List of parsed log entries
        """
        entries = []
        for line_num, line in enumerate(content.split("\n"), 1):
            line = line.strip()
            if not line:
                continue

            entry = self._parse_line(line, log_format, "string", line_num)
            if entry:
                entries.append(entry)

        return entries

    def _parse_line(
        self, line: str, log_format: LogFormat, source: str, line_num: int
    ) -> Optional[LogEntry]:
        """Parse a single log line based on format."""
        if log_format == LogFormat.JSON:
            return self._parse_json_log(line, source, line_num)
        elif log_format == LogFormat.SYSLOG:
            return self._parse_syslog(line, source, line_num)
        elif log_format == LogFormat.APACHE:
            return self._parse_apache_log(line, source, line_num)
        else:
            return self._parse_custom_log(line, source, line_num)

    def _parse_json_log(self, line: str, source: str, line_num: int) -> Optional[LogEntry]:
        """Parse JSON formatted log."""
        try:
            data = json.loads(line)
            timestamp = self._parse_timestamp(
                data.get("timestamp") or data.get("time") or data.get("@timestamp")
            )
            level = self._extract_level(
                data.get("level") or data.get("severity") or "INFO"
            )
            message = data.get("message") or data.get("msg") or str(data)

            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=message,
                source=source,
                raw_line=line,
                metadata=data,
                line_number=line_num,
            )
        except json.JSONDecodeError:
            return None

    def _parse_syslog(self, line: str, source: str, line_num: int) -> Optional[LogEntry]:
        """Parse syslog formatted log."""
        match = self.SYSLOG_PATTERN.match(line)
        if match:
            groups = match.groupdict()
            timestamp = self._parse_timestamp(groups["timestamp"])
            level = self._detect_level(groups["message"])

            metadata = {
                "host": groups.get("host"),
                "process": groups.get("process"),
                "pid": groups.get("pid"),
            }

            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=groups["message"],
                source=source,
                raw_line=line,
                metadata=metadata,
                line_number=line_num,
            )
        return None

    def _parse_apache_log(self, line: str, source: str, line_num: int) -> Optional[LogEntry]:
        """Parse Apache access log."""
        match = self.APACHE_PATTERN.match(line)
        if match:
            groups = match.groupdict()
            timestamp = self._parse_timestamp(groups["timestamp"])

            status_code = int(groups["status"])
            level = LogLevel.ERROR if status_code >= 400 else LogLevel.INFO

            message = f"{groups['method']} {groups['path']} - {status_code}"
            metadata = {
                "ip": groups["ip"],
                "method": groups["method"],
                "path": groups["path"],
                "status": status_code,
                "size": groups["size"],
            }

            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=message,
                source=source,
                raw_line=line,
                metadata=metadata,
                line_number=line_num,
            )
        return None

    def _parse_custom_log(self, line: str, source: str, line_num: int) -> LogEntry:
        """Parse custom/unknown format log."""
        timestamp = self._extract_timestamp_from_line(line) or datetime.utcnow()
        level = self._detect_level(line)

        return LogEntry(
            timestamp=timestamp,
            level=level,
            message=line,
            source=source,
            raw_line=line,
            line_number=line_num,
        )

    def _detect_level(self, text: str) -> LogLevel:
        """Detect log level from text content."""
        for level, pattern in self.LEVEL_PATTERNS.items():
            if pattern.search(text):
                return level
        return LogLevel.INFO

    def _extract_level(self, level_str: str) -> LogLevel:
        """Extract LogLevel from string."""
        level_upper = level_str.upper()
        try:
            return LogLevel(level_upper)
        except ValueError:
            # Try to match common variations
            if "WARN" in level_upper:
                return LogLevel.WARNING
            elif "ERR" in level_upper or "FATAL" in level_upper:
                return LogLevel.ERROR
            elif "DEBUG" in level_upper or "TRACE" in level_upper:
                return LogLevel.DEBUG
            return LogLevel.INFO

    def _parse_timestamp(self, ts_str: Optional[str]) -> datetime:
        """Parse timestamp from various formats."""
        if not ts_str:
            return datetime.utcnow()

        # Try common formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%b %d %H:%M:%S",
            "%d/%b/%Y:%H:%M:%S %z",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(ts_str, fmt)
            except ValueError:
                continue

        # If all else fails, return current time
        return datetime.utcnow()

    def _extract_timestamp_from_line(self, line: str) -> Optional[datetime]:
        """Try to extract timestamp from anywhere in the line."""
        # ISO format
        iso_pattern = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")
        match = iso_pattern.search(line)
        if match:
            return self._parse_timestamp(match.group())

        return None

    def filter_by_level(self, min_level: LogLevel) -> List[LogEntry]:
        """Filter entries by minimum log level."""
        level_order = [
            LogLevel.DEBUG,
            LogLevel.INFO,
            LogLevel.WARNING,
            LogLevel.ERROR,
            LogLevel.CRITICAL,
        ]
        min_index = level_order.index(min_level)

        return [
            entry
            for entry in self.entries
            if level_order.index(entry.level) >= min_index
        ]

    def filter_by_pattern(self, pattern: str) -> List[LogEntry]:
        """Filter entries by regex pattern in message."""
        compiled = re.compile(pattern, re.IGNORECASE)
        return [entry for entry in self.entries if compiled.search(entry.message)]

    def get_error_summary(self) -> dict:
        """Get summary of errors and warnings."""
        errors = [e for e in self.entries if e.level == LogLevel.ERROR]
        warnings = [e for e in self.entries if e.level == LogLevel.WARNING]
        critical = [e for e in self.entries if e.level == LogLevel.CRITICAL]

        return {
            "total_entries": len(self.entries),
            "errors": len(errors),
            "warnings": len(warnings),
            "critical": len(critical),
            "error_entries": errors[:10],  # First 10 errors
            "critical_entries": critical,
        }
