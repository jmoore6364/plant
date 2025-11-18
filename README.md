# AI-Powered System Health Analyzer & Auto-Fixer

An intelligent DevOps automation tool that analyzes system logs and metrics, diagnoses issues using AI, and automatically creates pull requests with fixes.

## Features

### Phase 1: Core Analysis
- **Log Parser**: Parse multiple log formats (syslog, application logs, JSON logs)
- **Metrics Collector**: Collect system metrics (CPU, memory, disk, network)
- **Anomaly Detection**: ML-based pattern recognition and anomaly detection

### Phase 2: AI Integration
- **LLM Analysis**: Deep log and metric analysis using Claude/GPT-4
- **Context Building**: Intelligent correlation of logs and metrics
- **Smart Diagnosis**: Human-readable summaries with root cause analysis

### Phase 3: Fix Generation
- **Code Templates**: Pre-built fix templates for common issues
- **AI Fix Generator**: LLM-powered code fix generation
- **Validation**: Automatic validation of generated fixes

### Phase 4: GitHub Automation
- **Auto PR Creation**: Automatically create PRs with fixes
- **Branch Management**: Smart branch creation and management
- **Test Integration**: Validate fixes before creating PRs

### Phase 5: Polish
- **Dashboard UI**: Real-time monitoring and analysis dashboard
- **Alerting**: Configurable alerts for critical issues
- **Documentation**: Comprehensive guides and API docs

## Architecture

```
src/
├── analyzers/          # Log and metric analysis
├── ai/                 # LLM integration and AI reasoning
├── collectors/         # Data collection modules
├── fixers/            # Fix generation and application
├── github_integration/ # GitHub PR automation
├── models/            # ML models for anomaly detection
├── api/               # FastAPI REST API
└── ui/                # React dashboard
```

## Quick Start

### Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Set the following in `.env`:
- `ANTHROPIC_API_KEY`: Your Anthropic Claude API key
- `OPENAI_API_KEY`: (Optional) OpenAI API key
- `GITHUB_TOKEN`: GitHub personal access token
- `GITHUB_REPO`: Target repository for PRs

### Usage

```bash
# Start the API server
python -m src.api.main

# Run analysis on logs
python -m src.cli analyze --logs /path/to/logs

# Monitor system metrics
python -m src.cli monitor --interval 60

# Start dashboard
cd src/ui && npm run dev
```

## Examples

### Analyze Application Logs
```python
from src.analyzers.log_analyzer import LogAnalyzer
from src.ai.llm_client import LLMClient

analyzer = LogAnalyzer()
logs = analyzer.parse_file("/var/log/app.log")

llm = LLMClient()
diagnosis = llm.analyze_logs(logs)
print(diagnosis.summary)
```

### Auto-Fix and Create PR
```python
from src.fixers.auto_fixer import AutoFixer

fixer = AutoFixer()
issue = fixer.analyze_and_fix(logs, metrics)

if issue.fix_generated:
    pr_url = fixer.create_pr(issue)
    print(f"PR created: {pr_url}")
```

## Development

```bash
# Run tests
pytest tests/

# Run linter
ruff check src/

# Format code
black src/
```

## License

MIT License - see LICENSE file
