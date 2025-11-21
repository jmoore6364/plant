"""Seed database with comprehensive help articles."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import get_db_session, init_db
from src.database.repository import HelpArticleRepository


HELP_ARTICLES = [
    {
        "title": "Getting Started with Plant AI System Analyzer",
        "slug": "getting-started",
        "category": "Getting Started",
        "summary": "Learn the basics of Plant AI System Analyzer and how to start monitoring your systems.",
        "content": """# Getting Started

Welcome to Plant AI System Analyzer! This guide will help you get up and running quickly.

## What is Plant?

Plant is an AI-powered system health analyzer that automatically monitors your systems, analyzes logs, detects anomalies, and can even generate fixes for common issues.

## Key Features

- **Real-time System Monitoring**: Track CPU, memory, disk, and network usage
- **Log Analysis**: Automatically parse and analyze system logs
- **Anomaly Detection**: Machine learning-based detection of unusual system behavior
- **Intelligent Alerts**: Get notified when issues are detected
- **Auto-Fix**: AI-generated fixes for common problems
- **REST API**: Full programmatic access to all features

## Quick Start

1. **Access the Dashboard**: Navigate to the Dashboard page to see an overview of your system health
2. **View Metrics**: Check the Metrics page for detailed system resource usage
3. **Analyze Logs**: Use the Logs page to search and analyze system logs
4. **Configure Alerts**: Set up notification rules to stay informed
5. **Review Fixes**: Check the Fixes & PRs page for AI-generated solutions

## Next Steps

- Read about [Understanding System Metrics](#)
- Learn how to [Configure Alerts](#)
- Explore the [API Documentation](#)
""",
        "tags": ["getting-started", "introduction", "basics"],
        "icon": "rocket",
        "featured": True,
        "order": 1,
    },
    {
        "title": "Understanding System Metrics",
        "slug": "understanding-metrics",
        "category": "Monitoring",
        "summary": "Learn about the system metrics Plant monitors and what they mean for your system health.",
        "content": """# Understanding System Metrics

Plant continuously monitors several key system metrics to assess overall health.

## CPU Usage

**What it measures**: Percentage of CPU capacity being used across all cores.

**Healthy range**: 0-70% under normal load
**Warning**: 70-85%
**Critical**: Above 85%

High CPU usage may indicate:
- Resource-intensive processes running
- Infinite loops or runaway processes
- Need for vertical scaling

## Memory Usage

**What it measures**: Percentage of RAM currently in use.

**Healthy range**: 0-80%
**Warning**: 80-90%
**Critical**: Above 90%

High memory usage may indicate:
- Memory leaks in applications
- Too many concurrent processes
- Insufficient RAM for workload

## Disk Usage

**What it measures**: Percentage of disk space used on primary drive.

**Healthy range**: 0-80%
**Warning**: 80-90%
**Critical**: Above 90%

High disk usage may indicate:
- Log files growing too large
- Need for log rotation
- Need for additional storage

## Network Activity

**What it measures**: Bytes sent and received over network interfaces.

Useful for:
- Detecting unusual network traffic
- Identifying bandwidth bottlenecks
- Monitoring data transfer rates

## Load Average

**What it measures**: Average system load over 1, 5, and 15 minutes.

**Rule of thumb**: Load should be below the number of CPU cores.

High load average may indicate:
- CPU bottleneck
- I/O wait issues
- Too many concurrent processes

## Viewing Metrics

1. **Dashboard**: Overview of all metrics with real-time updates
2. **Metrics Page**: Detailed historical charts and trends
3. **API**: `/metrics/current` endpoint for programmatic access
""",
        "tags": ["metrics", "monitoring", "cpu", "memory", "disk"],
        "icon": "activity",
        "featured": True,
        "order": 2,
    },
    {
        "title": "Analyzing Logs for Errors and Issues",
        "slug": "log-analysis",
        "category": "Monitoring",
        "summary": "How to use Plant's log analysis features to identify and troubleshoot system issues.",
        "content": """# Log Analysis

Plant can automatically parse, analyze, and extract insights from your system logs.

## Supported Log Formats

Plant supports multiple log formats:

- **JSON logs**: Structured JSON log entries
- **Syslog**: Standard syslog format
- **Apache/Nginx**: Web server logs
- **Custom formats**: Configurable pattern matching

## Analyzing Logs

### Via Web Interface

1. Navigate to the **Logs** page
2. Upload a log file or paste log content
3. Select the log format
4. Click "Analyze" to see results

### Via API

```bash
curl -X POST http://localhost:8000/analyze \\
  -H "Content-Type: application/json" \\
  -d '{
    "log_content": "...",
    "include_ai_analysis": true
  }'
```

## What Plant Detects

- **Error patterns**: Identifies ERROR and CRITICAL level messages
- **Anomalies**: Unusual patterns or spikes in error rates
- **Common issues**: Recognizes known error patterns
- **Resource issues**: Correlates logs with system metrics

## AI-Powered Analysis

Enable AI analysis to get:

- **Root cause diagnosis**: What's likely causing the issue
- **Severity assessment**: How critical is the problem
- **Recommendations**: Suggested actions to resolve
- **Fix generation**: Automatic code/config fixes

## Filtering and Search

Use the Logs page to:

- Filter by log level (INFO, WARNING, ERROR, CRITICAL)
- Search by regex pattern
- View error summaries
- Download filtered results

## Best Practices

1. **Regular monitoring**: Check logs daily for issues
2. **Enable AI analysis**: Get deeper insights automatically
3. **Set up alerts**: Be notified of critical errors immediately
4. **Correlate with metrics**: Look at system metrics when errors occur
""",
        "tags": ["logs", "analysis", "errors", "troubleshooting"],
        "icon": "file-text",
        "featured": True,
        "order": 3,
    },
    {
        "title": "Configuring Alerts and Notifications",
        "slug": "alert-configuration",
        "category": "Alerts",
        "summary": "Set up intelligent alerts to be notified when issues are detected in your systems.",
        "content": """# Configuring Alerts and Notifications

Stay informed about system issues with Plant's flexible alert system.

## Alert Channels

Plant supports multiple notification channels:

### Slack
- **Setup**: Configure webhook URL in settings
- **Test**: POST to `/notifications/channels/slack/test`
- **Enable**: POST to `/notifications/channels/slack/enable`

### Discord
- **Setup**: Configure webhook URL in settings
- **Test**: POST to `/notifications/channels/discord/test`
- **Enable**: POST to `/notifications/channels/discord/enable`

### Email
- **Setup**: Configure SMTP settings
- **Supports**: Multiple recipients, HTML formatting
- **Enable**: POST to `/notifications/channels/email/enable`

### PagerDuty
- **Setup**: Configure integration key
- **Features**: Incident creation, escalation
- **Enable**: POST to `/notifications/channels/pagerduty/enable`

## Alert Rules

Configure rules to trigger alerts based on conditions:

### CPU Threshold Alert
Triggers when CPU usage exceeds threshold for specified duration.

### Memory Threshold Alert
Triggers when memory usage is critically high.

### Disk Space Alert
Triggers when disk usage exceeds safe levels.

### Log Error Alert
Triggers on ERROR or CRITICAL log entries.

### Custom Alerts
Create custom alert rules via API.

## Alert Priorities

- **CRITICAL**: Immediate attention required (pages on-call)
- **HIGH**: Important issues that need prompt resolution
- **MEDIUM**: Notable issues for investigation
- **LOW**: Informational alerts

## Managing Alerts

### Via API

**Get alert status:**
```bash
GET /notifications/summary
```

**Send test alert:**
```bash
POST /notifications/send
{
  "title": "Test Alert",
  "message": "Testing notification system",
  "priority": "MEDIUM"
}
```

**View alert rules:**
```bash
GET /notifications/rules
```

**Enable/disable rules:**
```bash
POST /notifications/rules/{rule_name}/enable
POST /notifications/rules/{rule_name}/disable
```

## Alert Deduplication

Plant automatically deduplicates similar alerts:

- **Fingerprinting**: Alerts are identified by content hash
- **Grouping**: Similar alerts are grouped together
- **Rate limiting**: Prevents alert fatigue

## Best Practices

1. **Start with critical alerts**: Focus on high-priority issues first
2. **Test channels**: Always test notification channels before relying on them
3. **Adjust thresholds**: Fine-tune based on your system's normal behavior
4. **Review regularly**: Check alert history to optimize rules
5. **Use appropriate priorities**: Don't over-escalate routine issues
""",
        "tags": ["alerts", "notifications", "slack", "email", "pagerduty"],
        "icon": "bell",
        "featured": False,
        "order": 4,
    },
    {
        "title": "Using the Plant API",
        "slug": "api-usage",
        "category": "API",
        "summary": "Complete guide to using Plant's REST API for programmatic access to all features.",
        "content": """# Using the Plant API

Plant provides a comprehensive REST API for all functionality.

## Base URL

```
http://localhost:8000
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Key Endpoints

### Health Check

```bash
GET /health
```

Returns API health status.

### Analysis

```bash
POST /analyze
Content-Type: application/json

{
  "log_content": "...",
  "include_ai_analysis": true,
  "auto_fix": false,
  "auto_pr": false
}
```

Analyze logs with optional AI diagnosis and auto-fix.

### Current Metrics

```bash
GET /metrics/current
```

Get current system metrics (CPU, memory, disk, network).

### Metrics History

```bash
GET /metrics/history?limit=100
```

Get historical metrics data.

### Resource Issues

```bash
GET /metrics/issues
```

Get current resource-related issues.

### Parse Logs

```bash
POST /logs/parse
Content-Type: application/json

{
  "content": "...",
  "log_format": "json"
}
```

Parse logs into structured entries.

### Anomaly Detection

```bash
# Train detector
GET /anomalies/train?history_limit=100

# Detect anomalies
GET /anomalies/detect
```

Train and use anomaly detection on metrics.

### Notifications

```bash
# Send alert
POST /notifications/send

# Get channel status
GET /notifications/channels

# Test channel
POST /notifications/channels/{name}/test

# Get alert rules
GET /notifications/rules
```

Manage notifications and alert rules.

### Database Queries

```bash
# Recent analyses
GET /api/database/analyses/recent?limit=10

# Metrics averages
GET /api/database/metrics/averages?hours=24

# Alert statistics
GET /api/database/alerts/stats?hours=24

# System health trend
GET /api/database/health/trend?days=7
```

Query historical data and analytics.

## Authentication

Currently, the API is open for development. Production deployments should enable authentication:

- JWT tokens via `/auth/login`
- API keys via `/auth/api-keys`
- OAuth 2.0 for third-party integrations

## Rate Limiting

API is rate-limited to prevent abuse:
- **Default**: 100 requests per minute per IP
- **Burst**: Up to 200 requests in 10 seconds
- **Headers**: `X-RateLimit-*` headers show limits

## Error Handling

API uses standard HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid parameters)
- **404**: Resource not found
- **429**: Rate limit exceeded
- **500**: Internal server error

Error responses include details:

```json
{
  "detail": "Error message here"
}
```

## Python Client Example

```python
import requests

API_URL = "http://localhost:8000"

# Get current metrics
response = requests.get(f"{API_URL}/metrics/current")
metrics = response.json()
print(f"CPU: {metrics['cpu_percent']}%")

# Analyze logs
response = requests.post(f"{API_URL}/analyze", json={
    "log_content": log_data,
    "include_ai_analysis": True
})
analysis = response.json()
print(f"Found {len(analysis['anomalies'])} anomalies")
```

## JavaScript/TypeScript Example

```typescript
const API_URL = "http://localhost:8000";

// Get current metrics
const response = await fetch(`${API_URL}/metrics/current`);
const metrics = await response.json();
console.log(`CPU: ${metrics.cpu_percent}%`);

// Analyze logs
const analysis = await fetch(`${API_URL}/analyze`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    log_content: logData,
    include_ai_analysis: true
  })
});
```
""",
        "tags": ["api", "rest", "endpoints", "integration"],
        "icon": "code",
        "featured": False,
        "order": 5,
    },
    {
        "title": "Dashboard Features Overview",
        "slug": "dashboard-features",
        "category": "Getting Started",
        "summary": "Comprehensive guide to all features available in the Plant web dashboard.",
        "content": """# Dashboard Features Overview

The Plant web dashboard provides a comprehensive interface for system monitoring.

## Main Dashboard

The main dashboard shows:

### System Health Overview
- **Overall health score**: Aggregated health metric (0-100)
- **Status indicators**: Visual status for CPU, memory, disk
- **Active alerts**: Number of current alerts by priority

### Real-time Metrics
- **CPU usage**: Current CPU percentage with trend
- **Memory usage**: RAM usage with available memory
- **Disk usage**: Disk space used and free
- **Network activity**: Bytes sent/received

### Recent Activity
- **Latest analyses**: Recent log analysis runs
- **Recent alerts**: Most recent system alerts
- **Fix history**: Recently generated fixes

### Charts and Visualizations
- **Metric trends**: Historical charts (last 24 hours)
- **Error rates**: Log error frequency over time
- **Alert timeline**: When alerts were triggered

## Logs Page

**Features:**
- Upload log files or paste content
- Select log format (JSON, syslog, custom)
- Filter by log level
- Search with regex patterns
- View error summaries
- Download filtered results
- AI-powered analysis

**Actions:**
- Analyze logs
- Generate diagnoses
- Create fixes
- Export results

## Metrics Page

**Features:**
- Detailed metric charts
- Customizable time ranges
- Per-process breakdowns
- Resource usage trends
- Anomaly highlights
- Export metric data

**Metrics tracked:**
- CPU per core
- Memory breakdown (used, cached, buffers)
- Disk I/O rates
- Network traffic by interface
- Process details (top consumers)

## Fixes & PRs Page

**Features:**
- List of all generated fixes
- Fix details and code changes
- Validation status
- Application tracking
- PR status and links
- Rollback capability

**Actions:**
- View fix details
- Apply fixes
- Create pull requests
- Rollback changes
- Download fix patches

## Help Page

**Features:**
- Searchable help articles
- Category browsing
- Featured articles
- View count tracking
- Helpful/not helpful feedback
- Related articles

## Navigation

Use the top navigation bar to switch between pages:
- **Dashboard**: System overview
- **Logs**: Log analysis
- **Metrics**: Detailed metrics
- **Fixes & PRs**: Fix management
- **Help**: Documentation

## Auto-Refresh

Most pages auto-refresh to show latest data:
- **Dashboard**: Every 5 seconds
- **Metrics**: Every 10 seconds
- **Logs**: Manual refresh
- **Fixes**: Every 30 seconds

## Responsive Design

The dashboard is fully responsive and works on:
- Desktop computers
- Tablets
- Mobile devices

## Keyboard Shortcuts

- **`/`**: Focus search (on Help page)
- **`Esc`**: Clear search/close modals
- **`r`**: Refresh current page data

## Customization

Future versions will support:
- Custom dashboard layouts
- Widget configuration
- Color themes
- Alert preferences
""",
        "tags": ["dashboard", "ui", "features", "interface"],
        "icon": "layout-dashboard",
        "featured": False,
        "order": 6,
    },
    {
        "title": "Metrics Collection and Storage",
        "slug": "metrics-collection",
        "category": "Monitoring",
        "summary": "How Plant collects, stores, and manages system metrics data.",
        "content": """# Metrics Collection and Storage

Understanding how Plant gathers and stores system metrics.

## Collection Methods

### Automatic Collection

Plant automatically collects metrics at regular intervals:

- **Default interval**: Every 60 seconds
- **Configurable**: Set `metrics_interval` in settings
- **Background task**: Runs continuously after startup

### Manual Collection

Trigger metric collection on-demand:

```bash
GET /metrics/current
```

### Detailed Collection

Get extended metrics including per-process data:

```bash
GET /metrics/detailed
```

## Metrics Collected

### System-Level Metrics

**CPU:**
- Overall percentage
- Per-core usage
- Load average (1m, 5m, 15m)

**Memory:**
- Total, used, available
- Percentage used
- Swap usage

**Disk:**
- Total, used, free space
- Usage percentage
- I/O operations

**Network:**
- Bytes sent/received
- Packets sent/received
- Error counts

**Processes:**
- Total process count
- Top processes by CPU
- Top processes by memory

### Application-Level Metrics

**API:**
- Request counts
- Response times
- Error rates

**Database:**
- Query counts
- Connection pool stats
- Query performance

## Storage

### In-Memory History

Plant maintains recent metrics in memory:

- **Retention**: Last 1000 data points
- **Purpose**: Quick access for charts and anomaly detection
- **Access**: Via `/metrics/history` endpoint

### Database Persistence

Historical metrics are stored in the database:

- **Model**: `MetricsSnapshot`
- **Retention**: Configurable (default: 90 days)
- **Cleanup**: Automatic via retention policy
- **Indexing**: Optimized for time-series queries

## Data Structure

Metrics are stored as:

```python
{
  "timestamp": "2024-01-15T10:30:00Z",
  "cpu_percent": 45.2,
  "memory_percent": 62.5,
  "memory_available_mb": 4096,
  "disk_usage_percent": 55.0,
  "disk_free_gb": 100.5,
  "network_bytes_sent": 1048576,
  "network_bytes_recv": 2097152,
  "process_count": 125,
  "load_average": [1.5, 1.3, 1.2]
}
```

## Querying Metrics

### Recent Metrics

```bash
GET /metrics/history?limit=100
```

### Time Range

```bash
GET /api/database/metrics/range?start=2024-01-01&end=2024-01-31
```

### Averages

```bash
GET /api/database/metrics/averages?hours=24
```

### Anomalies

```bash
GET /api/database/metrics/anomalies?days=7
```

## Data Retention

Configure retention policies:

```python
# config.yaml
data_retention:
  metrics_days: 90
  analysis_runs_days: 365
  alerts_days: 180
```

Automatic cleanup runs daily to remove old data.

## Performance Optimization

Plant optimizes metrics storage:

- **Sampling**: Reduce resolution for old data
- **Aggregation**: Pre-compute hourly/daily averages
- **Compression**: Efficient storage format
- **Indexing**: Fast time-based queries

## Export Options

Export metrics data:

- **CSV**: Download from Metrics page
- **JSON**: Via API endpoints
- **Prometheus**: Metrics endpoint (future)
- **Grafana**: Direct integration (future)

## Custom Metrics

Add custom application metrics:

```python
from src.collectors.metrics_collector import MetricsCollector

collector = MetricsCollector()
collector.add_custom_metric("app_requests", 1523)
collector.add_custom_metric("app_errors", 3)
```

## Best Practices

1. **Adjust intervals**: Balance detail vs. storage
2. **Monitor storage**: Check database size regularly
3. **Set retention**: Keep only what's needed
4. **Use averages**: For long-term trend analysis
5. **Export important data**: Before retention cleanup
""",
        "tags": ["metrics", "collection", "storage", "performance"],
        "icon": "database",
        "featured": False,
        "order": 7,
    },
    {
        "title": "Troubleshooting Common Issues",
        "slug": "troubleshooting",
        "category": "Help",
        "summary": "Solutions to common problems and issues you might encounter with Plant.",
        "content": """# Troubleshooting Common Issues

Solutions to frequently encountered problems.

## API Issues

### API Won't Start

**Problem**: FastAPI server fails to start

**Solutions:**
1. Check port 8000 is not in use: `lsof -i :8000`
2. Verify Python version: `python --version` (need 3.10+)
3. Install dependencies: `pip install -r requirements.txt`
4. Check database connection
5. Review error logs in console

### Connection Refused

**Problem**: Can't connect to API at localhost:8000

**Solutions:**
1. Ensure API is running: `ps aux | grep uvicorn`
2. Check firewall settings
3. Try 127.0.0.1 instead of localhost
4. Verify CORS settings in main.py
5. Check if running in correct environment

## Database Issues

### Migration Errors

**Problem**: Database schema migration fails

**Solutions:**
1. Check database connection string
2. Ensure database exists
3. Drop and recreate tables (dev only!)
4. Check SQLAlchemy version compatibility
5. Review migration logs

### Connection Pool Exhausted

**Problem**: "Too many connections" error

**Solutions:**
1. Increase pool size in config
2. Check for connection leaks
3. Ensure sessions are closed properly
4. Restart API server
5. Review concurrent request load

## Metrics Collection

### No Metrics Data

**Problem**: Metrics page shows no data

**Solutions:**
1. Trigger manual collection: `GET /metrics/current`
2. Check background task is running
3. Verify metrics_interval in config
4. Check for collection errors in logs
5. Ensure psutil is installed correctly

### High Memory Usage

**Problem**: Plant consuming too much memory

**Solutions:**
1. Reduce metrics history limit
2. Decrease collection interval
3. Enable database cleanup
4. Check for memory leaks in logs
5. Restart API service

## Log Analysis

### Log Parsing Fails

**Problem**: Logs not parsing correctly

**Solutions:**
1. Verify log format selection
2. Check for encoding issues (use UTF-8)
3. Try custom format with regex
4. Validate log file is not corrupted
5. Check file permissions

### AI Analysis Timeout

**Problem**: AI analysis takes too long or times out

**Solutions:**
1. Reduce log file size
2. Filter logs before analysis
3. Increase timeout in config
4. Check LLM API status
5. Use batch processing for large files

## Notification Issues

### Alerts Not Sending

**Problem**: Configured alerts not being delivered

**Solutions:**
1. Test channel: `POST /notifications/channels/{name}/test`
2. Verify channel is enabled
3. Check webhook URLs are correct
4. Review alert rules configuration
5. Check notification logs for errors

### Slack Webhook Fails

**Problem**: Slack notifications not working

**Solutions:**
1. Verify webhook URL is correct
2. Check Slack app permissions
3. Test with curl directly
4. Review Slack API status
5. Check for rate limiting

## UI Issues

### Dashboard Not Loading

**Problem**: Web dashboard won't load

**Solutions:**
1. Check if Vite dev server is running
2. Clear browser cache
3. Check console for errors (F12)
4. Verify API is accessible
5. Try incognito/private mode

### Charts Not Displaying

**Problem**: Metrics charts empty or not rendering

**Solutions:**
1. Check browser console for errors
2. Verify Recharts is installed: `npm list recharts`
3. Ensure metrics data is available
4. Check API CORS settings
5. Try different browser

## Performance Issues

### Slow API Responses

**Problem**: API endpoints responding slowly

**Solutions:**
1. Check database query performance
2. Enable Redis caching
3. Reduce data returned in queries
4. Add database indexes
5. Monitor system resources

### High CPU Usage

**Problem**: Plant using excessive CPU

**Solutions:**
1. Reduce metrics collection frequency
2. Disable background tasks temporarily
3. Check for infinite loops in logs
4. Optimize database queries
5. Scale vertically if needed

## Installation Issues

### Dependency Conflicts

**Problem**: pip install fails with conflicts

**Solutions:**
1. Use virtual environment: `python -m venv venv`
2. Upgrade pip: `pip install --upgrade pip`
3. Install dependencies one at a time
4. Check Python version compatibility
5. Use `pip install --no-deps` if needed

### Missing Dependencies

**Problem**: Import errors for modules

**Solutions:**
1. Install all requirements: `pip install -r requirements.txt`
2. Check virtual environment is activated
3. Verify Python path
4. Install missing package directly
5. Check for typos in imports

## Getting More Help

If issues persist:

1. **Check logs**: Review application logs for errors
2. **Enable debug mode**: Set `debug: true` in config
3. **GitHub issues**: Report bugs or ask questions
4. **Documentation**: Review relevant help articles
5. **API docs**: Check interactive docs at /docs
""",
        "tags": ["troubleshooting", "help", "issues", "errors", "debugging"],
        "icon": "help-circle",
        "featured": False,
        "order": 8,
    },
    {
        "title": "Security Best Practices",
        "slug": "security-practices",
        "category": "Security",
        "summary": "Important security considerations and best practices when using Plant.",
        "content": """# Security Best Practices

Ensure your Plant deployment is secure and protected.

## Authentication

### Enable JWT Authentication

For production deployments, enable JWT authentication:

```python
# config.yaml
security:
  jwt_enabled: true
  jwt_secret: "your-secret-key"  # Use strong random key
  jwt_expiration: 3600  # 1 hour
```

### API Key Management

Use API keys for programmatic access:

1. Generate keys: `POST /auth/api-keys`
2. Scope permissions appropriately
3. Rotate keys regularly
4. Revoke unused keys
5. Never commit keys to version control

### OAuth 2.0

Enable OAuth for user authentication:

- **Google**: Configure client ID and secret
- **GitHub**: Set up OAuth app
- **Microsoft**: Register application

## Network Security

### HTTPS/TLS

Always use HTTPS in production:

1. Obtain SSL certificate (Let's Encrypt)
2. Configure reverse proxy (nginx/Apache)
3. Redirect HTTP to HTTPS
4. Enable HSTS headers
5. Use strong cipher suites

### CORS Configuration

Restrict CORS to trusted origins:

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Not "*"
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization"],
)
```

### Firewall Rules

Configure firewall to:

- Allow only necessary ports
- Restrict API access to known IPs
- Block suspicious traffic
- Enable DDoS protection

## Data Security

### Sensitive Data

Protect sensitive information:

1. **Secrets**: Use environment variables or vault
2. **Logs**: Redact sensitive data automatically
3. **API responses**: Don't expose internal details
4. **Database**: Encrypt sensitive columns
5. **Backups**: Encrypt backup files

### Secrets Management

Use proper secrets management:

**Development:**
- Use `.env` files (gitignored)
- Local environment variables

**Production:**
- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- Kubernetes Secrets

### Database Security

Secure your database:

1. **Authentication**: Strong passwords
2. **Network**: Restrict to application only
3. **Encryption**: Enable at rest and in transit
4. **Backups**: Regular encrypted backups
5. **Access**: Principle of least privilege

## Input Validation

Plant includes protection against:

### SQL Injection
- SQLAlchemy ORM prevents SQL injection
- Never use raw SQL with user input
- Parameterize all queries

### XSS Prevention
- Input sanitization with bleach
- Output encoding
- Content Security Policy headers

### Command Injection
- No shell=True in subprocess calls
- Whitelist allowed commands
- Validate all file paths

## Rate Limiting

Prevent abuse with rate limiting:

```python
# config.yaml
rate_limiting:
  enabled: true
  default_limit: "100/minute"
  burst_limit: 200
```

Limits apply per:
- IP address
- API key
- User account

## Monitoring and Auditing

### Security Monitoring

Monitor for:
- Failed authentication attempts
- Unusual API usage patterns
- Unauthorized access attempts
- Configuration changes
- Data exports

### Audit Logging

Enable comprehensive audit logs:

```python
# config.yaml
auditing:
  enabled: true
  log_auth: true
  log_data_access: true
  log_config_changes: true
```

Audit logs include:
- User/API key identification
- Timestamp
- Action performed
- Resource accessed
- Result (success/failure)

## Dependency Security

Keep dependencies secure:

### Regular Updates

```bash
# Check for vulnerabilities
pip-audit

# Update dependencies
pip install --upgrade -r requirements.txt
```

### Vulnerability Scanning

Use tools like:
- `pip-audit` for Python packages
- `npm audit` for Node packages
- Snyk for continuous monitoring
- GitHub Dependabot

## Deployment Security

### Docker Security

When using Docker:

1. Use official base images
2. Run as non-root user
3. Scan images for vulnerabilities
4. Minimize image size
5. Use specific tags, not `latest`

### Kubernetes Security

When deploying to Kubernetes:

1. Use NetworkPolicies
2. Enable RBAC
3. Use Pod Security Standards
4. Encrypt secrets
5. Regular security audits

### Environment Separation

Maintain separate environments:

- **Development**: Local, unrestricted
- **Staging**: Production-like, test security
- **Production**: Fully hardened, monitored

## Incident Response

Prepare for security incidents:

1. **Detection**: Monitor logs and metrics
2. **Containment**: Automated response rules
3. **Investigation**: Audit trail review
4. **Recovery**: Backup restoration
5. **Prevention**: Update security controls

## Compliance

Consider compliance requirements:

- **GDPR**: Data privacy and retention
- **HIPAA**: Healthcare data protection
- **SOC 2**: Security controls
- **PCI DSS**: Payment data security

## Security Checklist

Before production deployment:

- [ ] Enable authentication (JWT/OAuth)
- [ ] Configure HTTPS/TLS
- [ ] Restrict CORS origins
- [ ] Use strong secrets
- [ ] Enable rate limiting
- [ ] Set up audit logging
- [ ] Configure firewall rules
- [ ] Scan for vulnerabilities
- [ ] Encrypt sensitive data
- [ ] Regular backup schedule
- [ ] Incident response plan
- [ ] Security monitoring alerts

## Reporting Security Issues

Found a security vulnerability?

1. **Do not** create public GitHub issue
2. Email security concerns privately
3. Include detailed reproduction steps
4. Allow time for fix before disclosure
5. Coordinate disclosure timeline
""",
        "tags": ["security", "authentication", "encryption", "best-practices"],
        "icon": "shield",
        "featured": False,
        "order": 9,
    },
    {
        "title": "Auto-Fix and Code Generation",
        "slug": "auto-fix",
        "category": "Advanced",
        "summary": "How Plant's AI-powered auto-fix feature generates and applies code fixes.",
        "content": """# Auto-Fix and Code Generation

Plant can automatically generate fixes for detected issues using AI.

## How It Works

### 1. Issue Detection

Plant first detects issues through:
- Log analysis
- Anomaly detection
- Resource monitoring
- Error pattern matching

### 2. AI Diagnosis

The AI analyzes the issue to determine:
- **Root cause**: What's causing the problem
- **Severity**: How critical is it
- **Impact**: What's affected
- **Category**: Type of issue (config, code, resource)

### 3. Fix Generation

Based on the diagnosis, Plant generates:
- **Code changes**: Modified files
- **Configuration updates**: Config file changes
- **Scripts**: Automation scripts
- **Test commands**: Validation steps

### 4. Validation

Before applying, fixes are:
- Syntax checked
- Tested (if tests provided)
- Reviewed for safety
- Validated against codebase

### 5. Application

Fixes can be:
- Reviewed manually
- Applied automatically
- Turned into pull requests
- Rolled back if needed

## Enabling Auto-Fix

### Via API Request

```bash
POST /analyze
{
  "log_content": "...",
  "include_ai_analysis": true,
  "auto_fix": true,
  "auto_pr": false
}
```

### Via Configuration

```python
# config.yaml
auto_fix_enabled: true
auto_pr_enabled: false  # Manual PR creation
```

## Types of Fixes

### Configuration Fixes

Changes to configuration files:

```yaml
# Before
max_connections: 10

# After (AI-generated)
max_connections: 50  # Increased based on usage patterns
```

### Code Fixes

Bug fixes and optimizations:

```python
# Before
def process_data(data):
    return data.split(",")  # Fails on None

# After (AI-generated)
def process_data(data):
    if data is None:
        return []
    return data.split(",")
```

### Resource Fixes

System resource optimizations:

```python
# Before
workers: 2

# After (AI-generated)
workers: 4  # Based on CPU cores and load
```

### Dependency Fixes

Package version updates:

```
# Before
requests==2.25.0  # Has security vulnerability

# After (AI-generated)
requests>=2.31.0  # Security patch
```

## Fix Structure

Each fix includes:

```python
{
  "fix_id": "fix_abc123",
  "diagnosis_id": "diag_xyz789",
  "fix_type": "code_change",
  "title": "Fix null pointer in data processing",
  "description": "Add null check before split operation",
  "file_changes": {
    "src/processors/data.py": "... new content ..."
  },
  "test_commands": [
    "pytest tests/test_processors.py"
  ],
  "validation_passed": true
}
```

## Reviewing Fixes

### Via Web Dashboard

1. Navigate to **Fixes & PRs** page
2. View fix details
3. Review code changes (diff view)
4. Check validation status
5. Apply or reject

### Via API

```bash
# Get fix details
GET /api/database/fixes/{fix_id}

# Apply fix
POST /api/fixes/{fix_id}/apply

# Rollback fix
POST /api/fixes/{fix_id}/rollback
```

## Pull Request Creation

### Automatic PR Creation

Enable automatic PRs:

```python
# config.yaml
auto_pr_enabled: true
github_token: "your-github-token"
```

Plant will:
1. Create new branch
2. Commit changes
3. Create pull request
4. Add description with diagnosis
5. Link related issues

### Manual PR Creation

```bash
POST /api/fixes/{fix_id}/create-pr
{
  "branch_name": "fix/null-pointer",
  "target_branch": "main"
}
```

## Safety Features

### Validation

All fixes are validated:
- Syntax checking
- Test execution
- Impact analysis
- Security scanning

### Rollback

Undo applied fixes:

```bash
POST /api/fixes/{fix_id}/rollback
```

Rollback:
- Restores previous code
- Updates fix status
- Logs rollback action
- Notifies team

### Manual Review

Critical fixes require manual review:
- Breaking changes
- Security-related fixes
- Database migrations
- Production configs

## Best Practices

### 1. Start with Manual Review

Don't enable auto-apply immediately:
- Review generated fixes first
- Build confidence in AI accuracy
- Understand fix patterns
- Gradually increase automation

### 2. Use Version Control

Always use git:
- Easy rollback
- Change history
- Code review process
- Collaboration

### 3. Test Thoroughly

Run tests before and after:
- Unit tests
- Integration tests
- Manual testing
- Performance tests

### 4. Monitor Results

Track fix effectiveness:
- Did it solve the issue?
- Did new issues appear?
- Performance impact?
- User feedback?

### 5. Provide Feedback

Help improve AI:
- Mark fixes as helpful/not helpful
- Report issues
- Suggest improvements
- Share success stories

## Limitations

Be aware of limitations:

### What It Can Fix
- Common bugs and errors
- Configuration issues
- Resource problems
- Known vulnerabilities

### What It Cannot Fix
- Complex architectural issues
- Business logic bugs requiring domain knowledge
- Hardware failures
- Third-party service outages

## Configuration Options

Customize auto-fix behavior:

```python
# config.yaml
auto_fix:
  enabled: true
  auto_apply: false  # Require manual approval
  max_files_per_fix: 5  # Limit scope
  require_tests: true  # Must have test commands
  exclude_patterns:
    - "*/migrations/*"
    - "*.sql"
  allowed_fix_types:
    - "code_change"
    - "config_update"
  # - "dependency_update"  # Disabled
```

## Advanced Usage

### Custom Fix Templates

Provide fix templates for common issues:

```python
FIX_TEMPLATES = {
  "null_pointer": {
    "pattern": r"NoneType.*has no attribute",
    "fix_template": "Add null check before accessing {attribute}"
  }
}
```

### Fix Hooks

Run custom logic during fix lifecycle:

```python
# Pre-apply hook
@fix_manager.on_pre_apply
def validate_fix(fix):
    # Custom validation
    pass

# Post-apply hook
@fix_manager.on_post_apply
def notify_team(fix):
    # Send notification
    pass
```

## Troubleshooting

### Fix Generation Fails

If fix generation fails:
1. Check LLM API is accessible
2. Verify API quota/limits
3. Review error logs
4. Try simpler issues first
5. Check diagnosis quality

### Fix Doesn't Apply

If applying fix fails:
1. Check file permissions
2. Verify paths are correct
3. Ensure no conflicts with local changes
4. Check git status
5. Review validation errors
""",
        "tags": ["auto-fix", "ai", "code-generation", "automation"],
        "icon": "wand",
        "featured": False,
        "order": 10,
    },
]


async def seed_help_articles():
    """Seed the database with help articles."""
    # Ensure database exists and tables are created
    print("Initializing database...")
    await init_db()
    print("Database initialized!")

    print("\nSeeding help articles...")

    async with get_db_session() as session:
        try:
            repo = HelpArticleRepository(session)

            for article_data in HELP_ARTICLES:
                # Check if article already exists
                existing = await repo.get_by_slug(article_data["slug"])
                if existing:
                    print(f"  ⏭️  Skipping existing article: {article_data['title']}")
                    continue

                # Create article
                article = await repo.create(article_data)
                print(f"  ✅ Created: {article_data['title']} (category: {article_data['category']})")

            # Commit all changes
            await session.commit()
            print(f"\n✅ Successfully seeded {len(HELP_ARTICLES)} help articles!")

        except Exception as e:
            print(f"\n❌ Error seeding articles: {e}")
            await session.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(seed_help_articles())
