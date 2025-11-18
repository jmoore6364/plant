"""API routes for database and historical data."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime, timedelta

from src.database.connection import get_db
from src.database.repository import (
    AnalysisRepository,
    MetricsRepository,
    AlertRepository,
    DiagnosisRepository,
    FixRepository,
    IssueRecurrenceRepository,
)
from src.database.analytics import AnalyticsEngine
from src.database.retention import DataRetentionManager

router = APIRouter(prefix="/history", tags=["history"])


# Analysis History
@router.get("/analyses")
async def get_analysis_history(
    limit: int = Query(100, le=1000),
    hours: int = Query(24, le=720),
    db: AsyncSession = Depends(get_db),
):
    """Get analysis run history."""
    repo = AnalysisRepository(db)
    analyses = await repo.get_recent(limit=limit, hours=hours)

    return {
        "count": len(analyses),
        "analyses": [
            {
                "id": a.id,
                "request_id": a.request_id,
                "timestamp": a.timestamp.isoformat(),
                "logs_analyzed": a.logs_analyzed,
                "anomalies_found": a.anomalies_found,
                "diagnoses_generated": a.diagnoses_generated,
                "fixes_generated": a.fixes_generated,
                "processing_time_ms": a.processing_time_ms,
                "success": a.success,
            }
            for a in analyses
        ],
    }


@router.get("/analyses/stats")
async def get_analysis_stats(
    hours: int = Query(24, le=720),
    db: AsyncSession = Depends(get_db),
):
    """Get analysis statistics."""
    repo = AnalysisRepository(db)
    stats = await repo.get_stats(hours=hours)

    return {
        "time_window_hours": hours,
        **stats,
    }


# Metrics History
@router.get("/metrics")
async def get_metrics_history(
    limit: int = Query(1000, le=10000),
    hours: int = Query(24, le=720),
    db: AsyncSession = Depends(get_db),
):
    """Get metrics snapshot history."""
    repo = MetricsRepository(db)
    snapshots = await repo.get_recent(limit=limit, hours=hours)

    return {
        "count": len(snapshots),
        "snapshots": [
            {
                "id": m.id,
                "timestamp": m.timestamp.isoformat(),
                "cpu_percent": m.cpu_percent,
                "memory_percent": m.memory_percent,
                "disk_usage_percent": m.disk_usage_percent,
                "process_count": m.process_count,
            }
            for m in snapshots
        ],
    }


@router.get("/metrics/averages")
async def get_metrics_averages(
    hours: int = Query(24, le=720),
    db: AsyncSession = Depends(get_db),
):
    """Get average metrics over time period."""
    repo = MetricsRepository(db)
    averages = await repo.get_averages(hours=hours)

    return {
        "time_window_hours": hours,
        **averages,
    }


@router.get("/metrics/anomalies")
async def get_metric_anomalies(
    hours: int = Query(24, le=720),
    db: AsyncSession = Depends(get_db),
):
    """Get metrics snapshots with detected anomalies."""
    repo = MetricsRepository(db)
    anomalies = await repo.get_anomalies(hours=hours)

    return {
        "count": len(anomalies),
        "anomalies": [
            {
                "timestamp": a.timestamp.isoformat(),
                "cpu_anomaly": a.cpu_anomaly,
                "memory_anomaly": a.memory_anomaly,
                "disk_anomaly": a.disk_anomaly,
                "cpu_percent": a.cpu_percent,
                "memory_percent": a.memory_percent,
                "disk_usage_percent": a.disk_usage_percent,
            }
            for a in anomalies
        ],
    }


# Alert History
@router.get("/alerts")
async def get_alert_history(
    limit: int = Query(100, le=1000),
    hours: int = Query(24, le=720),
    priority: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get alert history."""
    repo = AlertRepository(db)
    alerts = await repo.get_recent(limit=limit, hours=hours, priority=priority)

    return {
        "count": len(alerts),
        "alerts": [
            {
                "alert_id": a.alert_id,
                "timestamp": a.timestamp.isoformat(),
                "title": a.title,
                "message": a.message,
                "priority": a.priority,
                "source": a.source,
                "resolved": a.resolved,
                "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
                "resolution_time_minutes": a.resolution_time_minutes,
                "tags": a.tags,
            }
            for a in alerts
        ],
    }


@router.get("/alerts/stats")
async def get_alert_stats(
    hours: int = Query(24, le=720),
    db: AsyncSession = Depends(get_db),
):
    """Get alert statistics."""
    repo = AlertRepository(db)
    stats = await repo.get_stats(hours=hours)

    return {
        "time_window_hours": hours,
        **stats,
    }


@router.get("/alerts/unresolved")
async def get_unresolved_alerts(db: AsyncSession = Depends(get_db)):
    """Get all unresolved alerts."""
    repo = AlertRepository(db)
    alerts = await repo.get_unresolved()

    return {
        "count": len(alerts),
        "alerts": [
            {
                "alert_id": a.alert_id,
                "timestamp": a.timestamp.isoformat(),
                "title": a.title,
                "priority": a.priority,
                "source": a.source,
                "age_hours": (datetime.utcnow() - a.timestamp).total_seconds() / 3600,
            }
            for a in alerts
        ],
    }


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Mark an alert as resolved."""
    repo = AlertRepository(db)
    success = await repo.mark_resolved(alert_id)

    if not success:
        raise HTTPException(status_code=404, detail="Alert not found or already resolved")

    await db.commit()

    return {"alert_id": alert_id, "resolved": True}


# Diagnoses History
@router.get("/diagnoses")
async def get_diagnosis_history(
    limit: int = Query(100, le=1000),
    hours: int = Query(24, le=720),
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get diagnosis history."""
    repo = DiagnosisRepository(db)

    if category:
        diagnoses = await repo.get_by_category(category, limit=limit)
    else:
        diagnoses = await repo.get_recent(limit=limit, hours=hours)

    return {
        "count": len(diagnoses),
        "diagnoses": [
            {
                "diagnosis_id": d.diagnosis_id,
                "timestamp": d.timestamp.isoformat(),
                "summary": d.summary,
                "severity": d.severity,
                "category": d.category,
                "confidence": d.confidence,
                "fix_applied": d.fix_applied,
            }
            for d in diagnoses
        ],
    }


@router.get("/diagnoses/{diagnosis_id}/similar")
async def find_similar_diagnoses(
    diagnosis_id: str,
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Find similar past diagnoses."""
    repo = DiagnosisRepository(db)

    # First get the diagnosis
    result = await db.execute(
        f"SELECT * FROM diagnosis_history WHERE diagnosis_id = '{diagnosis_id}'"
    )
    diagnosis = result.fetchone()

    if not diagnosis:
        raise HTTPException(status_code=404, detail="Diagnosis not found")

    # Find similar
    similar = await repo.find_similar(
        summary=diagnosis.summary,
        category=diagnosis.category,
        limit=limit,
    )

    return {
        "original_diagnosis_id": diagnosis_id,
        "similar_count": len(similar),
        "similar_diagnoses": [
            {
                "diagnosis_id": d.diagnosis_id,
                "timestamp": d.timestamp.isoformat(),
                "summary": d.summary,
                "severity": d.severity,
                "confidence": d.confidence,
            }
            for d in similar
        ],
    }


# Fix History
@router.get("/fixes")
async def get_fix_history(
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get fix generation history."""
    repo = FixRepository(db)
    fixes = await repo.get_recent(limit=limit)

    return {
        "count": len(fixes),
        "fixes": [
            {
                "fix_id": f.fix_id,
                "timestamp": f.timestamp.isoformat(),
                "title": f.title,
                "fix_type": f.fix_type,
                "validation_passed": f.validation_passed,
                "applied": f.applied,
                "applied_at": f.applied_at.isoformat() if f.applied_at else None,
            }
            for f in fixes
        ],
    }


@router.get("/fixes/effectiveness")
async def get_fix_effectiveness(
    hours: int = Query(168, le=720),  # Default 7 days
    db: AsyncSession = Depends(get_db),
):
    """Get fix effectiveness statistics."""
    repo = FixRepository(db)
    stats = await repo.get_success_rate(hours=hours)

    return {
        "time_window_hours": hours,
        **stats,
    }


# Recurring Issues
@router.get("/recurring-issues")
async def get_recurring_issues(
    min_occurrences: int = Query(3, ge=2, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get recurring issues."""
    repo = IssueRecurrenceRepository(db)
    issues = await repo.get_recurring_issues(min_occurrences=min_occurrences)

    return {
        "count": len(issues),
        "issues": [
            {
                "fingerprint": i.issue_fingerprint,
                "title": i.issue_title,
                "category": i.issue_category,
                "occurrence_count": i.occurrence_count,
                "first_seen": i.first_occurrence.isoformat(),
                "last_seen": i.last_occurrence.isoformat(),
                "average_interval_hours": i.average_interval_hours,
                "is_periodic": i.is_periodic,
            }
            for i in issues
        ],
    }


@router.get("/recurring-issues/periodic")
async def get_periodic_issues(db: AsyncSession = Depends(get_db)):
    """Get issues with periodic recurrence patterns."""
    repo = IssueRecurrenceRepository(db)
    issues = await repo.get_periodic_issues()

    return {
        "count": len(issues),
        "periodic_issues": [
            {
                "fingerprint": i.issue_fingerprint,
                "title": i.issue_title,
                "occurrence_count": i.occurrence_count,
                "average_interval_hours": i.average_interval_hours,
            }
            for i in issues
        ],
    }


# Analytics Endpoints
@router.get("/analytics/health-score")
async def get_health_score(db: AsyncSession = Depends(get_db)):
    """Get current system health score."""
    engine = AnalyticsEngine(db)
    score = await engine.get_system_health_score()
    await db.commit()

    return score


@router.get("/analytics/trends")
async def get_trend_analysis(
    metric: str = Query("cpu", regex="^(cpu|memory|disk)$"),
    hours: int = Query(24, le=720),
    db: AsyncSession = Depends(get_db),
):
    """Get trend analysis for a metric."""
    engine = AnalyticsEngine(db)
    trend = await engine.get_trend_analysis(metric=metric, hours=hours)

    return trend


@router.get("/analytics/mttr")
async def get_mttr_analysis(
    hours: int = Query(168, le=720),  # Default 7 days
    db: AsyncSession = Depends(get_db),
):
    """Get Mean Time To Resolution (MTTR) analysis."""
    engine = AnalyticsEngine(db)
    mttr = await engine.get_mttr_analysis(hours=hours)

    return mttr


@router.get("/analytics/report")
async def get_comprehensive_report(
    hours: int = Query(24, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Get comprehensive analytics report."""
    engine = AnalyticsEngine(db)
    report = await engine.get_comprehensive_report(hours=hours)
    await db.commit()

    return report


# Data Retention
@router.post("/retention/cleanup/{table_name}")
async def cleanup_table(
    table_name: str,
    retention_days: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
):
    """Clean up old data from specified table."""
    manager = DataRetentionManager(db)
    result = await manager.cleanup_old_data(table_name, retention_days)

    if result.get("success"):
        await db.commit()

    return result


@router.post("/retention/cleanup-all")
async def cleanup_all_tables(db: AsyncSession = Depends(get_db)):
    """Clean up all tables according to retention policies."""
    manager = DataRetentionManager(db)
    result = await manager.cleanup_all_tables()

    return result


@router.post("/retention/export/{table_name}")
async def export_table_data(
    table_name: str,
    export_path: str = Query(..., description="Path to save export file"),
    db: AsyncSession = Depends(get_db),
):
    """Export table data to JSON file."""
    manager = DataRetentionManager(db)
    result = await manager.export_data(table_name, export_path)

    return result


@router.get("/retention/stats")
async def get_database_stats(db: AsyncSession = Depends(get_db)):
    """Get database size and retention statistics."""
    manager = DataRetentionManager(db)
    stats = await manager.get_database_size_stats()

    return stats


@router.get("/retention/logs")
async def get_retention_logs(
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get retention operation logs."""
    manager = DataRetentionManager(db)
    logs = await manager.get_retention_logs(limit=limit)

    return {
        "count": len(logs),
        "logs": [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "operation_type": log.operation_type,
                "table_name": log.table_name,
                "records_deleted": log.records_deleted,
                "records_archived": log.records_archived,
                "success": log.success,
            }
            for log in logs
        ],
    }
