"""Main FastAPI application."""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import uuid
from datetime import datetime

from src.config import settings
from src.models.schemas import (
    AnalysisRequest,
    AnalysisResult,
    LogEntry,
    SystemMetrics,
    LogFormat,
)
from src.collectors.log_collector import LogCollector
from src.collectors.metrics_collector import MetricsCollector
from src.analyzers.log_analyzer import LogAnalyzer
from src.analyzers.anomaly_detector import AnomalyDetector
from src.ai.llm_client import LLMClient
from src.fixers.auto_fixer import AutoFixer
from src.github_integration.pr_creator import PRCreator
from src.notifications.setup import get_notification_manager
from src.notifications.base import Alert, NotificationPriority


app = FastAPI(
    title="Plant - AI System Health Analyzer",
    description="AI-powered system health analysis and automated fixing",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
metrics_collector = MetricsCollector()
anomaly_detector = AnomalyDetector()
notification_manager = get_notification_manager()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Plant AI System Analyzer",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/analyze", response_model=AnalysisResult)
async def analyze(request: AnalysisRequest, background_tasks: BackgroundTasks):
    """
    Analyze logs and metrics.

    Accepts either a log file path or raw log content.
    Optionally includes AI analysis, auto-fix, and PR creation.
    """
    start_time = datetime.utcnow()
    request_id = str(uuid.uuid4())

    try:
        # Collect logs
        log_collector = LogCollector()
        logs = []

        if request.log_file_path:
            logs = log_collector.parse_file(request.log_file_path)
        elif request.log_content:
            logs = log_collector.parse_string(request.log_content)

        # Collect metrics
        metrics = request.metrics
        if not metrics:
            metrics = metrics_collector.collect()

        # Analyze logs
        log_analyzer = LogAnalyzer()
        log_analysis = log_analyzer.analyze(logs)
        anomalies = log_analysis.get("anomalies", [])

        # Detect resource issues
        resource_issues = metrics_collector.detect_resource_issues(metrics)

        result = AnalysisResult(
            request_id=request_id,
            logs_analyzed=len(logs),
            anomalies=anomalies,
            summary=f"Analyzed {len(logs)} logs, found {len(anomalies)} anomalies",
        )

        # AI analysis if requested
        if request.include_ai_analysis and logs:
            llm_client = LLMClient()
            diagnosis = llm_client.analyze_logs(logs, anomalies, metrics)
            result.diagnoses.append(diagnosis)

            # Auto-fix if requested
            if request.auto_fix and settings.auto_fix_enabled:
                auto_fixer = AutoFixer(llm_client)
                fix = auto_fixer.generate_fix(diagnosis)
                result.fixes.append(fix)

                # Create PR if requested
                if request.auto_pr and settings.auto_pr_enabled:
                    background_tasks.add_task(
                        create_pr_background, diagnosis, fix
                    )

        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        result.processing_time_ms = processing_time

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/current", response_model=SystemMetrics)
async def get_current_metrics():
    """Get current system metrics."""
    try:
        metrics = metrics_collector.collect()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/detailed")
async def get_detailed_metrics():
    """Get detailed system metrics including per-process info."""
    try:
        metrics = metrics_collector.collect_detailed()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/history")
async def get_metrics_history(limit: int = 100):
    """Get metrics history."""
    try:
        history = metrics_collector.history[-limit:]
        return {"count": len(history), "metrics": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/metrics/issues")
async def get_resource_issues():
    """Get current resource issues."""
    try:
        metrics = metrics_collector.collect()
        issues = metrics_collector.detect_resource_issues(metrics)
        return {"issues": issues, "count": len(issues)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/logs/parse")
async def parse_logs(
    content: str, log_format: LogFormat = LogFormat.CUSTOM
):
    """Parse log content and return structured entries."""
    try:
        log_collector = LogCollector()
        entries = log_collector.parse_string(content, log_format)
        return {"count": len(entries), "entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomalies/train")
async def train_anomaly_detector(history_limit: int = 100):
    """Train anomaly detector on metrics history."""
    try:
        if len(metrics_collector.history) < 10:
            raise HTTPException(
                status_code=400,
                detail="Not enough metrics history (need at least 10 samples)",
            )

        history = metrics_collector.history[-history_limit:]
        anomaly_detector.train(history)

        return {
            "status": "trained",
            "samples_used": len(history),
            "message": "Anomaly detector trained successfully",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/anomalies/detect")
async def detect_anomalies():
    """Detect anomalies in current metrics."""
    try:
        if not anomaly_detector.is_trained:
            raise HTTPException(
                status_code=400,
                detail="Anomaly detector not trained. Call /anomalies/train first",
            )

        metrics = metrics_collector.collect()
        is_anomaly, score = anomaly_detector.detect(metrics)

        result = {
            "is_anomaly": is_anomaly,
            "anomaly_score": score,
            "metrics": metrics,
        }

        if is_anomaly:
            anomaly = anomaly_detector.classify_anomaly(metrics, score)
            result["anomaly_details"] = anomaly

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def create_pr_background(diagnosis, fix):
    """Background task to create PR."""
    try:
        pr_creator = PRCreator()
        # This would need actual codebase path from config
        # pr = pr_creator.create_pr(diagnosis, fix, codebase_path)
        print(f"PR creation task started for fix {fix.fix_id}")
    except Exception as e:
        print(f"Error creating PR: {e}")


# Notification Endpoints

@app.post("/notifications/send")
async def send_notification(
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.MEDIUM,
    source: str = "api",
    channels: Optional[list[str]] = None,
):
    """Send a custom notification."""
    try:
        alert = Alert(
            id=f"custom_{datetime.utcnow().isoformat()}",
            title=title,
            message=message,
            priority=priority,
            source=source,
        )

        results = await notification_manager.send_alert(alert, channels)

        return {
            "alert_id": alert.id,
            "results": [r.dict() for r in results],
            "success": any(r.success for r in results),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/channels")
async def get_notification_channels():
    """Get status of all notification channels."""
    try:
        status = notification_manager.get_channel_status()
        return {"channels": status, "count": len(status)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/channels/{channel_name}/test")
async def test_notification_channel(channel_name: str):
    """Test a specific notification channel."""
    try:
        if channel_name not in notification_manager.channels:
            raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")

        channel = notification_manager.channels[channel_name]
        result = channel.test_connection()

        return {
            "channel": channel_name,
            "test_passed": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/channels/{channel_name}/enable")
async def enable_notification_channel(channel_name: str):
    """Enable a notification channel."""
    try:
        result = notification_manager.enable_channel(channel_name)
        if not result:
            raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")

        return {"channel": channel_name, "enabled": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/channels/{channel_name}/disable")
async def disable_notification_channel(channel_name: str):
    """Disable a notification channel."""
    try:
        result = notification_manager.disable_channel(channel_name)
        if not result:
            raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")

        return {"channel": channel_name, "enabled": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/summary")
async def get_notification_summary(hours: int = 24):
    """Get summary of recent alerts and notifications."""
    try:
        summary = notification_manager.get_alert_summary(hours)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notifications/rules")
async def get_alert_rules():
    """Get all alert rules."""
    try:
        rules = notification_manager.rule_engine.list_rules()
        return {"rules": [r.dict() for r in rules], "count": len(rules)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/rules/{rule_name}/enable")
async def enable_alert_rule(rule_name: str):
    """Enable an alert rule."""
    try:
        result = notification_manager.rule_engine.enable_rule(rule_name)
        if not result:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")

        return {"rule": rule_name, "enabled": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/notifications/rules/{rule_name}/disable")
async def disable_alert_rule(rule_name: str):
    """Disable an alert rule."""
    try:
        result = notification_manager.rule_engine.disable_rule(rule_name)
        if not result:
            raise HTTPException(status_code=404, detail=f"Rule '{rule_name}' not found")

        return {"rule": rule_name, "enabled": False}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Background task to process metrics with notifications
async def process_metrics_with_notifications():
    """Background task to continuously monitor and send alerts."""
    while True:
        try:
            # Collect metrics
            metrics = metrics_collector.collect()

            # Process through notification manager
            await notification_manager.process_metrics(metrics)

            # Clean old history every hour
            import random
            if random.random() < 0.01:  # ~1% chance each run
                notification_manager.clear_history(keep_hours=24)

        except Exception as e:
            print(f"Error in metrics monitoring: {e}")

        # Wait for next interval
        import asyncio
        await asyncio.sleep(settings.metrics_interval)


@app.on_event("startup")
async def startup_event():
    """Start background tasks on startup."""
    if settings.notifications_enabled:
        # Start background monitoring (optional - can be disabled)
        # import asyncio
        # asyncio.create_task(process_metrics_with_notifications())
        pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
    )
