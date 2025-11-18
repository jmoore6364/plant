"""Tests for log collector."""

import pytest
from datetime import datetime
from src.collectors.log_collector import LogCollector
from src.models.schemas import LogLevel, LogFormat


def test_parse_custom_log():
    """Test parsing custom format logs."""
    collector = LogCollector()
    log_content = """2024-01-15 10:30:45 ERROR Failed to connect
2024-01-15 10:30:46 INFO Connection successful
2024-01-15 10:30:47 WARNING High memory usage"""

    entries = collector.parse_string(log_content, LogFormat.CUSTOM)

    assert len(entries) == 3
    assert entries[0].level == LogLevel.ERROR
    assert entries[1].level == LogLevel.INFO
    assert entries[2].level == LogLevel.WARNING
    assert "Failed to connect" in entries[0].message


def test_parse_json_log():
    """Test parsing JSON format logs."""
    collector = LogCollector()
    log_content = """{"timestamp": "2024-01-15T10:30:45", "level": "ERROR", "message": "Failed"}
{"timestamp": "2024-01-15T10:30:46", "level": "INFO", "message": "Success"}"""

    entries = collector.parse_string(log_content, LogFormat.JSON)

    assert len(entries) == 2
    assert entries[0].level == LogLevel.ERROR
    assert entries[1].level == LogLevel.INFO


def test_filter_by_level():
    """Test filtering logs by level."""
    collector = LogCollector()
    log_content = """2024-01-15 10:30:45 ERROR Error message
2024-01-15 10:30:46 INFO Info message
2024-01-15 10:30:47 DEBUG Debug message
2024-01-15 10:30:48 ERROR Another error"""

    collector.parse_string(log_content, LogFormat.CUSTOM)
    errors = collector.filter_by_level(LogLevel.ERROR)

    assert len(errors) == 2
    assert all(e.level == LogLevel.ERROR for e in errors)


def test_filter_by_pattern():
    """Test filtering logs by regex pattern."""
    collector = LogCollector()
    log_content = """2024-01-15 10:30:45 ERROR Database connection failed
2024-01-15 10:30:46 INFO User logged in
2024-01-15 10:30:47 ERROR Database timeout"""

    collector.parse_string(log_content, LogFormat.CUSTOM)
    db_errors = collector.filter_by_pattern(r"database")

    assert len(db_errors) == 2
    assert all("atabase" in e.message.lower() for e in db_errors)


def test_get_error_summary():
    """Test error summary generation."""
    collector = LogCollector()
    log_content = """2024-01-15 10:30:45 ERROR Error 1
2024-01-15 10:30:46 ERROR Error 2
2024-01-15 10:30:47 WARNING Warning 1
2024-01-15 10:30:48 CRITICAL Critical 1
2024-01-15 10:30:49 INFO Info 1"""

    collector.parse_string(log_content, LogFormat.CUSTOM)
    summary = collector.get_error_summary()

    assert summary["total_entries"] == 5
    assert summary["errors"] == 2
    assert summary["warnings"] == 1
    assert summary["critical"] == 1
