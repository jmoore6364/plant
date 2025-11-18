# Database & Historical Tracking System

Complete guide to the Plant AI database system for historical tracking and analytics.

## Overview

The database system provides **persistent storage** and **historical analysis** of all system events, metrics, and fixes. It enables:

- **Historical Tracking**: Store all analyses, metrics, alerts, diagnoses, and fixes
- **Trend Analysis**: Identify patterns and predict future issues
- **Performance Metrics**: Track MTTR, system health scores, and fix effectiveness
- **Recurring Issue Detection**: Identify problems that keep coming back
- **Data Retention**: Automated cleanup and archiving

## Architecture

```
Database Layer
├── Models (SQLAlchemy)
│   ├── AnalysisRun - Analysis execution records
│   ├── MetricsSnapshot - System metrics over time
│   ├── AlertHistory - All alerts sent
│   ├── DiagnosisHistory - AI diagnoses
│   ├── FixHistory - Generated fixes
│   ├── PRHistory - Pull requests created
│   ├── SystemHealthScore - Health scores
│   ├── IssueRecurrence - Recurring problem tracking
│   └── DataRetentionLog - Cleanup operations
│
├── Repository Layer
│   ├── Data access patterns
│   ├── Complex queries
│   └── Statistics calculations
│
├── Analytics Engine
│   ├── System health scoring
│   ├── Trend analysis
│   ├── MTTR calculation
│   └── Fix effectiveness
│
└── Retention Manager
    ├── Automated cleanup
    ├── Data archiving
    └── Export capabilities
```

## Quick Start

### 1. Database Initialization

The database is automatically initialized on application startup:

```python
from src.database.connection import init_db

# Initialize tables
await init_db()
```

### 2. Storing Data

```python
from src.database.connection import get_db_session
from src.database.repository import MetricsRepository

async with get_db_session() as db:
    metrics_repo = MetricsRepository(db)

    # Store metrics snapshot
    await metrics_repo.create({
        "cpu_percent": 75.5,
        "memory_percent": 60.2,
        "disk_usage_percent": 45.0,
        "memory_available_mb": 4096.0,
        "disk_free_gb": 100.0,
        "network_bytes_sent": 1000000,
        "network_bytes_recv": 2000000,
        "process_count": 150,
    })
```

### 3. Querying Historical Data

```python
from src.database.repository import AlertRepository

async with get_db_session() as db:
    alert_repo = AlertRepository(db)

    # Get recent alerts
    alerts = await alert_repo.get_recent(limit=100, hours=24)

    # Get statistics
    stats = await alert_repo.get_stats(hours=24)
    print(f"Total alerts: {stats['total_alerts']}")
    print(f"MTTR: {stats['avg_resolution_time_minutes']} minutes")
```

### 4. Analytics

```python
from src.database.analytics import AnalyticsEngine

async with get_db_session() as db:
    engine = AnalyticsEngine(db)

    # Get system health score
    health = await engine.get_system_health_score()
    print(f"Health score: {health['overall_score']}/100")

    # Analyze trends
    cpu_trend = await engine.get_trend_analysis("cpu", hours=24)
    print(f"CPU trend: {cpu_trend['trend_direction']}")

    # Get MTTR
    mttr = await engine.get_mttr_analysis(hours=168)
    print(f"MTTR: {mttr['overall_mttr_minutes']} minutes")
```

## API Endpoints

### Analysis History

```bash
# Get analysis history
GET /history/analyses?limit=100&hours=24

# Get analysis statistics
GET /history/analyses/stats?hours=24
```

Response:
```json
{
  "time_window_hours": 24,
  "total_runs": 50,
  "total_logs": 5000,
  "total_anomalies": 15,
  "total_fixes": 8,
  "avg_processing_time_ms": 1234.5
}
```

### Metrics History

```bash
# Get metrics snapshots
GET /history/metrics?limit=1000&hours=24

# Get averages
GET /history/metrics/averages?hours=24

# Get anomalies
GET /history/metrics/anomalies?hours=24
```

### Alert History

```bash
# Get alert history
GET /history/alerts?limit=100&hours=24&priority=high

# Get alert statistics
GET /history/alerts/stats?hours=24

# Get unresolved alerts
GET /history/alerts/unresolved

# Resolve an alert
POST /history/alerts/{alert_id}/resolve
```

### Diagnoses

```bash
# Get diagnosis history
GET /history/diagnoses?limit=100&category=performance

# Find similar diagnoses
GET /history/diagnoses/{diagnosis_id}/similar
```

### Fix History

```bash
# Get fix history
GET /history/fixes?limit=100

# Get effectiveness stats
GET /history/fixes/effectiveness?hours=168
```

### Recurring Issues

```bash
# Get recurring issues
GET /history/recurring-issues?min_occurrences=3

# Get periodic issues
GET /history/recurring-issues/periodic
```

### Analytics

```bash
# Get system health score
GET /history/analytics/health-score

# Get trend analysis
GET /history/analytics/trends?metric=cpu&hours=24

# Get MTTR analysis
GET /history/analytics/mttr?hours=168

# Get comprehensive report
GET /history/analytics/report?hours=24
```

Response (health score):
```json
{
  "overall_score": 87.5,
  "performance_score": 85.2,
  "reliability_score": 90.1,
  "security_score": 85.0,
  "mttr_minutes": 15.3,
  "trend": "improving",
  "metrics": {
    "alert_count_24h": 12,
    "critical_alerts_24h": 2,
    "issues_resolved_24h": 10,
    "fix_success_rate": 85.5
  }
}
```

### Data Retention

```bash
# Clean up old data from a table
POST /history/retention/cleanup/alert_history?retention_days=90

# Clean up all tables
POST /history/retention/cleanup-all

# Export data
POST /history/retention/export/metrics_snapshots?export_path=/path/to/export.json

# Get database stats
GET /history/retention/stats

# Get retention logs
GET /history/retention/logs?limit=100
```

## Data Models

### AnalysisRun

Tracks each analysis execution:

```python
{
    "request_id": "unique_id",
    "timestamp": "2024-01-15T10:30:00Z",
    "logs_analyzed": 1000,
    "anomalies_found": 5,
    "diagnoses_generated": 3,
    "fixes_generated": 2,
    "prs_created": 1,
    "processing_time_ms": 1500.0,
    "success": true
}
```

### MetricsSnapshot

Stores system metrics:

```python
{
    "timestamp": "2024-01-15T10:30:00Z",
    "cpu_percent": 75.5,
    "memory_percent": 60.2,
    "disk_usage_percent": 45.0,
    "memory_available_mb": 4096.0,
    "disk_free_gb": 100.0,
    "network_bytes_sent": 1000000,
    "network_bytes_recv": 2000000,
    "process_count": 150,
    "cpu_anomaly": false,
    "memory_anomaly": false,
    "disk_anomaly": false
}
```

### AlertHistory

Historical record of all alerts:

```python
{
    "alert_id": "alert_001",
    "timestamp": "2024-01-15T10:30:00Z",
    "title": "High CPU Usage",
    "message": "CPU at 95%",
    "priority": "high",
    "source": "metrics",
    "fingerprint": "cpu_high",
    "group_key": "performance",
    "tags": ["cpu", "performance"],
    "resolved": true,
    "resolved_at": "2024-01-15T11:00:00Z",
    "resolution_time_minutes": 30.0
}
```

### SystemHealthScore

Overall system health tracking:

```python
{
    "timestamp": "2024-01-15T12:00:00Z",
    "overall_score": 87.5,
    "reliability_score": 90.0,
    "performance_score": 85.0,
    "security_score": 85.0,
    "uptime_percent": 99.9,
    "mttr_minutes": 15.3,
    "alert_count_24h": 12,
    "critical_alerts_24h": 2,
    "score_trend": "improving"
}
```

### IssueRecurrence

Tracks recurring problems:

```python
{
    "issue_fingerprint": "memory_leak_app_server",
    "issue_title": "Memory Leak Detected",
    "issue_category": "performance",
    "first_occurrence": "2024-01-01T10:00:00Z",
    "last_occurrence": "2024-01-15T10:00:00Z",
    "occurrence_count": 12,
    "average_interval_hours": 28.0,
    "is_periodic": true,
    "times_fixed": 3,
    "permanent_fix_applied": false
}
```

## Analytics Features

### 1. System Health Score

Calculates overall system health (0-100) based on:

- **Performance** (40%): CPU, memory, disk usage
- **Reliability** (40%): Alert frequency, resolution rate
- **Security** (20%): Security-related findings

```python
health = await engine.get_system_health_score()

if health['overall_score'] < 70:
    print("⚠️ System health degraded")
elif health['trend'] == 'declining':
    print("📉 Health is declining")
else:
    print("✅ System healthy")
```

### 2. Trend Analysis

Analyzes metric trends and predicts future values:

```python
cpu_trend = await engine.get_trend_analysis("cpu", hours=24)

print(f"Current: {cpu_trend['current_value']}%")
print(f"Average: {cpu_trend['average']}%")
print(f"Trend: {cpu_trend['trend_direction']}")
print(f"Predicted next: {cpu_trend['predicted_next']}%")
print(f"Risk level: {cpu_trend['risk_level']}")
```

### 3. MTTR (Mean Time To Resolution)

Tracks how quickly issues are resolved:

```python
mttr = await engine.get_mttr_analysis(hours=168)

print(f"Overall MTTR: {mttr['overall_mttr_minutes']} minutes")
print(f"By priority: {mttr['by_priority']}")
print(f"Trend: {mttr['trend']}")  # improving, worsening, stable
```

### 4. Recurring Issue Detection

Identifies problems that keep happening:

```python
recurring = await engine.detect_recurring_issues(min_occurrences=3)

print(f"Total recurring issues: {recurring['total_recurring_issues']}")
print(f"High frequency: {recurring['high_frequency_issues']}")
print(f"Periodic: {recurring['periodic_issues']}")

for issue in recurring['top_recurring']:
    print(f"- {issue['title']}: {issue['occurrences']} times")
```

### 5. Fix Effectiveness

Tracks how well generated fixes work:

```python
effectiveness = await engine.get_fix_effectiveness(hours=168)

print(f"Validation rate: {effectiveness['validation_rate']}%")
print(f"Application rate: {effectiveness['application_rate']}%")
print(f"Success rate: {effectiveness['success_rate']}%")
```

## Data Retention

### Default Retention Periods

| Table | Retention (days) |
|-------|-----------------|
| metrics_snapshots | 30 |
| alert_history | 90 |
| analysis_runs | 60 |
| diagnosis_history | 90 |
| fix_history | 180 |
| pr_history | 365 |
| system_health_scores | 90 |
| issue_recurrences | 365 |

### Manual Cleanup

```python
from src.database.retention import DataRetentionManager

async with get_db_session() as db:
    manager = DataRetentionManager(db)

    # Clean single table
    result = await manager.cleanup_old_data(
        "alert_history",
        retention_days=90
    )

    print(f"Deleted {result['records_deleted']} records")

    # Clean all tables
    results = await manager.cleanup_all_tables()
    print(f"Total deleted: {results['total_records_deleted']}")
```

### Archiving

Export data before deletion:

```python
# Archive to JSON before cleanup
result = await manager.archive_old_data(
    table_name="metrics_snapshots",
    archive_path="/backups/metrics_2024_01.json",
    retention_days=30
)

print(f"Archived {result['records_archived']} records")
print(f"File size: {result['archive_size_mb']} MB")
```

### Exporting Data

Export data for specific date range:

```python
from datetime import datetime, timedelta

start_date = datetime.utcnow() - timedelta(days=7)
end_date = datetime.utcnow()

result = await manager.export_data(
    table_name="alert_history",
    export_path="/exports/alerts_last_week.json",
    start_date=start_date,
    end_date=end_date
)

print(f"Exported {result['records_exported']} records")
```

## Database Migrations

Using Alembic for schema versioning:

```bash
# Create a migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

## Best Practices

### 1. Regular Cleanup

Schedule automatic cleanup:

```python
import asyncio

async def scheduled_cleanup():
    """Run cleanup daily."""
    while True:
        async with get_db_session() as db:
            manager = DataRetentionManager(db)
            await manager.cleanup_all_tables()

        await asyncio.sleep(86400)  # 24 hours
```

### 2. Monitor Database Size

```python
async with get_db_session() as db:
    manager = DataRetentionManager(db)
    stats = await manager.get_database_size_stats()

    if stats['total_records'] > 1_000_000:
        print("⚠️ Database growing large, consider cleanup")
```

### 3. Archive Before Major Cleanup

```python
# Always archive before aggressive cleanup
await manager.archive_old_data("alert_history", "/backups/alerts.json", 30)
await manager.cleanup_old_data("alert_history", 30)
```

### 4. Use Indexes Wisely

All time-based queries use indexed `timestamp` columns for performance.

### 5. Batch Operations

For large datasets, use limits:

```python
# Good - limited query
alerts = await repo.get_recent(limit=1000, hours=24)

# Avoid - unbounded query
# alerts = await repo.get_all()  # Could be millions
```

## Configuration

### Database URL

Set in `.env`:

```bash
# SQLite (default)
DATABASE_URL=sqlite+aiosqlite:///./plant.db

# PostgreSQL
DATABASE_URL=postgresql+asyncpg://user:password@localhost/plant

# MySQL
DATABASE_URL=mysql+aiomysql://user:password@localhost/plant
```

### Retention Configuration

Customize retention periods:

```python
custom_retention = {
    "metrics_snapshots": 60,  # 60 days instead of 30
    "alert_history": 180,     # 180 days instead of 90
}

await manager.cleanup_all_tables(custom_retention=custom_retention)
```

## Troubleshooting

### Database Not Initializing

```python
# Manually initialize
from src.database.connection import init_db
await init_db()
```

### Slow Queries

Check indexes:

```sql
-- SQLite
EXPLAIN QUERY PLAN SELECT * FROM alert_history WHERE timestamp > ?;

-- Should use idx_alert_timestamp index
```

### Database Locked (SQLite)

Use connection pooling or switch to PostgreSQL for high concurrency.

### Migration Conflicts

```bash
# Reset migrations (development only!)
alembic downgrade base
alembic upgrade head
```

## Performance Tips

1. **Use Pagination**: Always use `limit` in queries
2. **Filter by Time**: Use `hours` parameter to limit data range
3. **Index Usage**: Queries on `timestamp`, `priority`, `status` are indexed
4. **Async Operations**: All database operations are async for better performance
5. **Batch Inserts**: Insert multiple records in single transaction

## Next Steps

- Set up database with desired backend (SQLite/PostgreSQL)
- Configure retention periods for your needs
- Set up scheduled cleanup jobs
- Monitor database size and performance
- Export historical data for long-term archival
- Integrate analytics into dashboards

For more information:
- [Main README](../README.md)
- [Setup Guide](../SETUP.md)
- [API Documentation](http://localhost:8000/docs)
