"""Analytics engine for historical data analysis."""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import statistics

from sqlalchemy.ext.asyncio import AsyncSession
from src.database.repository import (
    AnalysisRepository,
    MetricsRepository,
    AlertRepository,
    DiagnosisRepository,
    FixRepository,
    IssueRecurrenceRepository,
)
from src.database.models import SystemHealthScore


class AnalyticsEngine:
    """Engine for analyzing historical data and generating insights."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.analysis_repo = AnalysisRepository(session)
        self.metrics_repo = MetricsRepository(session)
        self.alert_repo = AlertRepository(session)
        self.diagnosis_repo = DiagnosisRepository(session)
        self.fix_repo = FixRepository(session)
        self.recurrence_repo = IssueRecurrenceRepository(session)

    async def get_system_health_score(self) -> Dict[str, Any]:
        """
        Calculate overall system health score.

        Returns score from 0-100 based on multiple factors.
        """
        # Get metrics from last 24 hours
        metrics = await self.metrics_repo.get_recent(hours=24)
        alert_stats = await self.alert_repo.get_stats(hours=24)
        fix_stats = await self.fix_repo.get_success_rate(hours=168)  # 7 days

        # Calculate component scores

        # 1. Performance Score (based on metrics)
        if metrics:
            avg_cpu = statistics.mean(m.cpu_percent for m in metrics)
            avg_memory = statistics.mean(m.memory_percent for m in metrics)
            avg_disk = statistics.mean(m.disk_usage_percent for m in metrics)

            # Higher usage = lower score
            performance_score = 100 - (
                (avg_cpu * 0.4 + avg_memory * 0.4 + avg_disk * 0.2)
            )
            performance_score = max(0, min(100, performance_score))
        else:
            performance_score = 100

        # 2. Reliability Score (based on alerts and resolution)
        total_alerts = alert_stats["total_alerts"]
        critical_alerts = alert_stats["by_priority"].get("critical", 0)

        if total_alerts > 0:
            alert_penalty = min(total_alerts * 2, 50)  # Max 50 point penalty
            critical_penalty = critical_alerts * 10  # More penalty for critical
            reliability_score = 100 - alert_penalty - critical_penalty
            reliability_score = max(0, min(100, reliability_score))

            # Bonus for good resolution rate
            if alert_stats["resolved_alerts"] > 0:
                resolution_rate = (
                    alert_stats["resolved_alerts"] / total_alerts * 100
                )
                reliability_score = (reliability_score * 0.7) + (resolution_rate * 0.3)
        else:
            reliability_score = 100

        # 3. Security Score (placeholder - could integrate with vulnerability scans)
        security_score = 85.0  # Default moderate score

        # 4. Overall Score (weighted average)
        overall_score = (
            performance_score * 0.40 +
            reliability_score * 0.40 +
            security_score * 0.20
        )

        # Calculate MTTR (Mean Time To Resolution)
        mttr_minutes = alert_stats.get("avg_resolution_time_minutes", 0)

        # Determine trend
        score_trend = await self._calculate_score_trend()

        # Create health score record
        health_score = SystemHealthScore(
            overall_score=overall_score,
            reliability_score=reliability_score,
            performance_score=performance_score,
            security_score=security_score,
            uptime_percent=max(0, 100 - (total_alerts / 10)),  # Simplified
            mttr_minutes=mttr_minutes,
            alert_count_24h=total_alerts,
            critical_alerts_24h=critical_alerts,
            issues_resolved_24h=alert_stats["resolved_alerts"],
            score_trend=score_trend,
        )

        self.session.add(health_score)
        await self.session.flush()

        return {
            "overall_score": round(overall_score, 1),
            "performance_score": round(performance_score, 1),
            "reliability_score": round(reliability_score, 1),
            "security_score": round(security_score, 1),
            "mttr_minutes": round(mttr_minutes, 1),
            "trend": score_trend,
            "metrics": {
                "alert_count_24h": total_alerts,
                "critical_alerts_24h": critical_alerts,
                "issues_resolved_24h": alert_stats["resolved_alerts"],
                "fix_success_rate": round(fix_stats.get("success_rate", 0), 1),
            },
        }

    async def _calculate_score_trend(self) -> str:
        """Calculate if system health is improving, stable, or declining."""
        from sqlalchemy import select, desc

        # Get last 7 health scores
        result = await self.session.execute(
            select(SystemHealthScore)
            .order_by(desc(SystemHealthScore.timestamp))
            .limit(7)
        )
        scores = list(result.scalars().all())

        if len(scores) < 3:
            return "stable"

        recent_avg = statistics.mean(s.overall_score for s in scores[:3])
        older_avg = statistics.mean(s.overall_score for s in scores[-3:])

        diff = recent_avg - older_avg

        if diff > 5:
            return "improving"
        elif diff < -5:
            return "declining"
        else:
            return "stable"

    async def get_trend_analysis(
        self, metric: str = "cpu", hours: int = 24
    ) -> Dict[str, Any]:
        """
        Analyze trend for a specific metric.

        Args:
            metric: Metric to analyze (cpu, memory, disk)
            hours: Time window in hours

        Returns:
            Trend analysis with predictions
        """
        snapshots = await self.metrics_repo.get_recent(hours=hours, limit=1000)

        if not snapshots:
            return {"status": "no_data"}

        # Extract metric values
        metric_map = {
            "cpu": lambda s: s.cpu_percent,
            "memory": lambda s: s.memory_percent,
            "disk": lambda s: s.disk_usage_percent,
        }

        if metric not in metric_map:
            return {"status": "invalid_metric"}

        values = [metric_map[metric](s) for s in reversed(snapshots)]

        # Calculate statistics
        avg_value = statistics.mean(values)
        max_value = max(values)
        min_value = min(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0

        # Simple trend detection (linear)
        # Compare first half vs second half
        mid = len(values) // 2
        first_half_avg = statistics.mean(values[:mid]) if mid > 0 else avg_value
        second_half_avg = statistics.mean(values[mid:]) if mid > 0 else avg_value

        trend_direction = "increasing" if second_half_avg > first_half_avg + 2 else \
                         "decreasing" if second_half_avg < first_half_avg - 2 else \
                         "stable"

        # Predict next value (simple linear extrapolation)
        if len(values) >= 10:
            recent_trend = (values[-1] - values[-10]) / 10
            predicted_next = values[-1] + recent_trend
        else:
            predicted_next = avg_value

        # Risk assessment
        risk_level = "low"
        if metric in ["cpu", "memory"] and avg_value > 80:
            risk_level = "high"
        elif metric in ["cpu", "memory"] and avg_value > 70:
            risk_level = "medium"
        elif metric == "disk" and avg_value > 85:
            risk_level = "high"
        elif metric == "disk" and avg_value > 75:
            risk_level = "medium"

        return {
            "metric": metric,
            "time_window_hours": hours,
            "samples": len(values),
            "current_value": values[-1] if values else 0,
            "average": round(avg_value, 2),
            "maximum": round(max_value, 2),
            "minimum": round(min_value, 2),
            "std_deviation": round(std_dev, 2),
            "trend_direction": trend_direction,
            "predicted_next": round(predicted_next, 2),
            "risk_level": risk_level,
        }

    async def detect_recurring_issues(
        self, min_occurrences: int = 3
    ) -> Dict[str, Any]:
        """
        Detect issues that keep recurring.

        Returns analysis of recurring patterns.
        """
        recurring = await self.recurrence_repo.get_recurring_issues(min_occurrences)
        periodic = await self.recurrence_repo.get_periodic_issues()

        # Categorize by severity
        high_frequency = [r for r in recurring if r.occurrence_count >= 10]
        moderate_frequency = [r for r in recurring if 5 <= r.occurrence_count < 10]

        return {
            "total_recurring_issues": len(recurring),
            "high_frequency_issues": len(high_frequency),
            "moderate_frequency_issues": len(moderate_frequency),
            "periodic_issues": len(periodic),
            "top_recurring": [
                {
                    "title": r.issue_title,
                    "category": r.issue_category,
                    "occurrences": r.occurrence_count,
                    "first_seen": r.first_occurrence.isoformat(),
                    "last_seen": r.last_occurrence.isoformat(),
                    "average_interval_hours": round(r.average_interval_hours or 0, 2),
                    "is_periodic": r.is_periodic,
                }
                for r in recurring[:10]
            ],
        }

    async def get_mttr_analysis(self, hours: int = 168) -> Dict[str, Any]:
        """
        Calculate Mean Time To Resolution (MTTR) metrics.

        Args:
            hours: Time window (default 7 days)

        Returns:
            MTTR analysis by category and priority
        """
        alert_stats = await self.alert_repo.get_stats(hours=hours)

        # Get detailed resolution times
        recent_alerts = await self.alert_repo.get_recent(hours=hours, limit=1000)
        resolved_alerts = [a for a in recent_alerts if a.resolved and a.resolution_time_minutes]

        if not resolved_alerts:
            return {
                "status": "no_resolved_alerts",
                "time_window_hours": hours,
            }

        # Overall MTTR
        overall_mttr = statistics.mean(a.resolution_time_minutes for a in resolved_alerts)

        # MTTR by priority
        by_priority = defaultdict(list)
        for alert in resolved_alerts:
            by_priority[alert.priority].append(alert.resolution_time_minutes)

        priority_mttr = {
            priority: {
                "mttr_minutes": round(statistics.mean(times), 2),
                "median_minutes": round(statistics.median(times), 2),
                "count": len(times),
            }
            for priority, times in by_priority.items()
        }

        # MTTR trend (comparing first half vs second half of period)
        mid_point = len(resolved_alerts) // 2
        if mid_point > 0:
            first_half_mttr = statistics.mean(
                a.resolution_time_minutes for a in resolved_alerts[:mid_point]
            )
            second_half_mttr = statistics.mean(
                a.resolution_time_minutes for a in resolved_alerts[mid_point:]
            )

            if second_half_mttr < first_half_mttr - 5:
                trend = "improving"
            elif second_half_mttr > first_half_mttr + 5:
                trend = "worsening"
            else:
                trend = "stable"
        else:
            trend = "stable"

        return {
            "time_window_hours": hours,
            "total_resolved_alerts": len(resolved_alerts),
            "overall_mttr_minutes": round(overall_mttr, 2),
            "overall_mttr_hours": round(overall_mttr / 60, 2),
            "by_priority": priority_mttr,
            "trend": trend,
        }

    async def get_fix_effectiveness(self, hours: int = 168) -> Dict[str, Any]:
        """
        Analyze effectiveness of generated fixes.

        Args:
            hours: Time window (default 7 days)

        Returns:
            Fix effectiveness analysis
        """
        stats = await self.fix_repo.get_success_rate(hours=hours)

        # Get recent fixes for detailed analysis
        recent_fixes = await self.fix_repo.get_recent(limit=100)

        # Analyze by fix type
        by_type = defaultdict(lambda: {"total": 0, "validated": 0, "applied": 0})
        for fix in recent_fixes:
            by_type[fix.fix_type]["total"] += 1
            if fix.validation_passed:
                by_type[fix.fix_type]["validated"] += 1
            if fix.applied:
                by_type[fix.fix_type]["applied"] += 1

        type_effectiveness = {
            fix_type: {
                **data,
                "validation_rate": (data["validated"] / data["total"] * 100) if data["total"] > 0 else 0,
                "application_rate": (data["applied"] / data["total"] * 100) if data["total"] > 0 else 0,
            }
            for fix_type, data in by_type.items()
        }

        return {
            "time_window_hours": hours,
            **stats,
            "by_fix_type": type_effectiveness,
            "total_fixes_generated": len(recent_fixes),
        }

    async def get_comprehensive_report(self, hours: int = 24) -> Dict[str, Any]:
        """
        Generate comprehensive analytics report.

        Returns:
            Complete system analysis
        """
        return {
            "generated_at": datetime.utcnow().isoformat(),
            "time_window_hours": hours,
            "system_health": await self.get_system_health_score(),
            "alerts": await self.alert_repo.get_stats(hours=hours),
            "metrics_trends": {
                "cpu": await self.get_trend_analysis("cpu", hours=hours),
                "memory": await self.get_trend_analysis("memory", hours=hours),
                "disk": await self.get_trend_analysis("disk", hours=hours),
            },
            "recurring_issues": await self.detect_recurring_issues(),
            "mttr": await self.get_mttr_analysis(hours=hours * 7),  # 7x window for MTTR
            "fix_effectiveness": await self.get_fix_effectiveness(hours=hours * 7),
        }
