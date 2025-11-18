# Setup Guide

Complete setup guide for the Plant AI System Health Analyzer.

## Prerequisites

- Python 3.10 or higher
- Node.js 18+ and npm (for the dashboard)
- Git
- GitHub account (for PR automation)
- Anthropic API key (for AI analysis)

## Installation Steps

### 1. Clone and Setup Python Environment

```bash
# Navigate to project directory
cd plant

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your credentials:
# - ANTHROPIC_API_KEY: Get from https://console.anthropic.com/
# - GITHUB_TOKEN: Create at https://github.com/settings/tokens
# - GITHUB_REPO: Your repo in format "owner/repo"
```

### 3. Setup Dashboard (Optional)

```bash
# Navigate to UI directory
cd src/ui

# Install dependencies
npm install

# Return to project root
cd ../..
```

## Running the Application

### Option 1: API Server

Start the FastAPI backend server:

```bash
python -m src.api.main
```

The API will be available at `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

### Option 2: CLI Tool

Use the command-line interface:

```bash
# Analyze logs
python -m src.cli.main analyze --logs examples/sample_logs.txt --ai

# Monitor system metrics
python -m src.cli.main monitor --interval 60 --detect

# Check PR status
python -m src.cli.main pr-status --pr-number 123
```

### Option 3: Dashboard UI

Start the React dashboard:

```bash
cd src/ui
npm run dev
```

Visit `http://localhost:5173` in your browser

### Option 4: Python Script

Run the example script:

```bash
python examples/usage_example.py
```

## Usage Examples

### Analyze Logs with AI

```python
from src.collectors.log_collector import LogCollector
from src.analyzers.log_analyzer import LogAnalyzer
from src.ai.llm_client import LLMClient

# Parse logs
collector = LogCollector()
logs = collector.parse_file("path/to/logs.txt")

# Analyze
analyzer = LogAnalyzer()
analysis = analyzer.analyze(logs)

# Get AI diagnosis
llm = LLMClient()
diagnosis = llm.analyze_logs(logs, analysis['anomalies'])

print(f"Summary: {diagnosis.summary}")
print(f"Root cause: {diagnosis.root_cause}")
```

### Generate and Apply Fix

```python
from src.fixers.auto_fixer import AutoFixer
from src.github_integration.pr_creator import PRCreator

# Generate fix
fixer = AutoFixer()
fix = fixer.generate_fix(diagnosis, codebase_path="/path/to/repo")

# Validate
is_valid = fixer.validate_fix(fix, codebase_path)

# Create PR
if is_valid:
    pr_creator = PRCreator()
    pr = pr_creator.create_pr(diagnosis, fix, codebase_path)
    print(f"PR created: {pr.pr_url}")
```

### Monitor System Metrics

```python
from src.collectors.metrics_collector import MetricsCollector
from src.analyzers.anomaly_detector import AnomalyDetector

# Collect metrics
collector = MetricsCollector()
metrics = collector.collect()

# Train anomaly detector
detector = AnomalyDetector()
detector.train(collector.history)

# Detect anomalies
is_anomaly, score = detector.detect(metrics)
if is_anomaly:
    anomaly = detector.classify_anomaly(metrics, score)
    print(f"Anomaly: {anomaly.description}")
```

## API Endpoints

### Metrics
- `GET /metrics/current` - Get current system metrics
- `GET /metrics/detailed` - Get detailed metrics with process info
- `GET /metrics/history` - Get metrics history
- `GET /metrics/issues` - Get current resource issues

### Analysis
- `POST /analyze` - Analyze logs with optional AI, fixes, and PR creation
- `POST /logs/parse` - Parse log content

### Anomaly Detection
- `GET /anomalies/train` - Train anomaly detector
- `GET /anomalies/detect` - Detect anomalies in current metrics

## Testing

Run the test suite:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run specific test file
pytest tests/test_log_collector.py
```

## Troubleshooting

### API Key Issues
- Ensure `.env` file exists and contains valid keys
- Check that `ANTHROPIC_API_KEY` starts with `sk-ant-`

### Import Errors
- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

### GitHub PR Creation Fails
- Check `GITHUB_TOKEN` has `repo` scope
- Verify `GITHUB_REPO` format is `owner/repo`
- Ensure you have write access to the repository

### Dashboard Won't Start
- Check Node.js version: `node --version` (should be 18+)
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check if port 5173 is available

## Development

### Code Quality

```bash
# Format code
black src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

### Project Structure

```
plant/
├── src/
│   ├── analyzers/      # Log and metrics analysis
│   ├── ai/             # LLM integration
│   ├── api/            # FastAPI application
│   ├── cli/            # Command-line interface
│   ├── collectors/     # Data collection
│   ├── fixers/         # Fix generation
│   ├── github_integration/  # PR automation
│   ├── models/         # Data models
│   └── ui/             # React dashboard
├── examples/           # Example scripts and data
├── tests/             # Test suite
└── requirements.txt   # Python dependencies
```

## Next Steps

1. **Customize for Your Stack**: Modify log patterns, metrics thresholds
2. **Add More Fix Templates**: Extend `auto_fixer.py` with common fixes
3. **Integrate with Monitoring**: Connect to Prometheus, Grafana, etc.
4. **Schedule Analysis**: Set up cron jobs for periodic analysis
5. **Enhance Dashboard**: Add more visualizations and features

## Support

For issues, questions, or contributions, please refer to the main README.md
