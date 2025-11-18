# API Reference

Complete REST API documentation for the System Health Analyzer.

## Base URL

- Local: `http://localhost:8000`
- Production: `https://api.example.com`

## Authentication

### Methods

1. **JWT Token** (Recommended)
2. **API Key** (For programmatic access)
3. **OAuth 2.0** (For user authentication)

### JWT Authentication

```bash
# Login to get token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# Response
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "Bearer"
}

# Use token in requests
curl http://localhost:8000/api/protected \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### API Key Authentication

```bash
curl http://localhost:8000/api/data \
  -H "X-API-Key: sha_your-api-key-here"
```

## Core Endpoints

### Health & Status

#### GET /health
Check application health.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "healthy",
    "cache": "healthy",
    "ai": "healthy"
  }
}
```

#### GET /metrics
Prometheus metrics endpoint.

```bash
curl http://localhost:8000/metrics
```

---

## Analysis Endpoints

### POST /api/analyze
Trigger system analysis.

**Request:**
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "trigger": "manual",
    "components": ["logs", "metrics", "anomalies"]
  }'
```

**Response:**
```json
{
  "run_id": "run_1704110400123",
  "status": "running",
  "started_at": "2024-01-01T12:00:00Z",
  "components": ["logs", "metrics", "anomalies"]
}
```

### GET /api/analyze/{run_id}
Get analysis status and results.

**Request:**
```bash
curl http://localhost:8000/api/analyze/run_1704110400123
```

**Response:**
```json
{
  "run_id": "run_1704110400123",
  "status": "completed",
  "started_at": "2024-01-01T12:00:00Z",
  "completed_at": "2024-01-01T12:05:00Z",
  "duration_seconds": 300,
  "findings": {
    "severity": "high",
    "category": "performance",
    "root_cause": "Database connection pool exhausted",
    "impact": "API response time degraded by 200%",
    "recommendations": [
      "Increase connection pool size",
      "Add connection timeout handling"
    ]
  }
}
```

### GET /api/metrics
Get current system metrics.

**Request:**
```bash
curl http://localhost:8000/api/metrics
```

**Response:**
```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "cpu": {
    "percent": 45.2,
    "count": 8,
    "frequency": 2400
  },
  "memory": {
    "percent": 62.5,
    "total": 17179869184,
    "available": 6442450944,
    "used": 10737418240
  },
  "disk": {
    "percent": 58.3,
    "total": 536870912000,
    "free": 223868092416,
    "used": 313002819584
  },
  "network": {
    "bytes_sent": 1234567890,
    "bytes_recv": 9876543210
  }
}
```

---

## Historical Data Endpoints

### GET /history/analyses
Get analysis history.

**Parameters:**
- `hours` (int): Time range in hours (default: 24)
- `limit` (int): Maximum results (default: 100)
- `offset` (int): Skip first N results (default: 0)

**Request:**
```bash
curl "http://localhost:8000/history/analyses?hours=24&limit=50"
```

**Response:**
```json
{
  "total": 150,
  "count": 50,
  "analyses": [
    {
      "run_id": "run_1704110400123",
      "timestamp": "2024-01-01T12:00:00Z",
      "trigger": "scheduled",
      "status": "completed",
      "duration_seconds": 300,
      "findings": {...}
    }
  ]
}
```

### GET /history/metrics
Get metrics history.

**Parameters:**
- `hours` (int): Time range (default: 24)
- `limit` (int): Maximum results (default: 1000)
- `metric_type` (str): Filter by type (cpu/memory/disk)

**Request:**
```bash
curl "http://localhost:8000/history/metrics?hours=6&limit=100"
```

**Response:**
```json
{
  "total": 360,
  "count": 100,
  "metrics": [
    {
      "id": 12345,
      "timestamp": "2024-01-01T12:00:00Z",
      "cpu_percent": 45.2,
      "memory_percent": 62.5,
      "disk_percent": 58.3
    }
  ]
}
```

### GET /history/alerts
Get alert history.

**Parameters:**
- `hours` (int): Time range (default: 24)
- `limit` (int): Maximum results (default: 100)
- `priority` (str): Filter by priority (low/medium/high/critical)
- `resolved` (bool): Filter by resolution status

**Request:**
```bash
curl "http://localhost:8000/history/alerts?hours=24&priority=high&resolved=false"
```

**Response:**
```json
{
  "total": 15,
  "count": 15,
  "alerts": [
    {
      "alert_id": "alert_1704110400123",
      "timestamp": "2024-01-01T12:00:00Z",
      "title": "High CPU Usage Detected",
      "priority": "high",
      "resolved": false,
      "channels_sent": ["slack", "email"]
    }
  ]
}
```

### GET /history/alerts/stats
Get alert statistics.

**Parameters:**
- `hours` (int): Time range (default: 24)

**Request:**
```bash
curl "http://localhost:8000/history/alerts/stats?hours=168"
```

**Response:**
```json
{
  "total": 250,
  "by_priority": {
    "low": 100,
    "medium": 80,
    "high": 50,
    "critical": 20
  },
  "resolved": 200,
  "unresolved": 50,
  "avg_resolution_time_minutes": 45.5
}
```

---

## Analytics Endpoints

### GET /history/analytics/health-score
Get system health score.

**Request:**
```bash
curl http://localhost:8000/history/analytics/health-score
```

**Response:**
```json
{
  "overall_score": 85.5,
  "timestamp": "2024-01-01T12:00:00Z",
  "components": {
    "performance": 90.0,
    "reliability": 85.0,
    "security": 82.0
  },
  "breakdown": {
    "cpu_score": 95.0,
    "memory_score": 88.0,
    "disk_score": 92.0,
    "alert_penalty": 10.0
  },
  "trend": "improving"
}
```

### GET /history/analytics/trends
Get trend analysis.

**Parameters:**
- `hours` (int): Time range (default: 24)
- `metric` (str): Metric to analyze (cpu/memory/disk)

**Request:**
```bash
curl "http://localhost:8000/history/analytics/trends?hours=24&metric=cpu"
```

**Response:**
```json
{
  "metric": "cpu",
  "period_hours": 24,
  "trend_direction": "increasing",
  "current_avg": 65.5,
  "previous_avg": 45.2,
  "change_percent": 44.9,
  "prediction_next_hour": 68.3,
  "anomalies_detected": 3
}
```

### GET /history/analytics/mttr
Get Mean Time To Resolution.

**Parameters:**
- `hours` (int): Time range (default: 168)

**Request:**
```bash
curl "http://localhost:8000/history/analytics/mttr?hours=168"
```

**Response:**
```json
{
  "period_hours": 168,
  "overall_mttr_minutes": 45.5,
  "by_priority": {
    "low": 120.5,
    "medium": 60.2,
    "high": 30.1,
    "critical": 15.5
  },
  "total_alerts": 250,
  "resolved_alerts": 200,
  "resolution_rate": 0.8
}
```

### GET /history/recurring-issues
Get recurring issues.

**Parameters:**
- `days` (int): Look back period (default: 30)
- `min_occurrences` (int): Minimum occurrences (default: 3)

**Request:**
```bash
curl "http://localhost:8000/history/recurring-issues?days=30&min_occurrences=5"
```

**Response:**
```json
{
  "total": 5,
  "issues": [
    {
      "fingerprint": "db_connection_timeout",
      "first_seen": "2024-01-01T12:00:00Z",
      "last_seen": "2024-01-15T14:30:00Z",
      "occurrences": 12,
      "avg_interval_hours": 48.5,
      "category": "database",
      "description": "Database connection timeout"
    }
  ]
}
```

---

## Notification Endpoints

### POST /api/notifications/send
Send a notification.

**Request:**
```bash
curl -X POST http://localhost:8000/api/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Alert",
    "message": "This is a test notification",
    "priority": "medium",
    "channels": ["slack", "email"]
  }'
```

**Response:**
```json
{
  "alert_id": "alert_1704110400123",
  "sent_to": ["slack", "email"],
  "results": {
    "slack": "success",
    "email": "success"
  }
}
```

### GET /api/notifications/channels
List configured notification channels.

**Request:**
```bash
curl http://localhost:8000/api/notifications/channels
```

**Response:**
```json
{
  "channels": [
    {
      "name": "slack",
      "enabled": true,
      "type": "webhook"
    },
    {
      "name": "email",
      "enabled": true,
      "type": "smtp"
    },
    {
      "name": "pagerduty",
      "enabled": false,
      "type": "api"
    }
  ]
}
```

---

## Data Retention Endpoints

### POST /retention/cleanup/{table_name}
Clean up old data from a table.

**Parameters:**
- `retention_days` (int): Keep data newer than N days

**Request:**
```bash
curl -X POST "http://localhost:8000/retention/cleanup/metrics_snapshots?retention_days=30"
```

**Response:**
```json
{
  "table": "metrics_snapshots",
  "retention_days": 30,
  "records_deleted": 5000,
  "archived": true
}
```

### POST /retention/export/{table_name}
Export historical data.

**Parameters:**
- `hours` (int): Export last N hours of data
- `format` (str): Export format (json/csv)

**Request:**
```bash
curl -X POST "http://localhost:8000/retention/export/alerts?hours=168&format=json"
```

**Response:**
```json
{
  "table": "alerts",
  "format": "json",
  "records_exported": 250,
  "file_path": "/exports/alerts_2024-01-01.json",
  "file_size_bytes": 524288
}
```

---

## Background Task Endpoints

### POST /tasks/trigger/{task_name}
Trigger a background task.

**Request:**
```bash
curl -X POST http://localhost:8000/tasks/trigger/run_system_analysis
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_name": "run_system_analysis",
  "status": "pending",
  "created_at": "2024-01-01T12:00:00Z"
}
```

### GET /tasks/status/{task_id}
Get task status.

**Request:**
```bash
curl http://localhost:8000/tasks/status/550e8400-e29b-41d4-a716-446655440000
```

**Response:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "SUCCESS",
  "info": {
    "metrics": {...},
    "diagnosis": {...}
  },
  "ready": true,
  "successful": true
}
```

### GET /tasks/active
List active background tasks.

**Request:**
```bash
curl http://localhost:8000/tasks/active
```

**Response:**
```json
{
  "count": 3,
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "run_system_analysis",
      "worker": "celery@worker1",
      "started_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

---

## Cache Management Endpoints

### GET /api/cache/stats
Get cache statistics.

**Request:**
```bash
curl http://localhost:8000/api/cache/stats
```

**Response:**
```json
{
  "hits": 1500,
  "misses": 500,
  "total_requests": 2000,
  "hit_rate": "75.00%",
  "redis": {
    "total_commands_processed": 50000,
    "keyspace_hits": 45000,
    "keyspace_misses": 5000
  }
}
```

### POST /api/cache/clear
Clear cache.

**Parameters:**
- `pattern` (str): Pattern to match (default: "*")

**Request:**
```bash
curl -X POST "http://localhost:8000/api/cache/clear?pattern=analysis:*"
```

**Response:**
```json
{
  "keys_deleted": 150,
  "pattern": "analysis:*"
}
```

---

## Error Responses

All endpoints may return standard error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid input: metric_type must be one of: cpu, memory, disk"
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "detail": "Insufficient permissions. Required roles: [admin]"
}
```

### 404 Not Found
```json
{
  "detail": "Analysis run not found: run_12345"
}
```

### 429 Too Many Requests
```json
{
  "detail": "Rate limit exceeded",
  "retry_after": 60
}
```

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704110460
Retry-After: 60
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## Rate Limiting

All API endpoints are rate limited:

- **Default Limit**: 100 requests per minute per IP
- **Authenticated Users**: 500 requests per minute
- **API Keys**: Configurable per key

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704110460
```

---

## Pagination

Endpoints that return lists support pagination:

**Parameters:**
- `limit` (int): Number of results per page
- `offset` (int): Skip first N results

**Response:**
```json
{
  "total": 1000,
  "count": 50,
  "limit": 50,
  "offset": 0,
  "items": [...]
}
```

---

## WebSocket Endpoints

### WS /ws/metrics
Real-time metrics stream.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/metrics');

ws.onmessage = (event) => {
  const metrics = JSON.parse(event.data);
  console.log('CPU:', metrics.cpu.percent);
};
```

### WS /ws/alerts
Real-time alert stream.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/alerts');

ws.onmessage = (event) => {
  const alert = JSON.parse(event.data);
  console.log('Alert:', alert.title, alert.priority);
};
```

---

## SDK Examples

### Python

```python
import requests

class SystemHealthClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}

    def get_health(self):
        response = requests.get(
            f"{self.base_url}/health",
            headers=self.headers
        )
        return response.json()

    def trigger_analysis(self):
        response = requests.post(
            f"{self.base_url}/api/analyze",
            headers=self.headers,
            json={"trigger": "manual"}
        )
        return response.json()

# Usage
client = SystemHealthClient(
    "http://localhost:8000",
    "sha_your-api-key-here"
)

health = client.get_health()
print(f"Status: {health['status']}")
```

### JavaScript

```javascript
class SystemHealthClient {
  constructor(baseUrl, apiKey) {
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
  }

  async getHealth() {
    const response = await fetch(`${this.baseUrl}/health`, {
      headers: { 'X-API-Key': this.apiKey }
    });
    return response.json();
  }

  async triggerAnalysis() {
    const response = await fetch(`${this.baseUrl}/api/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey
      },
      body: JSON.stringify({ trigger: 'manual' })
    });
    return response.json();
  }
}

// Usage
const client = new SystemHealthClient(
  'http://localhost:8000',
  'sha_your-api-key-here'
);

const health = await client.getHealth();
console.log('Status:', health.status);
```

---

## See Also

- [Quick Start Guide](QUICKSTART.md)
- [Authentication Guide](SECURITY.md)
- [Configuration Guide](CONFIGURATION.md)
- [Deployment Guide](DEPLOYMENT.md)
