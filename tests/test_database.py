"""Tests for database operations."""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.database.models import Base, AnalysisRun, MetricsSnapshot, AlertHistory, IssueRecurrence
from src.database.repository import (
    AnalysisRepository,
    MetricsRepository,
    AlertRepository,
    IssueRecurrenceRepository,
)
from src.database.analytics import AnalyticsEngine
from src.database.retention import DataRetentionManager


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def test_db():
    """Create test database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_create_analysis_run(test_db):
    """Test creating an analysis run."""
    repo = AnalysisRepository(test_db)

    analysis_data = {
        "request_id": "test_123",
        "logs_analyzed": 100,
        "anomalies_found": 5,
        "processing_time_ms": 1500.0,
        "success": True,
    }

    analysis = await repo.create(analysis_data)

    assert analysis.id is not None
    assert analysis.request_id == "test_123"
    assert analysis.logs_analyzed == 100


@pytest.mark.asyncio
async def test_get_recent_analyses(test_db):
    """Test getting recent analyses."""
    repo = AnalysisRepository(test_db)

    # Create multiple analyses
    for i in range(5):
        await repo.create({
            "request_id": f"test_{i}",
            "logs_analyzed": 100 + i,
            "success": True,
        })

    await test_db.commit()

    # Get recent
    recent = await repo.get_recent(limit=10, hours=24)

    assert len(recent) == 5
    assert recent[0].logs_analyzed > recent[-1].logs_analyzed  # Newest first


@pytest.mark.asyncio
async def test_metrics_snapshot(test_db):
    """Test storing metrics snapshots."""
    repo = MetricsRepository(test_db)

    snapshot_data = {
        "cpu_percent": 75.5,
        "memory_percent": 60.2,
        "disk_usage_percent": 45.0,
        "memory_available_mb": 4096.0,
        "disk_free_gb": 100.0,
        "network_bytes_sent": 1000000,
        "network_bytes_recv": 2000000,
        "process_count": 150,
    }

    snapshot = await repo.create(snapshot_data)

    assert snapshot.id is not None
    assert snapshot.cpu_percent == 75.5
    assert snapshot.memory_percent == 60.2


@pytest.mark.asyncio
async def test_metrics_averages(test_db):
    """Test calculating metric averages."""
    repo = MetricsRepository(test_db)

    # Create snapshots with varying metrics
    for i in range(10):
        await repo.create({
            "cpu_percent": 50.0 + i,
            "memory_percent": 60.0 + i,
            "disk_usage_percent": 40.0,
            "memory_available_mb": 4096.0,
            "disk_free_gb": 100.0,
            "network_bytes_sent": 1000000,
            "network_bytes_recv": 2000000,
            "process_count": 150,
        })

    await test_db.commit()

    # Get averages
    averages = await repo.get_averages(hours=24)

    assert averages["avg_cpu_percent"] > 50.0
    assert averages["avg_memory_percent"] > 60.0


@pytest.mark.asyncio
async def test_alert_creation_and_resolution(test_db):
    """Test alert lifecycle."""
    repo = AlertRepository(test_db)

    alert_data = {
        "alert_id": "alert_001",
        "title": "High CPU",
        "message": "CPU at 95%",
        "priority": "high",
        "source": "metrics",
        "fingerprint": "cpu_high",
    }

    alert = await repo.create(alert_data)
    await test_db.commit()

    assert alert.id is not None
    assert not alert.resolved

    # Resolve the alert
    success = await repo.mark_resolved("alert_001")
    await test_db.commit()

    assert success

    # Check it's resolved
    resolved_alert = await repo.get_by_id("alert_001")
    assert resolved_alert.resolved
    assert resolved_alert.resolved_at is not None
    assert resolved_alert.resolution_time_minutes is not None


@pytest.mark.asyncio
async def test_alert_stats(test_db):
    """Test alert statistics."""
    repo = AlertRepository(test_db)

    # Create alerts with different priorities
    for i in range(3):
        await repo.create({
            "alert_id": f"alert_high_{i}",
            "title": "High Alert",
            "message": "Test",
            "priority": "high",
            "source": "test",
        })

    for i in range(2):
        await repo.create({
            "alert_id": f"alert_critical_{i}",
            "title": "Critical Alert",
            "message": "Test",
            "priority": "critical",
            "source": "test",
        })

    await test_db.commit()

    # Get stats
    stats = await repo.get_stats(hours=24)

    assert stats["total_alerts"] == 5
    assert stats["by_priority"]["high"] == 3
    assert stats["by_priority"]["critical"] == 2


@pytest.mark.asyncio
async def test_issue_recurrence_tracking(test_db):
    """Test issue recurrence detection."""
    repo = IssueRecurrenceRepository(test_db)

    # Record multiple occurrences of same issue
    for i in range(5):
        recurrence = await repo.record_occurrence(
            fingerprint="memory_leak",
            title="Memory Leak Detected",
            category="performance",
        )

    await test_db.commit()

    # Should have single record with 5 occurrences
    assert recurrence.occurrence_count == 5
    assert recurrence.issue_fingerprint == "memory_leak"

    # Get recurring issues
    recurring = await repo.get_recurring_issues(min_occurrences=3)

    assert len(recurring) == 1
    assert recurring[0].occurrence_count == 5


@pytest.mark.asyncio
async def test_analytics_system_health_score(test_db):
    """Test system health score calculation."""
    # Create some metrics
    metrics_repo = MetricsRepository(test_db)

    for i in range(10):
        await metrics_repo.create({
            "cpu_percent": 60.0,
            "memory_percent": 50.0,
            "disk_usage_percent": 40.0,
            "memory_available_mb": 4096.0,
            "disk_free_gb": 100.0,
            "network_bytes_sent": 1000000,
            "network_bytes_recv": 2000000,
            "process_count": 150,
        })

    await test_db.commit()

    # Calculate health score
    engine = AnalyticsEngine(test_db)
    score = await engine.get_system_health_score()
    await test_db.commit()

    assert "overall_score" in score
    assert 0 <= score["overall_score"] <= 100
    assert "performance_score" in score
    assert "reliability_score" in score


@pytest.mark.asyncio
async def test_data_retention_cleanup(test_db):
    """Test data retention and cleanup."""
    # Create old and new alerts
    repo = AlertRepository(test_db)

    # Old alert (35 days ago)
    old_alert = AlertHistory(
        alert_id="old_alert",
        title="Old Alert",
        message="Old",
        priority="low",
        source="test",
        timestamp=datetime.utcnow() - timedelta(days=35),
    )
    test_db.add(old_alert)

    # Recent alert
    recent_alert = AlertHistory(
        alert_id="recent_alert",
        title="Recent Alert",
        message="Recent",
        priority="low",
        source="test",
        timestamp=datetime.utcnow(),
    )
    test_db.add(recent_alert)

    await test_db.commit()

    # Clean up with 30-day retention
    manager = DataRetentionManager(test_db)
    result = await manager.cleanup_old_data("alert_history", retention_days=30)

    assert result["success"]
    assert result["records_deleted"] == 1

    # Verify old alert is gone
    remaining = await repo.get_recent(hours=24 * 100)
    assert len(remaining) == 1
    assert remaining[0].alert_id == "recent_alert"


@pytest.mark.asyncio
async def test_trend_analysis(test_db):
    """Test metrics trend analysis."""
    repo = MetricsRepository(test_db)

    # Create increasing CPU trend
    for i in range(20):
        await repo.create({
            "cpu_percent": 50.0 + i * 2,  # Increasing from 50 to 88
            "memory_percent": 60.0,
            "disk_usage_percent": 40.0,
            "memory_available_mb": 4096.0,
            "disk_free_gb": 100.0,
            "network_bytes_sent": 1000000,
            "network_bytes_recv": 2000000,
            "process_count": 150,
        })

    await test_db.commit()

    # Analyze trend
    engine = AnalyticsEngine(test_db)
    trend = await engine.get_trend_analysis("cpu", hours=24)

    assert trend["trend_direction"] == "increasing"
    assert trend["average"] > 50
    assert "predicted_next" in trend


@pytest.mark.asyncio
async def test_database_stats(test_db):
    """Test database size statistics."""
    # Create some data
    metrics_repo = MetricsRepository(test_db)
    alert_repo = AlertRepository(test_db)

    for i in range(5):
        await metrics_repo.create({
            "cpu_percent": 60.0,
            "memory_percent": 50.0,
            "disk_usage_percent": 40.0,
            "memory_available_mb": 4096.0,
            "disk_free_gb": 100.0,
            "network_bytes_sent": 1000000,
            "network_bytes_recv": 2000000,
            "process_count": 150,
        })

        await alert_repo.create({
            "alert_id": f"alert_{i}",
            "title": "Test Alert",
            "message": "Test",
            "priority": "low",
            "source": "test",
        })

    await test_db.commit()

    # Get stats
    manager = DataRetentionManager(test_db)
    stats = await manager.get_database_size_stats()

    assert stats["total_records"] >= 10
    assert "metrics_snapshots" in stats["tables"]
    assert "alert_history" in stats["tables"]
    assert stats["tables"]["metrics_snapshots"]["record_count"] == 5
    assert stats["tables"]["alert_history"]["record_count"] == 5
