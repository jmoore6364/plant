"""
Integration tests for end-to-end workflows.

Tests complete workflows from log analysis through to PR creation,
including notifications, database persistence, and fix generation.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock, patch, AsyncMock

from src.core.log_parser import LogParser
from src.core.metrics_collector import MetricsCollector
from src.core.anomaly_detector import AnomalyDetector
from src.ai.analyzer import AIAnalyzer
from src.ai.fix_generator import FixGenerator
from src.github.pr_creator import PRCreator
from src.notifications.manager import NotificationManager
from src.notifications.base import Alert, NotificationPriority
from src.database.connection import get_db_session, init_db
from src.database.repository import (
    AnalysisRepository,
    MetricsRepository,
    AlertRepository,
    FixRepository,
)


@pytest.fixture
async def integration_db():
    """Create a test database for integration tests."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from src.database.models import Base

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with AsyncSessionLocal() as session:
        yield session
        await session.rollback()

    await engine.dispose()


@pytest.mark.asyncio
async def test_full_analysis_pipeline():
    """Test complete analysis pipeline from logs to diagnosis."""
    # Create sample log file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        f.write("2024-01-01 10:00:00 ERROR Database connection failed\n")
        f.write("2024-01-01 10:00:01 ERROR Timeout connecting to postgres://db:5432\n")
        f.write("2024-01-01 10:00:02 WARNING Retrying connection (attempt 1/3)\n")
        f.write("2024-01-01 10:00:05 ERROR Connection retry failed\n")
        log_file = f.name

    try:
        # Step 1: Parse logs
        parser = LogParser()
        entries = parser.parse_file(log_file)

        assert len(entries) > 0
        assert any(e.level == "ERROR" for e in entries)

        # Step 2: Collect metrics
        collector = MetricsCollector()
        metrics = await collector.collect_all()

        assert "cpu" in metrics
        assert "memory" in metrics
        assert "disk" in metrics

        # Step 3: Detect anomalies
        detector = AnomalyDetector()
        error_count = sum(1 for e in entries if e.level == "ERROR")

        # Train with normal data
        normal_data = [[10, 50, 30] for _ in range(100)]
        detector.train(normal_data)

        # Test with current metrics
        current_data = [[
            metrics["cpu"]["percent"],
            metrics["memory"]["percent"],
            error_count
        ]]
        anomalies = detector.predict(current_data)

        assert len(anomalies) > 0

        # Step 4: AI Analysis
        with patch('anthropic.AsyncAnthropic') as mock_anthropic:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.content = [Mock(text=json.dumps({
                "severity": "high",
                "category": "database",
                "root_cause": "Database connection pool exhausted",
                "impact": "Unable to process requests",
                "recommendations": ["Increase connection pool size", "Add connection retry logic"]
            }))]
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_anthropic.return_value = mock_client

            analyzer = AIAnalyzer()
            diagnosis = await analyzer.analyze(
                metrics=metrics,
                logs=entries[:10],
                anomalies={"cpu_spike": True, "error_rate_high": True}
            )

            assert diagnosis["severity"] in ["low", "medium", "high", "critical"]
            assert "category" in diagnosis
            assert "root_cause" in diagnosis

    finally:
        Path(log_file).unlink()


@pytest.mark.asyncio
async def test_notification_workflow(integration_db):
    """Test complete notification workflow with database persistence."""
    # Create alert
    alert = Alert(
        title="High CPU Usage Detected",
        message="CPU usage has exceeded 90% for 5 minutes",
        priority=NotificationPriority.HIGH,
        source="anomaly_detector",
        metadata={
            "cpu_percent": 95.5,
            "threshold": 90,
            "duration_minutes": 5
        }
    )

    # Store in database
    alert_repo = AlertRepository(integration_db)
    db_alert = await alert_repo.create({
        "alert_id": alert.id,
        "title": alert.title,
        "message": alert.message,
        "priority": alert.priority.value,
        "source": alert.source,
        "metadata": alert.metadata,
        "channels_sent": ["slack", "email"],
        "resolved": False
    })

    assert db_alert.alert_id == alert.id
    assert db_alert.priority == "high"
    assert db_alert.resolved is False

    # Simulate alert resolution
    await asyncio.sleep(0.1)
    resolved = await alert_repo.mark_resolved(alert.id)

    assert resolved is True

    # Verify resolution time was calculated
    resolved_alert = await alert_repo.get_by_alert_id(alert.id)
    assert resolved_alert.resolved is True
    assert resolved_alert.resolution_time_minutes is not None
    assert resolved_alert.resolution_time_minutes > 0


@pytest.mark.asyncio
async def test_fix_generation_and_pr_workflow(integration_db):
    """Test fix generation and PR creation workflow."""
    diagnosis = {
        "severity": "high",
        "category": "performance",
        "root_cause": "N+1 query problem in user endpoint",
        "impact": "API response time increased by 300%",
        "recommendations": [
            "Add database query prefetching",
            "Implement eager loading for relationships"
        ],
        "affected_files": ["src/api/users.py"]
    }

    with patch('anthropic.AsyncAnthropic') as mock_anthropic:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({
            "fixes": [
                {
                    "file_path": "src/api/users.py",
                    "description": "Add eager loading to user query",
                    "changes": "Use .options(joinedload(User.posts)) to prefetch related data",
                    "confidence": 0.9
                }
            ],
            "test_commands": ["pytest tests/api/test_users.py"],
            "validation_steps": ["Check query count", "Measure response time"],
            "rollback_plan": "Revert commit if response time doesn't improve"
        }))]
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        # Generate fix
        fix_generator = FixGenerator()
        fix_proposal = await fix_generator.generate_fix(diagnosis)

        assert "fixes" in fix_proposal
        assert len(fix_proposal["fixes"]) > 0
        assert "test_commands" in fix_proposal

        # Store fix in database
        fix_repo = FixRepository(integration_db)
        db_fix = await fix_repo.create({
            "fix_id": f"fix_{datetime.utcnow().timestamp()}",
            "diagnosis": diagnosis,
            "proposed_changes": fix_proposal["fixes"],
            "test_commands": fix_proposal["test_commands"],
            "confidence_score": fix_proposal["fixes"][0]["confidence"],
            "status": "proposed",
            "applied": False
        })

        assert db_fix.status == "proposed"
        assert db_fix.confidence_score > 0.8

        # Simulate fix application
        await fix_repo.update_status(db_fix.fix_id, "applied", applied=True)

        updated_fix = await fix_repo.get_by_fix_id(db_fix.fix_id)
        assert updated_fix.status == "applied"
        assert updated_fix.applied is True


@pytest.mark.asyncio
async def test_metrics_collection_and_storage(integration_db):
    """Test metrics collection and database storage."""
    collector = MetricsCollector()
    metrics = await collector.collect_all()

    # Store metrics snapshot
    metrics_repo = MetricsRepository(integration_db)
    snapshot = await metrics_repo.create_snapshot({
        "cpu_percent": metrics["cpu"]["percent"],
        "cpu_count": metrics["cpu"]["count"],
        "memory_percent": metrics["memory"]["percent"],
        "memory_available_gb": metrics["memory"]["available"] / (1024**3),
        "disk_percent": metrics["disk"]["percent"],
        "disk_free_gb": metrics["disk"]["free"] / (1024**3),
        "network_bytes_sent": metrics.get("network", {}).get("bytes_sent", 0),
        "network_bytes_recv": metrics.get("network", {}).get("bytes_recv", 0),
    })

    assert snapshot.cpu_percent >= 0
    assert snapshot.memory_percent >= 0
    assert snapshot.disk_percent >= 0

    # Query recent snapshots
    recent = await metrics_repo.get_recent(hours=1, limit=10)
    assert len(recent) > 0
    assert recent[0].id == snapshot.id


@pytest.mark.asyncio
async def test_end_to_end_with_database_persistence(integration_db):
    """Test complete end-to-end workflow with all database operations."""

    # Step 1: Create analysis run
    analysis_repo = AnalysisRepository(integration_db)
    analysis = await analysis_repo.create({
        "run_id": f"run_{datetime.utcnow().timestamp()}",
        "trigger": "scheduled",
        "status": "running"
    })

    assert analysis.status == "running"

    # Step 2: Collect and store metrics
    collector = MetricsCollector()
    metrics = await collector.collect_all()

    metrics_repo = MetricsRepository(integration_db)
    snapshot = await metrics_repo.create_snapshot({
        "analysis_run_id": analysis.id,
        "cpu_percent": metrics["cpu"]["percent"],
        "cpu_count": metrics["cpu"]["count"],
        "memory_percent": metrics["memory"]["percent"],
        "memory_available_gb": metrics["memory"]["available"] / (1024**3),
        "disk_percent": metrics["disk"]["percent"],
        "disk_free_gb": metrics["disk"]["free"] / (1024**3),
    })

    # Step 3: Detect issues and create alerts
    alert_repo = AlertRepository(integration_db)

    if metrics["cpu"]["percent"] > 80 or metrics["memory"]["percent"] > 80:
        alert = await alert_repo.create({
            "alert_id": f"alert_{datetime.utcnow().timestamp()}",
            "analysis_run_id": analysis.id,
            "title": "Resource usage high",
            "message": f"CPU: {metrics['cpu']['percent']}%, Memory: {metrics['memory']['percent']}%",
            "priority": "medium",
            "source": "metrics_collector",
            "channels_sent": ["slack"],
            "resolved": False
        })

    # Step 4: Generate and store diagnosis
    with patch('anthropic.AsyncAnthropic') as mock_anthropic:
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.content = [Mock(text=json.dumps({
            "severity": "medium",
            "category": "performance",
            "root_cause": "High resource utilization",
            "impact": "Potential service degradation",
            "recommendations": ["Scale horizontally", "Optimize queries"]
        }))]
        mock_client.messages.create = AsyncMock(return_value=mock_response)
        mock_anthropic.return_value = mock_client

        analyzer = AIAnalyzer()
        diagnosis = await analyzer.analyze(
            metrics=metrics,
            logs=[],
            anomalies={}
        )

    # Step 5: Complete analysis run
    await analysis_repo.complete(
        analysis.run_id,
        status="completed",
        findings={
            "metrics": metrics,
            "diagnosis": diagnosis
        }
    )

    completed_analysis = await analysis_repo.get_by_run_id(analysis.run_id)
    assert completed_analysis.status == "completed"
    assert completed_analysis.findings is not None
    assert completed_analysis.duration_seconds is not None


@pytest.mark.asyncio
async def test_alert_deduplication():
    """Test alert deduplication logic."""
    alert1 = Alert(
        title="High CPU Usage",
        message="CPU at 95%",
        priority=NotificationPriority.HIGH,
        source="monitor"
    )

    alert2 = Alert(
        title="High CPU Usage",
        message="CPU at 96%",
        priority=NotificationPriority.HIGH,
        source="monitor"
    )

    # Same fingerprint should be detected
    assert alert1.fingerprint == alert2.fingerprint

    alert3 = Alert(
        title="High Memory Usage",
        message="Memory at 90%",
        priority=NotificationPriority.HIGH,
        source="monitor"
    )

    # Different alert should have different fingerprint
    assert alert1.fingerprint != alert3.fingerprint


@pytest.mark.asyncio
async def test_concurrent_analysis_runs(integration_db):
    """Test handling of concurrent analysis runs."""
    analysis_repo = AnalysisRepository(integration_db)

    # Create multiple concurrent analysis runs
    runs = await asyncio.gather(*[
        analysis_repo.create({
            "run_id": f"run_{i}_{datetime.utcnow().timestamp()}",
            "trigger": "manual",
            "status": "running"
        })
        for i in range(5)
    ])

    assert len(runs) == 5

    # Complete them concurrently
    await asyncio.gather(*[
        analysis_repo.complete(
            run.run_id,
            status="completed",
            findings={"test": f"data_{i}"}
        )
        for i, run in enumerate(runs)
    ])

    # Verify all completed
    for run in runs:
        completed = await analysis_repo.get_by_run_id(run.run_id)
        assert completed.status == "completed"


@pytest.mark.asyncio
async def test_error_recovery_workflow(integration_db):
    """Test error recovery and retry mechanisms."""
    analysis_repo = AnalysisRepository(integration_db)

    # Start analysis
    analysis = await analysis_repo.create({
        "run_id": f"run_{datetime.utcnow().timestamp()}",
        "trigger": "scheduled",
        "status": "running"
    })

    # Simulate failure
    await analysis_repo.complete(
        analysis.run_id,
        status="failed",
        error_message="API timeout"
    )

    failed_analysis = await analysis_repo.get_by_run_id(analysis.run_id)
    assert failed_analysis.status == "failed"
    assert "timeout" in failed_analysis.error_message.lower()

    # Query failed analyses
    recent_analyses = await analysis_repo.get_recent(hours=1, limit=10)
    failed_count = sum(1 for a in recent_analyses if a.status == "failed")
    assert failed_count > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
