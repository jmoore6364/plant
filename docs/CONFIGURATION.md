# Configuration Guide

Comprehensive guide to configuring the System Health Analyzer.

## Configuration Methods

The application supports multiple configuration methods (in order of precedence):

1. **Environment Variables** (highest priority)
2. **Configuration Files** (YAML/TOML)
3. **Default Values** (lowest priority)

## Configuration Files

### File Locations

The application looks for configuration files in this order:

1. Path specified in `CONFIG_FILE` environment variable
2. `config.yaml`
3. `config.yml`
4. `config.toml`
5. `config/app.yaml`
6. `config/app.yml`
7. `config/app.toml`

### YAML Configuration

```yaml
# config/config.yaml
environment: production
debug: false

database:
  url: "postgresql+asyncpg://user:pass@localhost/db"
  pool_size: 20
  max_overflow: 40
  pool_timeout: 30
  echo: false

ai:
  provider: "anthropic"  # or "openai"
  anthropic_api_key: "${secret:ai/anthropic_api_key}"
  openai_api_key: "${secret:ai/openai_api_key}"
  model: "claude-3-sonnet-20240229"
  max_tokens: 4096
  temperature: 0.7
  timeout: 120

api:
  host: "0.0.0.0"
  port: 8000
  workers: 4
  reload: false
  cors_origins:
    - "https://app.example.com"
  request_timeout: 300

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "/var/log/system-health/app.log"
  max_bytes: 10485760  # 10MB
  backup_count: 5

notifications:
  slack:
    enabled: true
    webhook_url: "${secret:notifications/slack/webhook_url}"
    token: "${secret:notifications/slack/token}"
    channel: "#alerts"
    username: "System Health Bot"

  discord:
    enabled: false
    webhook_url: "${secret:notifications/discord/webhook_url}"
    username: "System Health Bot"

  email:
    enabled: true
    smtp_host: "smtp.gmail.com"
    smtp_port: 587
    smtp_user: "${secret:notifications/email/user}"
    smtp_password: "${secret:notifications/email/password}"
    from_address: "alerts@example.com"
    to_addresses:
      - "ops@example.com"
      - "oncall@example.com"
    use_tls: true

  pagerduty:
    enabled: true
    api_key: "${secret:notifications/pagerduty/api_key}"
    integration_key: "${secret:notifications/pagerduty/integration_key}"

  deduplication_window_minutes: 30

github:
  token: "${secret:github/token}"
  repo: "owner/repository"
  default_branch: "main"
  create_prs: true
  auto_merge: false

cache:
  enabled: true
  redis_url: "redis://localhost:6379/0"
  ttl_seconds: 300
  max_connections: 10

security:
  jwt_secret_key: "${secret:security/jwt_secret_key}"
  jwt_algorithm: "HS256"
  jwt_expiration_minutes: 1440  # 1 day
  api_keys_enabled: true
  rate_limit_enabled: true
  rate_limit_requests: 500
  rate_limit_period_seconds: 60
  cors_enabled: true
  allowed_hosts:
    - "app.example.com"

monitoring:
  metrics_enabled: true
  prometheus_enabled: true
  prometheus_port: 9090
  tracing_enabled: false
  jaeger_host: "localhost:6831"

retention:
  metrics_days: 30
  alerts_days: 90
  diagnoses_days: 180
  fixes_days: 180
  prs_days: 365
  auto_cleanup_enabled: true
  cleanup_schedule_cron: "0 2 * * *"  # 2 AM daily

feature_flags:
  ai_analysis: true
  auto_fix: true
  auto_pr: true
  notifications: true
  database: true
  cache: true
  monitoring: true
```

### TOML Configuration

See `config/config.example.toml` for TOML format.

## Environment Variables

### Core Settings

```bash
# Application environment
APP_ENV=production  # development, staging, production, testing
DEBUG=false
LOG_LEVEL=INFO

# Configuration file
CONFIG_FILE=/path/to/config.yaml
ENABLE_HOT_RELOAD=false
```

### Database

```bash
# Database URL (overrides config file)
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Connection pool settings
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
```

### Redis/Caching

```bash
REDIS_URL=redis://localhost:6379/0
CACHE_TTL_SECONDS=300
CACHE_MAX_CONNECTIONS=10
```

### AI Services

```bash
# API keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here

# Provider selection
AI_PROVIDER=anthropic  # or openai
AI_MODEL=claude-3-sonnet-20240229
AI_MAX_TOKENS=4096
AI_TEMPERATURE=0.7
AI_TIMEOUT=120
```

### GitHub

```bash
GITHUB_TOKEN=ghp_your-token-here
GITHUB_REPO=owner/repository
GITHUB_DEFAULT_BRANCH=main
```

### Notifications

```bash
# Slack
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_TOKEN=xoxb-your-token-here
SLACK_CHANNEL=#alerts

# Discord
DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR/WEBHOOK

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=alerts@example.com

# PagerDuty
PAGERDUTY_API_KEY=your-api-key
PAGERDUTY_INTEGRATION_KEY=your-integration-key
```

### Security

```bash
# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Rate limiting
RATE_LIMIT_REQUESTS=500
RATE_LIMIT_PERIOD_SECONDS=60

# CORS
CORS_ORIGINS=https://app.example.com,https://admin.example.com
```

## Secrets Management

### Using Secrets Placeholders

In configuration files, use `${secret:path/to/secret}` to load from secrets managers:

```yaml
database:
  url: "${secret:database/production_url}"

ai:
  anthropic_api_key: "${secret:ai/anthropic_api_key}"
```

### HashiCorp Vault

```bash
# Set Vault connection
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=your-vault-token

# Store secrets
vault kv put secret/database/production_url value="postgresql://..."
vault kv put secret/ai/anthropic_api_key value="sk-ant-..."

# Application will automatically fetch from Vault
```

### AWS Secrets Manager

```bash
# Set AWS credentials
export AWS_REGION=us-east-1
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key

# Store secrets
aws secretsmanager create-secret \
  --name system-health/database/url \
  --secret-string "postgresql://..."

# Use in config
database:
  url: "${secret:system-health/database/url}"
```

### File-Based Secrets

Create `secrets.json`:

```json
{
  "database": {
    "production_url": "postgresql://..."
  },
  "ai": {
    "anthropic_api_key": "sk-ant-..."
  },
  "notifications": {
    "slack": {
      "webhook_url": "https://..."
    }
  }
}
```

## Environment-Specific Configuration

### Development

```yaml
# config.yaml with development section
development:
  environment: development
  debug: true

  database:
    url: "sqlite+aiosqlite:///./data/dev.db"
    echo: true

  api:
    reload: true
    workers: 1

  logging:
    level: "DEBUG"

  feature_flags:
    auto_fix: false
    auto_pr: false
```

### Staging

```yaml
staging:
  environment: staging
  debug: false

  database:
    url: "${secret:database/staging_url}"
    pool_size: 10

  api:
    workers: 4
    cors_origins:
      - "https://staging.example.com"

  monitoring:
    metrics_enabled: true
```

### Production

```yaml
production:
  environment: production
  debug: false

  database:
    url: "${secret:database/production_url}"
    pool_size: 50
    max_overflow: 100

  api:
    workers: 16
    cors_origins:
      - "https://app.example.com"

  security:
    jwt_secret_key: "${secret:security/production_jwt_secret}"
    rate_limit_requests: 1000

  monitoring:
    metrics_enabled: true
    prometheus_enabled: true
    tracing_enabled: true

  feature_flags:
    ai_analysis: true
    auto_fix: true
    auto_pr: true
```

### Selecting Environment

```bash
# Via environment variable
export APP_ENV=production

# Via command line
APP_ENV=production uvicorn src.api.main:app
```

## Hot Reload

Enable configuration hot reload for development:

```bash
export ENABLE_HOT_RELOAD=true
```

The application will automatically reload when configuration files change.

## Configuration Validation

The application validates configuration on startup using Pydantic schemas.

### View Current Configuration

```python
from src.config import get_config

config = get_config()
print(config.json(indent=2))
```

### Validate Configuration

```bash
# Validate without starting
python -c "from src.config import get_config; get_config(); print('Config valid!')"
```

## Advanced Configuration

### Custom Configuration Sections

Add custom settings:

```yaml
custom:
  feature_x_enabled: true
  feature_x_timeout: 30
  feature_x_params:
    param1: value1
    param2: value2
```

Access in code:

```python
from src.config import get_config

config = get_config()
if config.custom.get("feature_x_enabled"):
    timeout = config.custom.get("feature_x_timeout", 30)
```

### Database URL Formats

```bash
# SQLite (development)
sqlite+aiosqlite:///./data/app.db

# PostgreSQL
postgresql+asyncpg://user:password@host:5432/database

# MySQL
mysql+aiomysql://user:password@host:3306/database
```

### Redis URL Formats

```bash
# Local
redis://localhost:6379/0

# With password
redis://:password@localhost:6379/0

# Redis Sentinel
redis+sentinel://sentinel-host:26379/mymaster/0

# Redis Cluster
redis://host1:6379,host2:6379,host3:6379/0
```

## Configuration Best Practices

### 1. Use Secrets Management

❌ **Don't:**
```yaml
database:
  url: "postgresql://user:password@host/db"
```

✅ **Do:**
```yaml
database:
  url: "${secret:database/production_url}"
```

### 2. Environment-Specific Settings

❌ **Don't:** Mix development and production settings

✅ **Do:** Use environment sections
```yaml
default:
  # Shared settings
development:
  # Dev overrides
production:
  # Prod overrides
```

### 3. Validate Production Settings

```yaml
# Auto-validated in production
production:
  security:
    jwt_secret_key: "${secret:...}"  # Must be set
  database:
    url: "postgresql://..."  # SQLite warns in production
```

### 4. Use Feature Flags

```yaml
feature_flags:
  ai_analysis: true
  auto_fix: false  # Enable gradually
  auto_pr: false
```

### 5. Configure Retention

```yaml
retention:
  metrics_days: 30      # Keep metrics for 30 days
  alerts_days: 90       # Keep alerts for 90 days
  auto_cleanup_enabled: true
  cleanup_schedule_cron: "0 2 * * *"  # Daily at 2 AM
```

## Troubleshooting Configuration

### Configuration Not Loading

```bash
# Check configuration file path
python -c "from src.config.loader import ConfigLoader; \
  loader = ConfigLoader(); \
  print(f'Config file: {loader.config_file}')"

# Verify file exists
ls -la config/config.yaml
```

### Invalid Configuration

```bash
# Run validation
python -c "from src.config import get_config; \
  try: \
    get_config(); \
    print('✓ Configuration valid'); \
  except Exception as e: \
    print(f'✗ Configuration error: {e}')"
```

### Secrets Not Loading

```bash
# Check secrets manager connection
# For Vault:
vault status

# For AWS:
aws secretsmanager list-secrets

# Check secret path
vault kv get secret/your/path
```

### Environment Variables Not Applied

```bash
# Verify environment variables are set
env | grep -E "(APP_ENV|DATABASE_URL|REDIS_URL)"

# Check precedence (env vars override config file)
python -c "from src.config import get_config; \
  config = get_config(); \
  print(f'Database URL: {config.database.url}')"
```

## Example Configurations

### Minimal Development

```yaml
environment: development
debug: true

database:
  url: "sqlite+aiosqlite:///./data/dev.db"

ai:
  provider: "anthropic"
  anthropic_api_key: "sk-ant-..."

notifications:
  slack:
    enabled: false
```

### Production with High Availability

```yaml
environment: production
debug: false

database:
  url: "${secret:database/production_url}"
  pool_size: 50
  max_overflow: 100

cache:
  redis_url: "${secret:cache/redis_cluster_url}"
  max_connections: 50

api:
  workers: 16
  request_timeout: 600

security:
  jwt_secret_key: "${secret:security/jwt_secret}"
  rate_limit_requests: 1000

monitoring:
  metrics_enabled: true
  prometheus_enabled: true
  tracing_enabled: true

retention:
  auto_cleanup_enabled: true

feature_flags:
  ai_analysis: true
  auto_fix: true
  auto_pr: true
  monitoring: true
```

## See Also

- [Quick Start Guide](QUICKSTART.md)
- [Secrets Management](SECURITY.md#secrets-management)
- [Deployment Guide](DEPLOYMENT.md)
- [Environment Variables Reference](ENVIRONMENT.md)
