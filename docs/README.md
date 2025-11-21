# Documentation Index

Welcome to the System Health Analyzer documentation! This index will help you find what you need.

## 📚 Documentation Structure

### Getting Started

Start here if you're new to the System Health Analyzer.

| Document | Description |
|----------|-------------|
| [Quick Start Guide](QUICKSTART.md) | Get up and running in minutes |
| [Installation Guide](../README.md#-quick-start) | Detailed installation instructions |
| [Configuration Guide](CONFIGURATION.md) | Configure the application |

### Core Documentation

Essential guides for using the system.

| Document | Description |
|----------|-------------|
| [API Reference](API.md) | Complete REST API documentation |
| [Web Dashboard UI](UI.md) | React dashboard setup and usage |
| [Configuration Guide](CONFIGURATION.md) | Configuration options and secrets management |
| [Security Guide](SECURITY.md) | Authentication, authorization, and security |
| [Deployment Guide](DEPLOYMENT.md) | Deploy to Docker, Kubernetes, or AWS |

### Feature Guides

Detailed documentation for specific features.

| Document | Description |
|----------|-------------|
| [Notifications Guide](NOTIFICATIONS.md) | Multi-channel alerting (Slack, Email, PagerDuty) |
| [Database Guide](DATABASE.md) | Historical tracking and analytics |
| [Testing Guide](TESTING.md) | Testing strategies and best practices |
| [Development Guide](DEVELOPMENT.md) | Contributing and development workflow |

### Operations

Guides for running the system in production.

| Document | Description |
|----------|-------------|
| [Monitoring Guide](MONITORING.md) | Metrics, logging, and observability |
| [Troubleshooting Guide](TROUBLESHOOTING.md) | Common issues and solutions |
| [Runbook](RUNBOOK.md) | Operational procedures |
| [FAQ](FAQ.md) | Frequently asked questions |

---

## 🚀 Quick Links

### For New Users

1. **Start Here**: [Quick Start Guide](QUICKSTART.md)
2. **Configure**: [Configuration Guide](CONFIGURATION.md)
3. **Learn API**: [API Reference](API.md)

### For Developers

1. **Setup Dev Environment**: [Development Guide](DEVELOPMENT.md)
2. **Understand Architecture**: [Architecture](#architecture)
3. **Write Tests**: [Testing Guide](TESTING.md)
4. **Contribute**: [Contributing Guidelines](#contributing)

### For DevOps/SRE

1. **Deploy**: [Deployment Guide](DEPLOYMENT.md)
2. **Monitor**: [Monitoring Guide](MONITORING.md)
3. **Secure**: [Security Guide](SECURITY.md)
4. **Troubleshoot**: [Troubleshooting Guide](TROUBLESHOOTING.md)

---

## 📖 Documentation by Topic

### Authentication & Security

- [JWT Authentication](SECURITY.md#jwt-authentication)
- [OAuth 2.0 Integration](SECURITY.md#oauth-20)
- [API Key Management](SECURITY.md#api-key-authentication)
- [Input Validation](SECURITY.md#input-validation)
- [Audit Logging](SECURITY.md#audit-logging)
- [Secrets Management](CONFIGURATION.md#secrets-management)

### Configuration

- [Configuration Files](CONFIGURATION.md#configuration-files)
- [Environment Variables](CONFIGURATION.md#environment-variables)
- [Environment-Specific Configs](CONFIGURATION.md#environment-specific-configuration)
- [Hot Reload](CONFIGURATION.md#hot-reload)
- [HashiCorp Vault](CONFIGURATION.md#hashicorp-vault)
- [AWS Secrets Manager](CONFIGURATION.md#aws-secrets-manager)

### Deployment

- [Docker Deployment](DEPLOYMENT.md#docker-deployment)
- [Docker Compose](DEPLOYMENT.md#docker-deployment)
- [Kubernetes Deployment](DEPLOYMENT.md#kubernetes-deployment)
- [AWS/ECS Deployment](DEPLOYMENT.md#aws-deployment-terraform)
- [Manual Deployment](DEPLOYMENT.md#manual-deployment)
- [Production Checklist](DEPLOYMENT.md#production-checklist)

### API

- [Authentication](API.md#authentication)
- [Core Endpoints](API.md#core-endpoints)
- [Analysis Endpoints](API.md#analysis-endpoints)
- [Historical Data](API.md#historical-data-endpoints)
- [Analytics Endpoints](API.md#analytics-endpoints)
- [Rate Limiting](API.md#rate-limiting)
- [Error Responses](API.md#error-responses)

### Features

- [AI Analysis](../README.md#core-system-phases-1-5)
- [Alerting & Notifications](NOTIFICATIONS.md)
- [Database & Analytics](DATABASE.md)
- [Performance Optimization](../README.md#performance-optimization-)
- [Background Jobs](API.md#background-task-endpoints)
- [Caching](API.md#cache-management-endpoints)

### Testing

- [Unit Tests](TESTING.md#unit-tests)
- [Integration Tests](TESTING.md#integration-tests)
- [Performance Tests](TESTING.md#performance-tests)
- [Load Tests](TESTING.md#load-tests)
- [Test Coverage](TESTING.md#coverage)
- [Mock Data](TESTING.md#mock-data)

### Development

- [Setup Environment](DEVELOPMENT.md#development-environment)
- [Code Structure](DEVELOPMENT.md#code-structure)
- [Development Workflow](DEVELOPMENT.md#development-workflow)
- [Adding Features](DEVELOPMENT.md#adding-features)
- [Code Quality](DEVELOPMENT.md#code-quality)
- [Contributing](DEVELOPMENT.md#contributing)

---

## 🏗️ Architecture

### High-Level Overview

```
┌─────────────┐
│   Client    │
│ Application │
└──────┬──────┘
       │ HTTPS
       ▼
┌─────────────────────────────────────┐
│        Load Balancer / Ingress      │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│  FastAPI    │  │  FastAPI    │
│  Instance   │  │  Instance   │
│  (App)      │  │  (App)      │
└──────┬──────┘  └──────┬──────┘
       │                │
       ├────────┬───────┤
       ▼        ▼       ▼
┌──────────┐ ┌──────┐ ┌─────────┐
│PostgreSQL│ │Redis │ │ Celery  │
│(Database)│ │(Cache│ │(Workers)│
└──────────┘ └──────┘ └─────────┘
```

### Component Architecture

```
src/
├── api/               # REST API layer
│   └── FastAPI endpoints
├── ai/                # AI integration
│   ├── Anthropic Claude
│   └── OpenAI GPT
├── core/              # Core business logic
│   ├── Log parsing
│   ├── Metrics collection
│   └── Anomaly detection
├── database/          # Data persistence
│   ├── SQLAlchemy models
│   └── Analytics engine
├── notifications/     # Multi-channel alerts
│   ├── Slack
│   ├── Discord
│   ├── Email
│   └── PagerDuty
├── performance/       # Performance features
│   ├── Redis caching
│   ├── Rate limiting
│   └── Background jobs
└── security/          # Security features
    ├── JWT auth
    ├── OAuth 2.0
    └── API keys
```

### Data Flow

```
1. Client Request
   ↓
2. Authentication/Authorization
   ↓
3. Rate Limiting
   ↓
4. Input Validation
   ↓
5. Business Logic
   ↓
6. Database/Cache
   ↓
7. Response
```

---

## 🎯 Common Use Cases

### 1. Setting Up for Development

```bash
# See: Quick Start Guide
1. Clone repository
2. Install dependencies
3. Configure application
4. Start services
5. Run tests
```

[Full Guide →](QUICKSTART.md#option-2-local-development)

### 2. Deploying to Production

```bash
# See: Deployment Guide
1. Build Docker image
2. Configure secrets
3. Deploy to Kubernetes/AWS
4. Configure monitoring
5. Run health checks
```

[Full Guide →](DEPLOYMENT.md)

### 3. Setting Up Notifications

```yaml
# See: Notifications Guide
notifications:
  slack:
    enabled: true
    webhook_url: "..."
```

[Full Guide →](NOTIFICATIONS.md)

### 4. Securing the API

```python
# See: Security Guide
@app.get("/protected")
async def protected(user=Depends(get_current_user)):
    return {"data": "..."}
```

[Full Guide →](SECURITY.md)

### 5. Monitoring System Health

```bash
# See: Monitoring Guide
curl http://localhost:8000/metrics
curl http://localhost:8000/history/analytics/health-score
```

[Full Guide →](MONITORING.md)

---

## 🔧 Configuration Examples

### Minimal Development Setup

```yaml
# config.yaml
environment: development
debug: true

database:
  url: "sqlite+aiosqlite:///./data/dev.db"

ai:
  provider: "anthropic"
  anthropic_api_key: "sk-ant-..."
```

### Production Setup

```yaml
# config.yaml
environment: production
debug: false

database:
  url: "${secret:database/production_url}"
  pool_size: 50

security:
  jwt_secret_key: "${secret:security/jwt_secret}"
  rate_limit_requests: 1000

monitoring:
  metrics_enabled: true
  prometheus_enabled: true
```

[Full Configuration Guide →](CONFIGURATION.md)

---

## 📊 API Examples

### Trigger Analysis

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"trigger": "manual"}'
```

### Get System Health

```bash
curl http://localhost:8000/history/analytics/health-score
```

### Send Alert

```bash
curl -X POST http://localhost:8000/api/notifications/send \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sha_your-key" \
  -d '{
    "title": "High CPU Usage",
    "priority": "high",
    "channels": ["slack", "email"]
  }'
```

[Full API Reference →](API.md)

---

## 🐛 Troubleshooting

### Quick Diagnostics

```bash
# Check health
curl http://localhost:8000/health

# View logs
docker-compose logs -f app

# Check database
python -c "from src.database.connection import init_db; import asyncio; asyncio.run(init_db())"

# Test Redis
redis-cli ping
```

[Full Troubleshooting Guide →](TROUBLESHOOTING.md)

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Write code
   - Add tests
   - Update documentation
4. **Run tests**
   ```bash
   pytest tests/ -v
   ```
5. **Submit a pull request**

[Development Guide →](DEVELOPMENT.md)

---

## 📞 Getting Help

### Documentation

- Check this documentation index
- Read the relevant guide
- Search the FAQ

### Issues

- Check [existing issues](https://github.com/org/repo/issues)
- Create a new issue with:
  - Description of the problem
  - Steps to reproduce
  - Expected behavior
  - Actual behavior
  - Logs/error messages

### Community

- Join our Discord/Slack
- Ask questions
- Share your use cases

---

## 📝 Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| Quick Start | ✅ Complete | 2024-01-01 |
| API Reference | ✅ Complete | 2024-01-01 |
| Configuration | ✅ Complete | 2024-01-01 |
| Security | ✅ Complete | 2024-01-01 |
| Deployment | ✅ Complete | 2024-01-01 |
| Notifications | ✅ Complete | 2023-12-15 |
| Database | ✅ Complete | 2023-12-15 |
| Development | ✅ Complete | 2024-01-01 |
| Testing | 🚧 In Progress | - |
| Monitoring | 🚧 In Progress | - |
| Troubleshooting | 🚧 In Progress | - |
| FAQ | 📝 Planned | - |

---

## 🔄 Documentation Updates

This documentation is continuously improved. To suggest improvements:

1. Open an issue with `documentation` label
2. Submit a PR with documentation changes
3. Contact the maintainers

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

**Need help?** Start with the [Quick Start Guide](QUICKSTART.md) or check the [FAQ](FAQ.md).
