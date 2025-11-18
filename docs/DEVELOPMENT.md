# Development Guide

Guide for developers contributing to the System Health Analyzer.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Code Structure](#code-structure)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Quality](#code-quality)
- [Contributing](#contributing)

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Docker and Docker Compose (recommended)
- PostgreSQL 13+ (optional, can use SQLite)
- Redis 6+ (for caching and background jobs)

### Clone Repository

```bash
git clone <repository-url>
cd plant
```

### Setup Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development tools
pip install pre-commit

# Setup pre-commit hooks
pre-commit install
```

### Configuration

```bash
# Copy example config
cp config/config.example.yaml config/config.yaml

# Edit with your settings
nano config/config.yaml
```

### Start Services

```bash
# Option 1: Docker Compose (recommended)
docker-compose up -d postgres redis

# Option 2: Local services
# Start PostgreSQL and Redis locally
```

### Run Application

```bash
# Development server with hot reload
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or use the CLI
python -m src.cli serve --reload
```

---

## Development Environment

### VS Code Setup

Recommended extensions:

```json
// .vscode/extensions.json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "tamasfe.even-better-toml",
    "redhat.vscode-yaml"
  ]
}
```

Settings:

```json
// .vscode/settings.json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

### PyCharm Setup

1. Open project in PyCharm
2. Configure Python interpreter (venv)
3. Enable Black formatter
4. Enable type checking (mypy)
5. Configure run configurations

### Environment Variables

```bash
# .env.development
APP_ENV=development
DEBUG=true
LOG_LEVEL=DEBUG

DATABASE_URL=sqlite+aiosqlite:///./data/dev.db
REDIS_URL=redis://localhost:6379/0

ANTHROPIC_API_KEY=sk-ant-your-dev-key
OPENAI_API_KEY=sk-your-dev-key

GITHUB_TOKEN=ghp_your-dev-token
GITHUB_REPO=owner/test-repo
```

---

## Code Structure

### Directory Layout

```
plant/
├── src/
│   ├── api/               # FastAPI application
│   │   ├── main.py        # Main API entry point
│   │   ├── routes.py      # API routes
│   │   └── database_routes.py
│   ├── ai/                # AI integration
│   │   ├── analyzer.py    # AI analysis
│   │   └── fix_generator.py
│   ├── config/            # Configuration management
│   │   ├── loader.py      # Config loader
│   │   ├── schema.py      # Pydantic schemas
│   │   └── secrets.py     # Secrets management
│   ├── core/              # Core functionality
│   │   ├── log_parser.py
│   │   ├── metrics_collector.py
│   │   └── anomaly_detector.py
│   ├── database/          # Database layer
│   │   ├── models.py      # SQLAlchemy models
│   │   ├── repository.py  # Data access
│   │   └── analytics.py   # Analytics engine
│   ├── github/            # GitHub integration
│   ├── notifications/     # Multi-channel notifications
│   ├── performance/       # Performance optimization
│   │   ├── cache.py       # Redis caching
│   │   ├── rate_limit.py  # Rate limiting
│   │   └── tasks.py       # Background jobs
│   └── security/          # Security features
│       ├── auth.py        # JWT authentication
│       ├── api_keys.py    # API key management
│       └── validation.py  # Input validation
├── tests/                 # Test suite
│   ├── test_integration.py
│   ├── test_performance.py
│   ├── test_database.py
│   └── mock_data.py
├── docs/                  # Documentation
├── deployment/            # Deployment configs
│   ├── kubernetes/
│   └── terraform/
└── config/                # Configuration files
```

### Module Organization

Each module follows this pattern:

```python
# module/__init__.py
"""
Module description.

Exports public API.
"""

from .main_class import MainClass
from .helper import helper_function

__all__ = ["MainClass", "helper_function"]
```

---

## Development Workflow

### Branch Strategy

```bash
# Feature branch
git checkout -b feature/amazing-feature

# Bug fix branch
git checkout -b fix/bug-description

# Make changes, commit
git add .
git commit -m "Add amazing feature"

# Push and create PR
git push origin feature/amazing-feature
```

### Commit Messages

Follow conventional commits:

```bash
# Format
<type>(<scope>): <description>

# Types
feat: New feature
fix: Bug fix
docs: Documentation
style: Formatting
refactor: Code refactoring
test: Tests
chore: Maintenance

# Examples
feat(api): add metrics endpoint
fix(database): resolve connection pool issue
docs(readme): update installation instructions
test(auth): add JWT authentication tests
```

### Making Changes

1. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes**
   - Write code
   - Add tests
   - Update documentation

3. **Run tests**
   ```bash
   pytest tests/ -v
   ```

4. **Format code**
   ```bash
   black src/ tests/
   isort src/ tests/
   ```

5. **Lint**
   ```bash
   ruff check src/
   mypy src/
   ```

6. **Commit**
   ```bash
   git add .
   git commit -m "feat(module): description"
   ```

7. **Push and create PR**
   ```bash
   git push origin feature/my-feature
   ```

---

## Testing

### Run Tests

```bash
# All tests
pytest tests/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Specific test file
pytest tests/test_integration.py -v

# Specific test
pytest tests/test_integration.py::test_full_analysis_pipeline -v

# Performance benchmarks
pytest tests/test_performance.py --benchmark-only

# Load tests
cd tests/load_testing
./run_load_tests.sh
```

### Writing Tests

#### Unit Test Example

```python
# tests/test_metrics.py
import pytest
from src.core.metrics_collector import MetricsCollector

def test_collect_cpu_metrics():
    """Test CPU metrics collection."""
    collector = MetricsCollector()
    metrics = asyncio.run(collector.collect_cpu())

    assert "percent" in metrics
    assert 0 <= metrics["percent"] <= 100
    assert "count" in metrics
    assert metrics["count"] > 0

@pytest.mark.asyncio
async def test_collect_all_metrics():
    """Test collecting all metrics."""
    collector = MetricsCollector()
    metrics = await collector.collect_all()

    assert "cpu" in metrics
    assert "memory" in metrics
    assert "disk" in metrics
```

#### Integration Test Example

```python
# tests/test_api_integration.py
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_metrics_endpoint():
    """Test metrics endpoint."""
    response = client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "cpu" in data
    assert "memory" in data
```

#### Fixtures

```python
# tests/conftest.py
import pytest
from src.database.connection import get_db_session

@pytest.fixture
async def test_db():
    """Create test database."""
    # Setup
    async with get_db_session() as db:
        yield db
    # Teardown

@pytest.fixture
def mock_ai_response():
    """Mock AI API response."""
    return {
        "severity": "high",
        "category": "performance",
        "root_cause": "Database connection pool exhausted"
    }
```

### Test Coverage

```bash
# Generate coverage report
pytest tests/ --cov=src --cov-report=html

# View report
open htmlcov/index.html
```

---

## Code Quality

### Formatting

```bash
# Format code with Black
black src/ tests/

# Sort imports
isort src/ tests/

# Check formatting
black --check src/ tests/
```

### Linting

```bash
# Ruff (fast linter)
ruff check src/

# Flake8
flake8 src/ --max-line-length=127

# Pylint
pylint src/ --exit-zero
```

### Type Checking

```bash
# MyPy
mypy src/ --ignore-missing-imports
```

### Security Scanning

```bash
# Bandit (security issues)
bandit -r src/

# Safety (dependency vulnerabilities)
safety check
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.8
    hooks:
      - id: ruff

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

```bash
# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

---

## Adding Features

### 1. Plan Feature

- Define requirements
- Design API/interface
- Consider testing strategy
- Update documentation

### 2. Create Module

```python
# src/features/new_feature.py
"""
New feature module.

Provides functionality for X.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)


class NewFeature:
    """Main feature class."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize feature."""
        self.config = config or {}
        logger.info("NewFeature initialized")

    async def process(self, data: dict) -> dict:
        """Process data."""
        # Implementation
        return {"result": "..."}


# Export public API
__all__ = ["NewFeature"]
```

### 3. Add Tests

```python
# tests/test_new_feature.py
import pytest
from src.features.new_feature import NewFeature


def test_new_feature_init():
    """Test feature initialization."""
    feature = NewFeature()
    assert feature is not None


@pytest.mark.asyncio
async def test_new_feature_process():
    """Test feature processing."""
    feature = NewFeature()
    result = await feature.process({"input": "data"})
    assert "result" in result
```

### 4. Add API Endpoint

```python
# src/api/routes.py
from fastapi import APIRouter
from src.features.new_feature import NewFeature

router = APIRouter()


@router.post("/api/new-feature")
async def process_new_feature(data: dict):
    """Process with new feature."""
    feature = NewFeature()
    result = await feature.process(data)
    return result
```

### 5. Update Documentation

```markdown
# docs/FEATURES.md

## New Feature

Description of new feature.

### Usage

\```python
from src.features.new_feature import NewFeature

feature = NewFeature()
result = await feature.process(data)
\```

### API Endpoint

`POST /api/new-feature`
```

---

## Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Use Debugger

```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use debugpy for VS Code
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

### Print Debugging

```python
# Use rich for better output
from rich import print
print({"data": data})

# Or use pretty printer
import pprint
pprint.pprint(data)
```

---

## Performance Profiling

### Profile Code

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = my_function()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Memory Profiling

```python
from memory_profiler import profile

@profile
def my_function():
    # Code to profile
    pass
```

---

## Contributing

### Code Review Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Code formatted (black, isort)
- [ ] Linting passed (ruff, mypy)
- [ ] No security vulnerabilities
- [ ] Performance acceptable
- [ ] Error handling added
- [ ] Logging added
- [ ] Type hints added
- [ ] Docstrings added

### Pull Request Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing

How was this tested?

## Checklist

- [ ] Tests pass
- [ ] Code formatted
- [ ] Documentation updated
- [ ] No breaking changes

## Screenshots

If applicable.
```

---

## Common Tasks

### Add New Endpoint

1. Define route in `src/api/routes.py`
2. Add request/response models
3. Implement handler
4. Add tests
5. Update API docs

### Add New Database Table

1. Define model in `src/database/models.py`
2. Create migration: `alembic revision --autogenerate -m "Add table"`
3. Review migration
4. Apply: `alembic upgrade head`
5. Add repository methods
6. Add tests

### Add New Configuration

1. Add to schema in `src/config/schema.py`
2. Update example configs
3. Add validation
4. Update documentation

### Add New Test

1. Create test file in `tests/`
2. Write test functions
3. Add fixtures if needed
4. Run tests: `pytest tests/test_new.py -v`

---

## Troubleshooting

### Import Errors

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Or use editable install
pip install -e .
```

### Database Issues

```bash
# Reset database
rm data/dev.db
alembic upgrade head
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping

# Or start with Docker
docker-compose up -d redis
```

---

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [pytest Documentation](https://docs.pytest.org/)

---

## See Also

- [Quick Start Guide](QUICKSTART.md)
- [API Reference](API.md)
- [Testing Guide](TESTING.md)
- [Architecture Documentation](ARCHITECTURE.md)
