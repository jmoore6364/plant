"""
Background job queue using Celery.

Handles long-running tasks asynchronously.
"""

from celery import Celery, Task
from celery.schedules import crontab
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from src.config import get_config

logger = logging.getLogger(__name__)

# Initialize Celery
config = get_config()
celery_app = Celery(
    "system_health_analyzer",
    broker=config.cache.redis_url,
    backend=config.cache.redis_url
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3000,  # 50 minutes
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
)


class BaseTask(Task):
    """Base task with error handling."""

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Task {task_id} failed: {exc}")
        logger.error(f"Error info: {einfo}")

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(f"Task {task_id} completed successfully")

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(f"Task {task_id} retrying: {exc}")


@celery_app.task(base=BaseTask, bind=True, max_retries=3)
def run_system_analysis(self, trigger: str = "scheduled"):
    """Run complete system analysis."""
    try:
        logger.info(f"Starting system analysis (trigger: {trigger})")

        # Import here to avoid circular dependencies
        from src.core.metrics_collector import MetricsCollector
        from src.core.log_parser import LogParser
        from src.ai.analyzer import AIAnalyzer
        import asyncio

        async def analyze():
            # Collect metrics
            collector = MetricsCollector()
            metrics = await collector.collect_all()

            # Analyze with AI
            analyzer = AIAnalyzer()
            diagnosis = await analyzer.analyze(
                metrics=metrics,
                logs=[],
                anomalies={}
            )

            return {
                "metrics": metrics,
                "diagnosis": diagnosis,
                "timestamp": datetime.utcnow().isoformat()
            }

        # Run async analysis
        result = asyncio.run(analyze())

        logger.info("System analysis completed")
        return result

    except Exception as e:
        logger.error(f"System analysis failed: {e}")
        raise self.retry(exc=e, countdown=60)


@celery_app.task(base=BaseTask)
def cleanup_old_data(table_name: str, retention_days: int):
    """Clean up old data from database."""
    try:
        logger.info(f"Cleaning up {table_name} (retention: {retention_days} days)")

        from src.database.retention import DataRetentionManager
        from src.database.connection import get_db_session
        import asyncio

        async def cleanup():
            async with get_db_session() as session:
                manager = DataRetentionManager(session)
                deleted = await manager.cleanup_old_data(table_name, retention_days)
                return deleted

        deleted = asyncio.run(cleanup())

        logger.info(f"Cleaned up {deleted} records from {table_name}")
        return {"table": table_name, "deleted": deleted}

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise


@celery_app.task(base=BaseTask)
def send_notification(title: str, message: str, priority: str, channels: list):
    """Send notification through configured channels."""
    try:
        logger.info(f"Sending notification: {title}")

        from src.notifications.manager import NotificationManager
        from src.notifications.base import Alert, NotificationPriority
        import asyncio

        async def send():
            manager = NotificationManager()
            alert = Alert(
                title=title,
                message=message,
                priority=NotificationPriority[priority.upper()],
                source="task_queue"
            )

            results = await manager.send_alert(alert, channels=channels)
            return results

        results = asyncio.run(send())

        logger.info(f"Notification sent: {results}")
        return results

    except Exception as e:
        logger.error(f"Notification failed: {e}")
        raise


@celery_app.task(base=BaseTask, bind=True, max_retries=5)
def generate_and_apply_fix(self, diagnosis: Dict[str, Any]):
    """Generate and apply fix for diagnosis."""
    try:
        logger.info(f"Generating fix for diagnosis: {diagnosis.get('category')}")

        from src.ai.fix_generator import FixGenerator
        from src.github.pr_creator import PRCreator
        import asyncio

        async def create_fix():
            # Generate fix
            fix_generator = FixGenerator()
            fix_proposal = await fix_generator.generate_fix(diagnosis)

            # Create PR
            pr_creator = PRCreator()
            pr_url = await pr_creator.create_fix_pr(
                diagnosis=diagnosis,
                fix_proposal=fix_proposal
            )

            return {
                "fix": fix_proposal,
                "pr_url": pr_url
            }

        result = asyncio.run(create_fix())

        logger.info(f"Fix created and PR submitted: {result['pr_url']}")
        return result

    except Exception as e:
        logger.error(f"Fix generation failed: {e}")
        raise self.retry(exc=e, countdown=300)


@celery_app.task(base=BaseTask)
def export_historical_data(table_name: str, hours: int, format: str = "json"):
    """Export historical data."""
    try:
        logger.info(f"Exporting {table_name} data (last {hours} hours)")

        from src.database.retention import DataRetentionManager
        from src.database.connection import get_db_session
        import asyncio

        async def export():
            async with get_db_session() as session:
                manager = DataRetentionManager(session)
                export_path = await manager.export_data(table_name, hours, format)
                return export_path

        path = asyncio.run(export())

        logger.info(f"Data exported to: {path}")
        return {"table": table_name, "path": path}

    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise


# Periodic tasks (scheduled)
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Set up periodic tasks."""

    # Run system analysis every hour
    sender.add_periodic_task(
        3600.0,
        run_system_analysis.s(trigger="scheduled"),
        name="hourly-system-analysis"
    )

    # Clean up old data daily at 2 AM
    sender.add_periodic_task(
        crontab(hour=2, minute=0),
        cleanup_old_data.s("metrics_snapshots", 30),
        name="daily-metrics-cleanup"
    )

    sender.add_periodic_task(
        crontab(hour=2, minute=15),
        cleanup_old_data.s("alert_history", 90),
        name="daily-alerts-cleanup"
    )

    # Export weekly reports every Monday at 6 AM
    sender.add_periodic_task(
        crontab(day_of_week=1, hour=6, minute=0),
        export_historical_data.s("analyses", 168, "json"),
        name="weekly-analysis-export"
    )


# Task monitoring
def get_task_status(task_id: str) -> Dict[str, Any]:
    """Get status of a task."""
    result = celery_app.AsyncResult(task_id)

    return {
        "task_id": task_id,
        "state": result.state,
        "info": result.info,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None,
        "failed": result.failed() if result.ready() else None,
    }


def cancel_task(task_id: str) -> bool:
    """Cancel a running task."""
    celery_app.control.revoke(task_id, terminate=True)
    return True


def get_active_tasks() -> list:
    """Get list of active tasks."""
    inspect = celery_app.control.inspect()
    active = inspect.active()

    tasks = []
    if active:
        for worker, task_list in active.items():
            for task in task_list:
                tasks.append({
                    "worker": worker,
                    "task_id": task["id"],
                    "name": task["name"],
                    "args": task["args"],
                    "kwargs": task["kwargs"],
                })

    return tasks
