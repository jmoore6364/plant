# Quick Start Guide

Get up and running with the System Health Analyzer in minutes.

## Prerequisites

- Python 3.10 or higher
- Docker and Docker Compose (recommended)
- Git
- Redis (for caching and background jobs)
- PostgreSQL (optional, SQLite used by default)

## Installation Methods

### Option 1: Docker Compose (Recommended)

The fastest way to get started with all services running:

```bash
# Clone the repository
git clone <repository-url>
cd plant

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

**Services Available:**
- API Server: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Flower (Celery): http://localhost:5555

### Option 2: Local Development

For development with hot reload:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy configuration
cp config/config.example.yaml config/config.yaml

# Edit config.yaml with your settings
nano config/config.yaml

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Option 3: Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for Kubernetes and AWS deployment guides.

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Application
APP_ENV=development
LOG_LEVEL=INFO

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/system_health.db

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Services
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here

# GitHub
GITHUB_TOKEN=ghp_your-token-here
GITHUB_REPO=owner/repository

# Notifications
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
SLACK_TOKEN=xoxb-your-token
```

### Configuration File

Edit `config/config.yaml` for more advanced settings:

```yaml
environment: development
debug: true

database:
  url: "sqlite+aiosqlite:///./data/system_health.db"

ai:
  provider: "anthropic"
  model: "claude-3-sonnet-20240229"

notifications:
  slack:
    enabled: true
    channel: "#alerts"
```

## First Steps

### 1. Health Check

Verify the system is running:

```bash
curl http://localhost:8000/health
```

### 2. Collect System Metrics

```bash
curl http://localhost:8000/api/metrics
```

### 3. Trigger Analysis

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"trigger": "manual"}'
```

### 4. View Historical Data

```bash
# Get recent analyses
curl http://localhost:8000/history/analyses?hours=24&limit=10

# Get system health score
curl http://localhost:8000/history/analytics/health-score

# Get alert history
curl http://localhost:8000/history/alerts?hours=24
```

## API Documentation

Interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Common Tasks

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_integration.py -v

# Run load tests
cd tests/load_testing
./run_load_tests.sh
```

### Start Background Workers

```bash
# Start Celery worker
celery -A src.performance.tasks worker --loglevel=info

# Start Celery beat (scheduler)
celery -A src.performance.tasks beat --loglevel=info

# Monitor with Flower
celery -A src.performance.tasks flower
```

### Database Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Data Cleanup

```bash
# Clean up old metrics (older than 30 days)
curl -X POST http://localhost:8000/retention/cleanup/metrics_snapshots?retention_days=30

# Export data
curl -X POST http://localhost:8000/retention/export/alerts?hours=168
```

## Authentication

### Create User

```python
from src.security import UserManager, hash_password

manager = UserManager()
user = manager.create_user(
    username="admin",
    password="secure_password",
    email="admin@example.com",
    roles=["admin"]
)
```

### Generate API Key

```python
from src.security import APIKeyManager

manager = APIKeyManager()
raw_key, api_key = manager.generate_key(
    name="Production API",
    scopes=["read", "write"],
    rate_limit=1000,
    expires_in_days=365
)

print(f"API Key: {raw_key}")  # Save this securely!
```

### Use API Key

```bash
curl http://localhost:8000/api/data \
  -H "X-API-Key: sha_your-api-key-here"
```

## Monitoring

### View Metrics

```bash
# Prometheus metrics
curl http://localhost:8000/metrics

# Cache statistics
curl http://localhost:8000/api/cache/stats

# System health
curl http://localhost:8000/api/system/health
```

### View Logs

```bash
# Application logs
tail -f logs/app.log

# Audit logs
tail -f logs/audit.log

# Docker logs
docker-compose logs -f app
```

## Troubleshooting

### API Not Starting

1. Check if port 8000 is available:
   ```bash
   lsof -i :8000
   ```

2. Check logs for errors:
   ```bash
   docker-compose logs app
   ```

3. Verify configuration:
   ```bash
   python -c "from src.config import get_config; print(get_config())"
   ```

### Database Connection Issues

1. Check database URL in config
2. Verify database is running:
   ```bash
   docker-compose ps postgres
   ```

3. Test connection:
   ```bash
   python -c "from src.database.connection import init_db; import asyncio; asyncio.run(init_db())"
   ```

### Redis Connection Issues

1. Check Redis is running:
   ```bash
   docker-compose ps redis
   ```

2. Test connection:
   ```bash
   redis-cli ping
   ```

### AI Analysis Not Working

1. Verify API keys are set:
   ```bash
   echo $ANTHROPIC_API_KEY
   ```

2. Check AI service status in logs
3. Verify network connectivity to API endpoints

## Next Steps

- [Configuration Guide](CONFIGURATION.md) - Detailed configuration options
- [API Reference](API.md) - Complete API documentation
- [Security Guide](SECURITY.md) - Authentication and authorization
- [Deployment Guide](DEPLOYMENT.md) - Production deployment
- [Development Guide](DEVELOPMENT.md) - Contributing and development

## Getting Help

- Check the [Troubleshooting Guide](TROUBLESHOOTING.md)
- Review [FAQ](FAQ.md)
- Open an issue on GitHub
- Check the logs for error messages

## Quick Reference

| Task | Command |
|------|---------|
| Start services | `docker-compose up -d` |
| Stop services | `docker-compose down` |
| View logs | `docker-compose logs -f` |
| Run tests | `pytest tests/` |
| API docs | http://localhost:8000/docs |
| Health check | `curl localhost:8000/health` |
| Run migrations | `alembic upgrade head` |
| Clean old data | `curl -X POST localhost:8000/retention/cleanup/metrics_snapshots` |
