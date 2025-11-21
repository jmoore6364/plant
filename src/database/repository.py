"""Repository layer for database operations."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import (
    AnalysisRun,
    MetricsSnapshot,
    AlertHistory,
    DiagnosisHistory,
    FixHistory,
    PRHistory,
    SystemHealthScore,
    IssueRecurrence,
    DataRetentionLog,
)


class AnalysisRepository:
    """Repository for analysis run operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, analysis_data: Dict[str, Any]) -> AnalysisRun:
        """Create a new analysis run record."""
        # Auto-sync request_id and run_id for backwards compatibility
        if "request_id" in analysis_data and "run_id" not in analysis_data:
            analysis_data["run_id"] = analysis_data["request_id"]
        elif "run_id" in analysis_data and "request_id" not in analysis_data:
            analysis_data["request_id"] = analysis_data["run_id"]

        analysis = AnalysisRun(**analysis_data)
        self.session.add(analysis)
        await self.session.flush()
        return analysis

    async def get_by_id(self, analysis_id: int) -> Optional[AnalysisRun]:
        """Get analysis run by ID."""
        result = await self.session.execute(
            select(AnalysisRun).where(AnalysisRun.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def get_by_request_id(self, request_id: str) -> Optional[AnalysisRun]:
        """Get analysis run by request ID."""
        result = await self.session.execute(
            select(AnalysisRun).where(AnalysisRun.request_id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_by_run_id(self, run_id: str) -> Optional[AnalysisRun]:
        """Get analysis run by run ID."""
        result = await self.session.execute(
            select(AnalysisRun).where(AnalysisRun.run_id == run_id)
        )
        return result.scalar_one_or_none()

    async def complete(
        self,
        run_id: str,
        status: str = "completed",
        error_message: Optional[str] = None,
        **kwargs
    ) -> Optional[AnalysisRun]:
        """Mark an analysis run as complete with status and optional error message."""
        analysis = await self.get_by_run_id(run_id)
        if analysis:
            analysis.status = status
            if error_message:
                analysis.error_message = error_message

            # Update any additional fields passed
            for key, value in kwargs.items():
                if hasattr(analysis, key):
                    setattr(analysis, key, value)

            await self.session.flush()
        return analysis

    async def get_recent(self, limit: int = 100, hours: int = 24) -> List[AnalysisRun]:
        """Get recent analysis runs."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(AnalysisRun)
            .where(AnalysisRun.timestamp >= cutoff)
            .order_by(desc(AnalysisRun.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get analysis statistics."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = await self.session.execute(
            select(
                func.count(AnalysisRun.id).label("total_runs"),
                func.sum(AnalysisRun.logs_analyzed).label("total_logs"),
                func.sum(AnalysisRun.anomalies_found).label("total_anomalies"),
                func.sum(AnalysisRun.fixes_generated).label("total_fixes"),
                func.sum(AnalysisRun.prs_created).label("total_prs"),
                func.avg(AnalysisRun.processing_time_ms).label("avg_processing_time"),
            ).where(AnalysisRun.timestamp >= cutoff)
        )
        stats = result.one()

        return {
            "total_runs": stats.total_runs or 0,
            "total_logs": stats.total_logs or 0,
            "total_anomalies": stats.total_anomalies or 0,
            "total_fixes": stats.total_fixes or 0,
            "total_prs": stats.total_prs or 0,
            "avg_processing_time_ms": stats.avg_processing_time or 0,
        }


class MetricsRepository:
    """Repository for metrics snapshot operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, metrics_data: Dict[str, Any]) -> MetricsSnapshot:
        """Create a new metrics snapshot."""
        snapshot = MetricsSnapshot(**metrics_data)
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def create_snapshot(self, metrics_data: Dict[str, Any]) -> MetricsSnapshot:
        """
        Create a new metrics snapshot with field name normalization.

        Handles field name variations and conversions for backwards compatibility.
        """
        # Normalize field names and convert units
        normalized_data = {}

        # CPU fields
        if "cpu_percent" in metrics_data:
            normalized_data["cpu_percent"] = metrics_data["cpu_percent"]
        # cpu_count is not stored (just metadata)

        # Memory fields
        if "memory_percent" in metrics_data:
            normalized_data["memory_percent"] = metrics_data["memory_percent"]
        if "memory_available_gb" in metrics_data:
            # Convert GB to MB
            normalized_data["memory_available_mb"] = metrics_data["memory_available_gb"] * 1024
        elif "memory_available_mb" in metrics_data:
            normalized_data["memory_available_mb"] = metrics_data["memory_available_mb"]

        # Disk fields
        if "disk_percent" in metrics_data:
            normalized_data["disk_usage_percent"] = metrics_data["disk_percent"]
        elif "disk_usage_percent" in metrics_data:
            normalized_data["disk_usage_percent"] = metrics_data["disk_usage_percent"]
        if "disk_free_gb" in metrics_data:
            normalized_data["disk_free_gb"] = metrics_data["disk_free_gb"]

        # Network fields
        if "network_bytes_sent" in metrics_data:
            normalized_data["network_bytes_sent"] = metrics_data["network_bytes_sent"]
        if "network_bytes_recv" in metrics_data:
            normalized_data["network_bytes_recv"] = metrics_data["network_bytes_recv"]

        # Process count - default to 0 if not provided
        normalized_data["process_count"] = metrics_data.get("process_count", 0)

        # Load average if provided
        if "load_average" in metrics_data:
            normalized_data["load_average"] = metrics_data["load_average"]

        return await self.create(normalized_data)

    async def get_recent(self, limit: int = 1000, hours: int = 24) -> List[MetricsSnapshot]:
        """Get recent metrics snapshots."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(MetricsSnapshot)
            .where(MetricsSnapshot.timestamp >= cutoff)
            .order_by(desc(MetricsSnapshot.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_anomalies(self, hours: int = 24) -> List[MetricsSnapshot]:
        """Get snapshots with anomalies."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(MetricsSnapshot)
            .where(
                and_(
                    MetricsSnapshot.timestamp >= cutoff,
                    or_(
                        MetricsSnapshot.cpu_anomaly == True,
                        MetricsSnapshot.memory_anomaly == True,
                        MetricsSnapshot.disk_anomaly == True,
                    ),
                )
            )
            .order_by(desc(MetricsSnapshot.timestamp))
        )
        return list(result.scalars().all())

    async def get_averages(self, hours: int = 24) -> Dict[str, float]:
        """Get average metrics over time period."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = await self.session.execute(
            select(
                func.avg(MetricsSnapshot.cpu_percent).label("avg_cpu"),
                func.avg(MetricsSnapshot.memory_percent).label("avg_memory"),
                func.avg(MetricsSnapshot.disk_usage_percent).label("avg_disk"),
                func.max(MetricsSnapshot.cpu_percent).label("max_cpu"),
                func.max(MetricsSnapshot.memory_percent).label("max_memory"),
            ).where(MetricsSnapshot.timestamp >= cutoff)
        )
        stats = result.one()

        return {
            "avg_cpu_percent": stats.avg_cpu or 0,
            "avg_memory_percent": stats.avg_memory or 0,
            "avg_disk_percent": stats.avg_disk or 0,
            "max_cpu_percent": stats.max_cpu or 0,
            "max_memory_percent": stats.max_memory or 0,
        }


class AlertRepository:
    """Repository for alert history operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, alert_data: Dict[str, Any]) -> AlertHistory:
        """Create a new alert record."""
        alert = AlertHistory(**alert_data)
        self.session.add(alert)
        await self.session.flush()
        return alert

    async def get_by_id(self, alert_id: str) -> Optional[AlertHistory]:
        """Get alert by ID."""
        result = await self.session.execute(
            select(AlertHistory).where(AlertHistory.alert_id == alert_id)
        )
        return result.scalar_one_or_none()

    async def get_by_alert_id(self, alert_id: str) -> Optional[AlertHistory]:
        """Get alert by alert_id (alias for get_by_id)."""
        return await self.get_by_id(alert_id)

    async def get_recent(
        self, limit: int = 100, hours: int = 24, priority: Optional[str] = None
    ) -> List[AlertHistory]:
        """Get recent alerts, optionally filtered by priority."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        query = select(AlertHistory).where(AlertHistory.timestamp >= cutoff)

        if priority:
            query = query.where(AlertHistory.priority == priority)

        query = query.order_by(desc(AlertHistory.timestamp)).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unresolved(self) -> List[AlertHistory]:
        """Get all unresolved alerts."""
        result = await self.session.execute(
            select(AlertHistory)
            .where(AlertHistory.resolved == False)
            .order_by(desc(AlertHistory.timestamp))
        )
        return list(result.scalars().all())

    async def mark_resolved(self, alert_id: str) -> bool:
        """Mark an alert as resolved."""
        alert = await self.get_by_id(alert_id)
        if alert and not alert.resolved:
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()

            # Calculate resolution time
            if alert.timestamp:
                delta = alert.resolved_at - alert.timestamp
                alert.resolution_time_minutes = delta.total_seconds() / 60

            await self.session.flush()
            return True
        return False

    async def get_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        # Count by priority
        priority_result = await self.session.execute(
            select(
                AlertHistory.priority,
                func.count(AlertHistory.id).label("count"),
            )
            .where(AlertHistory.timestamp >= cutoff)
            .group_by(AlertHistory.priority)
        )

        priority_counts = {row.priority: row.count for row in priority_result}

        # Overall stats
        stats_result = await self.session.execute(
            select(
                func.count(AlertHistory.id).label("total"),
                func.count(AlertHistory.id).filter(AlertHistory.resolved == True).label("resolved"),
                func.avg(AlertHistory.resolution_time_minutes).label("avg_resolution_time"),
            ).where(AlertHistory.timestamp >= cutoff)
        )
        stats = stats_result.one()

        return {
            "total_alerts": stats.total or 0,
            "resolved_alerts": stats.resolved or 0,
            "unresolved_alerts": (stats.total or 0) - (stats.resolved or 0),
            "avg_resolution_time_minutes": stats.avg_resolution_time or 0,
            "by_priority": priority_counts,
        }


class DiagnosisRepository:
    """Repository for diagnosis history operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, diagnosis_data: Dict[str, Any]) -> DiagnosisHistory:
        """Create a new diagnosis record."""
        diagnosis = DiagnosisHistory(**diagnosis_data)
        self.session.add(diagnosis)
        await self.session.flush()
        return diagnosis

    async def get_recent(self, limit: int = 100, hours: int = 24) -> List[DiagnosisHistory]:
        """Get recent diagnoses."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(DiagnosisHistory)
            .where(DiagnosisHistory.timestamp >= cutoff)
            .order_by(desc(DiagnosisHistory.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_category(self, category: str, limit: int = 50) -> List[DiagnosisHistory]:
        """Get diagnoses by category."""
        result = await self.session.execute(
            select(DiagnosisHistory)
            .where(DiagnosisHistory.category == category)
            .order_by(desc(DiagnosisHistory.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def find_similar(
        self, summary: str, category: str, limit: int = 10
    ) -> List[DiagnosisHistory]:
        """Find similar past diagnoses (simple keyword matching)."""
        # This is a simple implementation - could be enhanced with vector similarity
        keywords = summary.lower().split()[:5]  # First 5 words

        result = await self.session.execute(
            select(DiagnosisHistory)
            .where(DiagnosisHistory.category == category)
            .order_by(desc(DiagnosisHistory.timestamp))
            .limit(limit * 2)  # Get more for filtering
        )

        diagnoses = list(result.scalars().all())

        # Simple keyword matching
        scored = []
        for diagnosis in diagnoses:
            score = sum(
                1 for keyword in keywords if keyword in diagnosis.summary.lower()
            )
            if score > 0:
                scored.append((diagnosis, score))

        # Sort by score and return top results
        scored.sort(key=lambda x: x[1], reverse=True)
        return [d for d, _ in scored[:limit]]


class FixRepository:
    """Repository for fix history operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, fix_data: Dict[str, Any]) -> FixHistory:
        """Create a new fix record."""
        fix = FixHistory(**fix_data)
        self.session.add(fix)
        await self.session.flush()
        return fix

    async def get_recent(self, limit: int = 100) -> List[FixHistory]:
        """Get recent fixes."""
        result = await self.session.execute(
            select(FixHistory)
            .order_by(desc(FixHistory.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_success_rate(self, hours: int = 168) -> Dict[str, Any]:
        """Get fix success rate over period."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        result = await self.session.execute(
            select(
                func.count(FixHistory.id).label("total"),
                func.count(FixHistory.id).filter(FixHistory.validation_passed == True).label("validated"),
                func.count(FixHistory.id).filter(FixHistory.applied == True).label("applied"),
                func.count(FixHistory.id).filter(FixHistory.issue_recurred == False).label("successful"),
            ).where(FixHistory.timestamp >= cutoff)
        )
        stats = result.one()

        total = stats.total or 0
        return {
            "total_fixes": total,
            "validation_rate": (stats.validated / total * 100) if total > 0 else 0,
            "application_rate": (stats.applied / total * 100) if total > 0 else 0,
            "success_rate": (stats.successful / total * 100) if total > 0 else 0,
        }


class IssueRecurrenceRepository:
    """Repository for issue recurrence tracking."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def record_occurrence(
        self, fingerprint: str, title: str, category: Optional[str] = None
    ) -> IssueRecurrence:
        """Record an issue occurrence (creates new or updates existing)."""
        # Try to find existing recurrence record
        result = await self.session.execute(
            select(IssueRecurrence).where(IssueRecurrence.issue_fingerprint == fingerprint)
        )
        recurrence = result.scalar_one_or_none()

        now = datetime.utcnow()

        if recurrence:
            # Update existing record
            time_since_last = (now - recurrence.last_occurrence).total_seconds() / 3600  # hours
            recurrence.last_occurrence = now
            recurrence.occurrence_count += 1

            # Update average interval
            if recurrence.occurrence_count > 1:
                total_hours = (now - recurrence.first_occurrence).total_seconds() / 3600
                recurrence.average_interval_hours = total_hours / (recurrence.occurrence_count - 1)

            # Check if periodic (similar intervals)
            if recurrence.average_interval_hours:
                deviation = abs(time_since_last - recurrence.average_interval_hours)
                recurrence.is_periodic = (
                    deviation / recurrence.average_interval_hours < 0.3
                )  # Within 30%

        else:
            # Create new record
            recurrence = IssueRecurrence(
                issue_fingerprint=fingerprint,
                issue_title=title,
                issue_category=category,
                first_occurrence=now,
                last_occurrence=now,
                occurrence_count=1,
            )
            self.session.add(recurrence)

        await self.session.flush()
        return recurrence

    async def get_recurring_issues(self, min_occurrences: int = 3) -> List[IssueRecurrence]:
        """Get issues that have recurred multiple times."""
        result = await self.session.execute(
            select(IssueRecurrence)
            .where(IssueRecurrence.occurrence_count >= min_occurrences)
            .order_by(desc(IssueRecurrence.occurrence_count))
        )
        return list(result.scalars().all())

    async def get_periodic_issues(self) -> List[IssueRecurrence]:
        """Get issues with periodic recurrence."""
        result = await self.session.execute(
            select(IssueRecurrence)
            .where(IssueRecurrence.is_periodic == True)
            .order_by(desc(IssueRecurrence.occurrence_count))
        )
        return list(result.scalars().all())
