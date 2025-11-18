"""Data retention and cleanup policies."""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json
from pathlib import Path

from sqlalchemy import delete, select, func
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


class DataRetentionManager:
    """Manages data retention policies and cleanup operations."""

    # Default retention periods (days)
    DEFAULT_RETENTION = {
        "metrics_snapshots": 30,
        "alert_history": 90,
        "analysis_runs": 60,
        "diagnosis_history": 90,
        "fix_history": 180,
        "pr_history": 365,
        "system_health_scores": 90,
        "issue_recurrences": 365,
    }

    def __init__(self, session: AsyncSession):
        self.session = session

    async def cleanup_old_data(
        self, table_name: str, retention_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Clean up old data from specified table.

        Args:
            table_name: Name of table to clean
            retention_days: Days to retain (uses default if not specified)

        Returns:
            Cleanup statistics
        """
        start_time = datetime.utcnow()

        # Get retention period
        retention = retention_days or self.DEFAULT_RETENTION.get(table_name, 30)
        cutoff_date = datetime.utcnow() - timedelta(days=retention)

        # Map table names to models
        table_models = {
            "metrics_snapshots": MetricsSnapshot,
            "alert_history": AlertHistory,
            "analysis_runs": AnalysisRun,
            "diagnosis_history": DiagnosisHistory,
            "fix_history": FixHistory,
            "pr_history": PRHistory,
            "system_health_scores": SystemHealthScore,
        }

        model = table_models.get(table_name)
        if not model:
            raise ValueError(f"Unknown table: {table_name}")

        try:
            # Count records to be deleted
            count_result = await self.session.execute(
                select(func.count(model.id)).where(model.timestamp < cutoff_date)
            )
            records_to_delete = count_result.scalar()

            # Delete old records
            await self.session.execute(
                delete(model).where(model.timestamp < cutoff_date)
            )

            await self.session.commit()

            # Log the operation
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._log_retention_operation(
                operation_type="cleanup",
                table_name=table_name,
                records_deleted=records_to_delete,
                retention_days=retention,
                duration_seconds=duration,
                success=True,
            )

            return {
                "table": table_name,
                "retention_days": retention,
                "cutoff_date": cutoff_date.isoformat(),
                "records_deleted": records_to_delete,
                "duration_seconds": round(duration, 2),
                "success": True,
            }

        except Exception as e:
            await self.session.rollback()

            # Log the failure
            await self._log_retention_operation(
                operation_type="cleanup",
                table_name=table_name,
                retention_days=retention,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                success=False,
                error_message=str(e),
            )

            return {
                "table": table_name,
                "success": False,
                "error": str(e),
            }

    async def cleanup_all_tables(
        self, custom_retention: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """
        Clean up all tables according to retention policies.

        Args:
            custom_retention: Optional custom retention periods

        Returns:
            Comprehensive cleanup results
        """
        retention_config = {**self.DEFAULT_RETENTION}
        if custom_retention:
            retention_config.update(custom_retention)

        results = {}
        total_deleted = 0

        for table_name, retention_days in retention_config.items():
            result = await self.cleanup_old_data(table_name, retention_days)
            results[table_name] = result

            if result.get("success"):
                total_deleted += result.get("records_deleted", 0)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_records_deleted": total_deleted,
            "tables_cleaned": len([r for r in results.values() if r.get("success")]),
            "results": results,
        }

    async def archive_old_data(
        self,
        table_name: str,
        archive_path: str,
        retention_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Archive old data to JSON file before deletion.

        Args:
            table_name: Table to archive
            archive_path: Path to save archive file
            retention_days: Days to retain

        Returns:
            Archive statistics
        """
        start_time = datetime.utcnow()

        retention = retention_days or self.DEFAULT_RETENTION.get(table_name, 30)
        cutoff_date = datetime.utcnow() - timedelta(days=retention)

        table_models = {
            "metrics_snapshots": MetricsSnapshot,
            "alert_history": AlertHistory,
            "analysis_runs": AnalysisRun,
            "diagnosis_history": DiagnosisHistory,
            "fix_history": FixHistory,
        }

        model = table_models.get(table_name)
        if not model:
            raise ValueError(f"Unknown table: {table_name}")

        try:
            # Fetch old records
            result = await self.session.execute(
                select(model).where(model.timestamp < cutoff_date)
            )
            old_records = result.scalars().all()

            records_count = len(old_records)

            # Convert to JSON-serializable format
            archive_data = {
                "table": table_name,
                "archived_at": datetime.utcnow().isoformat(),
                "cutoff_date": cutoff_date.isoformat(),
                "retention_days": retention,
                "record_count": records_count,
                "records": [self._serialize_record(record) for record in old_records],
            }

            # Save to file
            archive_file = Path(archive_path)
            archive_file.parent.mkdir(parents=True, exist_ok=True)

            with open(archive_file, "w") as f:
                json.dump(archive_data, f, indent=2, default=str)

            # Now delete the archived records
            await self.session.execute(
                delete(model).where(model.timestamp < cutoff_date)
            )

            await self.session.commit()

            # Log the operation
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._log_retention_operation(
                operation_type="archive",
                table_name=table_name,
                records_affected=records_count,
                records_deleted=records_count,
                records_archived=records_count,
                retention_days=retention,
                archive_path=str(archive_file),
                duration_seconds=duration,
                success=True,
            )

            return {
                "table": table_name,
                "records_archived": records_count,
                "archive_file": str(archive_file),
                "archive_size_mb": round(archive_file.stat().st_size / (1024 * 1024), 2),
                "duration_seconds": round(duration, 2),
                "success": True,
            }

        except Exception as e:
            await self.session.rollback()

            await self._log_retention_operation(
                operation_type="archive",
                table_name=table_name,
                retention_days=retention,
                duration_seconds=(datetime.utcnow() - start_time).total_seconds(),
                success=False,
                error_message=str(e),
            )

            return {
                "table": table_name,
                "success": False,
                "error": str(e),
            }

    async def export_data(
        self,
        table_name: str,
        export_path: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Export data to JSON file for a specific date range.

        Args:
            table_name: Table to export
            export_path: Path to save export file
            start_date: Start of date range
            end_date: End of date range

        Returns:
            Export statistics
        """
        start_time = datetime.utcnow()

        table_models = {
            "metrics_snapshots": MetricsSnapshot,
            "alert_history": AlertHistory,
            "analysis_runs": AnalysisRun,
            "diagnosis_history": DiagnosisHistory,
            "fix_history": FixHistory,
        }

        model = table_models.get(table_name)
        if not model:
            raise ValueError(f"Unknown table: {table_name}")

        try:
            # Build query with date filters
            query = select(model)

            if start_date:
                query = query.where(model.timestamp >= start_date)
            if end_date:
                query = query.where(model.timestamp <= end_date)

            result = await self.session.execute(query)
            records = result.scalars().all()

            records_count = len(records)

            # Convert to JSON
            export_data = {
                "table": table_name,
                "exported_at": datetime.utcnow().isoformat(),
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
                "record_count": records_count,
                "records": [self._serialize_record(record) for record in records],
            }

            # Save to file
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            with open(export_file, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

            # Log the operation
            duration = (datetime.utcnow() - start_time).total_seconds()
            await self._log_retention_operation(
                operation_type="export",
                table_name=table_name,
                records_affected=records_count,
                archive_path=str(export_file),
                duration_seconds=duration,
                success=True,
            )

            return {
                "table": table_name,
                "records_exported": records_count,
                "export_file": str(export_file),
                "export_size_mb": round(export_file.stat().st_size / (1024 * 1024), 2),
                "duration_seconds": round(duration, 2),
                "success": True,
            }

        except Exception as e:
            return {
                "table": table_name,
                "success": False,
                "error": str(e),
            }

    def _serialize_record(self, record: Any) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dict for JSON serialization."""
        data = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            if isinstance(value, datetime):
                data[column.name] = value.isoformat()
            else:
                data[column.name] = value
        return data

    async def _log_retention_operation(
        self,
        operation_type: str,
        table_name: str,
        records_affected: int = 0,
        records_deleted: int = 0,
        records_archived: int = 0,
        retention_days: Optional[int] = None,
        archive_path: Optional[str] = None,
        duration_seconds: float = 0,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> None:
        """Log retention operation to database."""
        log_entry = DataRetentionLog(
            operation_type=operation_type,
            table_name=table_name,
            records_affected=records_affected,
            records_deleted=records_deleted,
            records_archived=records_archived,
            retention_days=retention_days,
            archive_path=archive_path,
            duration_seconds=duration_seconds,
            success=success,
            error_message=error_message,
        )

        self.session.add(log_entry)
        await self.session.flush()

    async def get_retention_logs(self, limit: int = 100) -> list:
        """Get recent retention operation logs."""
        from sqlalchemy import desc

        result = await self.session.execute(
            select(DataRetentionLog)
            .order_by(desc(DataRetentionLog.timestamp))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_database_size_stats(self) -> Dict[str, Any]:
        """Get statistics about database size and record counts."""
        table_models = {
            "metrics_snapshots": MetricsSnapshot,
            "alert_history": AlertHistory,
            "analysis_runs": AnalysisRun,
            "diagnosis_history": DiagnosisHistory,
            "fix_history": FixHistory,
            "pr_history": PRHistory,
            "system_health_scores": SystemHealthScore,
            "issue_recurrences": IssueRecurrence,
        }

        stats = {}
        total_records = 0

        for table_name, model in table_models.items():
            result = await self.session.execute(select(func.count(model.id)))
            count = result.scalar()

            stats[table_name] = {
                "record_count": count,
                "retention_days": self.DEFAULT_RETENTION.get(table_name, 30),
            }
            total_records += count

        return {
            "total_records": total_records,
            "tables": stats,
            "timestamp": datetime.utcnow().isoformat(),
        }
