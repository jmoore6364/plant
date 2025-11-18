# Notification & Alerting System

Complete guide to the Plant AI notification and alerting system.

## Overview

The notification system provides **real-time alerts** through multiple channels when issues are detected. It includes:

- **Multi-Channel Support**: Slack, Discord, Email, PagerDuty
- **Smart Alert Rules**: Configurable thresholds and conditions
- **Deduplication**: Prevents alert spam
- **Alert Grouping**: Groups related alerts together
- **Priority Levels**: LOW, MEDIUM, HIGH, CRITICAL
- **Auto-Recovery**: Resolves alerts when issues are fixed

## Quick Start

### 1. Configure Channels

Edit your `.env` file:

```bash
# Enable notifications
NOTIFICATIONS_ENABLED=true

# Slack (choose webhook OR API token)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR/WEBHOOK/URL

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TO_EMAILS=admin@company.com,ops@company.com

# PagerDuty (for critical incidents only)
PAGERDUTY_INTEGRATION_KEY=your_integration_key
```

### 2. Test Channels

```python
from src.notifications.setup import get_notification_manager

manager = get_notification_manager()

# Test all configured channels
results = manager.test_all_channels()
print(results)  # {'slack': True, 'discord': True, ...}
```

### 3. Send Your First Alert

```python
from src.notifications.base import Alert, NotificationPriority
from src.notifications.setup import get_notification_manager

manager = get_notification_manager()

alert = Alert(
    id="test_001",
    title="Test Alert",
    message="This is a test notification",
    priority=NotificationPriority.MEDIUM,
    source="manual_test",
)

# Send to all enabled channels
import asyncio
results = asyncio.run(manager.send_alert(alert))

# Or send to specific channels only
results = asyncio.run(manager.send_alert(alert, channels=["slack"]))
```

## Channels

### Slack

**Setup Options:**

1. **Webhook URL** (Easiest):
   - Go to https://api.slack.com/apps
   - Create new app → Incoming Webhooks
   - Add to workspace and copy webhook URL

2. **API Token** (Advanced features):
   - Create app → OAuth & Permissions
   - Add `chat:write` scope
   - Install to workspace and copy Bot Token

**Configuration:**

```bash
# Option 1: Webhook
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ

# Option 2: API Token (allows channel selection)
SLACK_API_TOKEN=xoxb-your-token-here
SLACK_CHANNEL=#alerts  # or @username
```

**Features:**
- Rich message formatting with colored attachments
- Severity-based colors (green → red)
- Metadata displayed as fields
- Timestamps and footer

### Discord

**Setup:**

1. Open Discord server settings
2. Integrations → Webhooks → New Webhook
3. Choose channel, copy webhook URL

**Configuration:**

```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
```

**Features:**
- Rich embeds with colors
- Structured fields for metadata
- Supports inline fields for compact display

### Email (SMTP)

**Setup:**

For Gmail:
1. Enable 2FA on your Google account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Use app password in config

**Configuration:**

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587  # or 465 for SSL
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # NOT your regular password
SMTP_FROM_EMAIL=Plant AI <noreply@company.com>
SMTP_TO_EMAILS=admin@company.com,ops@company.com,team@company.com
```

**Features:**
- HTML and plain text versions
- Color-coded by priority
- Professional email templates
- Metadata in formatted tables

**Other SMTP Providers:**

```bash
# SendGrid
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your_sendgrid_api_key

# Mailgun
SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@yourdomain.mailgun.org
SMTP_PASSWORD=your_mailgun_password

# AWS SES
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USER=your_smtp_username
SMTP_PASSWORD=your_smtp_password
```

### PagerDuty

**Setup:**

1. Log in to PagerDuty
2. Services → Select service → Integrations
3. Add Integration → Events API v2
4. Copy Integration Key

**Configuration:**

```bash
PAGERDUTY_INTEGRATION_KEY=your_32_character_key
```

**Features:**
- Automatic incident creation
- Only sends HIGH and CRITICAL alerts
- Deduplication using alert fingerprints
- Can programmatically resolve incidents
- Integrates with on-call rotations

**Usage:**

```python
# Incidents are automatically created for critical issues
# To manually resolve an incident:
manager = get_notification_manager()
pagerduty = manager.channels['pagerduty']
await pagerduty.resolve('dedup_key_here')
```

## Alert Rules

### Built-in Rules

The system includes default rules for common issues:

| Rule Name | Trigger | Priority | Cooldown |
|-----------|---------|----------|----------|
| `high_cpu_usage` | CPU ≥ 90% | HIGH | 15 min |
| `critical_cpu_usage` | CPU ≥ 95% | CRITICAL | 5 min |
| `high_memory_usage` | Memory ≥ 85% | HIGH | 15 min |
| `low_disk_space` | Disk ≥ 90% | HIGH | 15 min |
| `critical_disk_space` | Disk ≥ 95% | CRITICAL | 10 min |
| `error_logs` | 5+ errors in 5 min | MEDIUM | 10 min |
| `critical_logs` | Any CRITICAL log | CRITICAL | 5 min |

### Creating Custom Rules

```python
from src.notifications.rules import AlertRule
from src.notifications.base import NotificationPriority
from src.models.schemas import LogLevel

# Metric-based rule
custom_rule = AlertRule(
    name="very_high_memory",
    description="Memory usage above 95%",
    metric_type="memory",
    threshold=95.0,
    comparison=">=",
    priority=NotificationPriority.CRITICAL,
    cooldown_minutes=5,
    tags=["performance", "memory", "critical"],
)

manager.rule_engine.add_rule(custom_rule)

# Log-based rule
log_rule = AlertRule(
    name="auth_failures",
    description="Multiple authentication failures",
    log_level=LogLevel.WARNING,
    log_pattern=r"authentication.*failed",
    occurrence_count=10,
    time_window_minutes=5,
    priority=NotificationPriority.HIGH,
    cooldown_minutes=10,
    tags=["security", "auth"],
)

manager.rule_engine.add_rule(log_rule)
```

### Managing Rules via API

```bash
# List all rules
curl http://localhost:8000/notifications/rules

# Enable a rule
curl -X POST http://localhost:8000/notifications/rules/high_cpu_usage/enable

# Disable a rule
curl -X POST http://localhost:8000/notifications/rules/high_cpu_usage/disable
```

## Deduplication

Prevents alert spam by detecting duplicate alerts within a time window.

**How it Works:**

1. Each alert gets a **fingerprint** (default: hash of title + source + priority)
2. If same fingerprint seen within window → **deduplicated**
3. Default window: **15 minutes**

**Configure Deduplication:**

```bash
ALERT_DEDUP_WINDOW_MINUTES=15  # Adjust as needed
```

**Custom Fingerprints:**

```python
# Use custom fingerprint for better deduplication
alert = Alert(
    id="alert_1",
    title="High CPU",
    message="CPU at 92%",
    priority=NotificationPriority.HIGH,
    source="metrics",
    fingerprint="cpu_high",  # All "cpu_high" alerts deduplicated together
)
```

## Alert Grouping

Group related alerts together for better organization.

**Example:**

```python
# All these alerts will be grouped
cpu_alert_1 = Alert(
    id="cpu_1",
    title="CPU Spike",
    message="CPU at 92%",
    priority=NotificationPriority.HIGH,
    source="metrics",
    group_key="performance_issues",  # Grouping key
)

memory_alert = Alert(
    id="mem_1",
    title="Memory High",
    message="Memory at 88%",
    priority=NotificationPriority.HIGH,
    source="metrics",
    group_key="performance_issues",  # Same group
)

# Get all alerts in a group
grouped = manager.deduplicator.get_grouped_alerts("performance_issues")
```

## Priority Levels

Alerts have 4 priority levels that determine routing and formatting:

| Priority | Color | PagerDuty | Use Case |
|----------|-------|-----------|----------|
| **LOW** | 🟢 Green | ❌ No | Info, FYI items |
| **MEDIUM** | 🟡 Yellow | ❌ No | Warnings, non-urgent issues |
| **HIGH** | 🔴 Red | ✅ Yes | Errors, urgent attention needed |
| **CRITICAL** | 🔴 Dark Red | ✅ Yes | System down, data loss, security |

**Setting Priority:**

```python
from src.notifications.base import NotificationPriority

alert = Alert(
    id="critical_001",
    title="Database Down",
    message="Cannot connect to primary database",
    priority=NotificationPriority.CRITICAL,  # 🚨
    source="health_check",
)
```

## API Endpoints

### Send Custom Alert

```bash
curl -X POST http://localhost:8000/notifications/send \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Deployment Started",
    "message": "Version 2.0.1 deploying to production",
    "priority": "medium",
    "source": "ci_cd"
  }'
```

### Get Channel Status

```bash
curl http://localhost:8000/notifications/channels
```

Response:
```json
{
  "channels": {
    "slack": {"enabled": true, "type": "slack"},
    "discord": {"enabled": true, "type": "discord"},
    "email": {"enabled": true, "type": "email"}
  },
  "count": 3
}
```

### Test a Channel

```bash
curl -X POST http://localhost:8000/notifications/channels/slack/test
```

### Enable/Disable Channels

```bash
# Disable
curl -X POST http://localhost:8000/notifications/channels/slack/disable

# Enable
curl -X POST http://localhost:8000/notifications/channels/slack/enable
```

### Get Alert Summary

```bash
# Last 24 hours (default)
curl http://localhost:8000/notifications/summary

# Last 7 days
curl http://localhost:8000/notifications/summary?hours=168
```

Response:
```json
{
  "time_window_hours": 24,
  "total_alerts": 15,
  "by_priority": {
    "high": 5,
    "medium": 8,
    "critical": 2
  },
  "by_source": {
    "metrics": 10,
    "logs": 3,
    "anomaly_detector": 2
  },
  "notifications_sent": 15,
  "success_rate": "93.3%"
}
```

## Integration Examples

### With Metrics Monitoring

```python
from src.collectors.metrics_collector import MetricsCollector
from src.notifications.setup import get_notification_manager

collector = MetricsCollector()
manager = get_notification_manager()

# Collect and check metrics
metrics = collector.collect()
results = await manager.process_metrics(metrics)

# Alerts automatically sent if thresholds exceeded
```

### With Log Analysis

```python
from src.collectors.log_collector import LogCollector
from src.notifications.setup import get_notification_manager

collector = LogCollector()
logs = collector.parse_file("/var/log/app.log")

manager = get_notification_manager()
results = await manager.process_logs(logs)

# Alerts sent for error patterns
```

### With Anomaly Detection

```python
from src.analyzers.anomaly_detector import AnomalyDetector
from src.notifications.setup import get_notification_manager

detector = AnomalyDetector()
anomaly = detector.classify_anomaly(metrics, score)

manager = get_notification_manager()
results = await manager.process_anomaly(anomaly)

# Alert sent for detected anomaly
```

## Best Practices

### 1. Choose Appropriate Priorities

```python
# ✅ Good
Alert(title="Disk at 92%", priority=NotificationPriority.HIGH)
Alert(title="User logged in", priority=NotificationPriority.LOW)

# ❌ Bad
Alert(title="Debug log entry", priority=NotificationPriority.CRITICAL)
```

### 2. Use Meaningful Fingerprints

```python
# ✅ Good - specific to issue type
fingerprint="db_connection_failure"
fingerprint=f"cpu_high_{server_name}"

# ❌ Bad - too generic, won't deduplicate well
fingerprint="error"
```

### 3. Set Appropriate Cooldowns

```python
# For frequently changing metrics
AlertRule(name="cpu", cooldown_minutes=5)

# For slower-changing metrics
AlertRule(name="disk_space", cooldown_minutes=30)
```

### 4. Tag Your Alerts

```python
alert = Alert(
    title="API Slow",
    message="Response time > 5s",
    priority=NotificationPriority.HIGH,
    tags=["performance", "api", "latency"],  # Useful for filtering
)
```

### 5. Include Actionable Metadata

```python
alert = Alert(
    title="High Memory Usage",
    message="Memory at 95%",
    priority=NotificationPriority.HIGH,
    metadata={
        "current_usage": "95%",
        "threshold": "85%",
        "server": "prod-web-01",
        "action_needed": "Restart or scale up",
        "runbook": "https://docs.company.com/runbooks/high-memory",
    },
)
```

## Troubleshooting

### Alerts Not Sending

1. **Check if notifications enabled:**
   ```bash
   # In .env
   NOTIFICATIONS_ENABLED=true
   ```

2. **Verify channel configuration:**
   ```python
   manager = get_notification_manager()
   print(manager.get_channel_status())
   ```

3. **Test channel connectivity:**
   ```python
   results = manager.test_all_channels()
   print(results)
   ```

### Slack Not Working

- Verify webhook URL is correct
- Check workspace permissions
- Test with curl:
  ```bash
  curl -X POST YOUR_WEBHOOK_URL \
    -H 'Content-Type: application/json' \
    -d '{"text": "Test message"}'
  ```

### Email Not Sending

- For Gmail: Use App Password, not regular password
- Check firewall allows SMTP ports (587, 465)
- Verify SMTP credentials
- Check spam folder

### Too Many Alerts

1. **Increase cooldown:**
   ```bash
   ALERT_COOLDOWN_MINUTES=30
   ```

2. **Increase dedup window:**
   ```bash
   ALERT_DEDUP_WINDOW_MINUTES=30
   ```

3. **Adjust thresholds:**
   ```python
   # Make rules less sensitive
   rule.threshold = 95.0  # instead of 90.0
   ```

4. **Disable noisy rules:**
   ```python
   manager.rule_engine.disable_rule("error_logs")
   ```

## Advanced Usage

### Custom Notification Templates

```python
from src.notifications.base import NotificationTemplate

template = NotificationTemplate(
    name="deployment",
    subject_template="[{priority}] Deployment: {title}",
    body_template="""
Deployment Alert: {title}

{message}

Environment: {environment}
Version: {version}
Deployed by: {deployer}
    """,
    format="markdown",
)

# Use in alert metadata
alert = Alert(
    title="Production Deployment",
    message="Deploying v2.0.1",
    metadata={
        "environment": "production",
        "version": "2.0.1",
        "deployer": "Alice",
    },
)
```

### Conditional Channel Routing

```python
# Send critical alerts to PagerDuty, others to Slack
def route_alert(alert):
    if alert.priority == NotificationPriority.CRITICAL:
        return ["pagerduty", "slack"]
    elif alert.priority == NotificationPriority.HIGH:
        return ["slack", "email"]
    else:
        return ["slack"]

channels = route_alert(my_alert)
results = await manager.send_alert(my_alert, channels=channels)
```

### Programmatic Rule Management

```python
# Temporarily disable all rules
for rule_name in manager.rule_engine.rules:
    manager.rule_engine.disable_rule(rule_name)

# During maintenance window
manager.disable_channel("pagerduty")

# After maintenance
manager.enable_channel("pagerduty")
for rule_name in manager.rule_engine.rules:
    manager.rule_engine.enable_rule(rule_name)
```

## Next Steps

- Set up at least one notification channel
- Test with a sample alert
- Configure alert thresholds for your environment
- Set up PagerDuty for critical incidents
- Create custom rules for your specific use cases
- Integrate into CI/CD for deployment notifications

For more help, see:
- [Main README](../README.md)
- [Setup Guide](../SETUP.md)
- [API Documentation](http://localhost:8000/docs)
