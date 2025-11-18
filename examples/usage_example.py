"""Example usage of the Plant AI System Analyzer."""

from src.collectors.log_collector import LogCollector
from src.collectors.metrics_collector import MetricsCollector
from src.analyzers.log_analyzer import LogAnalyzer
from src.analyzers.anomaly_detector import AnomalyDetector
from src.ai.llm_client import LLMClient
from src.fixers.auto_fixer import AutoFixer
from src.github_integration.pr_creator import PRCreator
from src.models.schemas import LogFormat


def main():
    print("🌱 Plant AI System Analyzer - Example Usage\n")

    # 1. Collect and parse logs
    print("📋 Step 1: Parsing logs...")
    log_collector = LogCollector()
    logs = log_collector.parse_file("examples/sample_logs.txt", LogFormat.CUSTOM)
    print(f"   ✓ Parsed {len(logs)} log entries\n")

    # 2. Analyze logs
    print("🔍 Step 2: Analyzing logs...")
    log_analyzer = LogAnalyzer()
    analysis = log_analyzer.analyze(logs)
    print(f"   ✓ Found {len(analysis.get('anomalies', []))} anomalies")
    print(f"   ✓ Errors: {analysis['level_distribution']['ERROR']['count']}")
    print(f"   ✓ Warnings: {analysis['level_distribution']['WARNING']['count']}\n")

    # 3. Collect system metrics
    print("📊 Step 3: Collecting system metrics...")
    metrics_collector = MetricsCollector()
    metrics = metrics_collector.collect()
    print(f"   ✓ CPU: {metrics.cpu_percent:.1f}%")
    print(f"   ✓ Memory: {metrics.memory_percent:.1f}%")
    print(f"   ✓ Disk: {metrics.disk_usage_percent:.1f}%\n")

    # 4. AI Analysis (requires API key)
    print("🤖 Step 4: AI-powered diagnosis...")
    print("   ⚠ Skipping (requires ANTHROPIC_API_KEY in .env)")
    print("   To enable: Set ANTHROPIC_API_KEY in your .env file\n")

    # Example of how it would work:
    """
    llm_client = LLMClient()
    diagnosis = llm_client.analyze_logs(logs, analysis.get('anomalies'), metrics)
    print(f"   ✓ Summary: {diagnosis.summary}")
    print(f"   ✓ Severity: {diagnosis.severity.value}")
    print(f"   ✓ Recommendations: {len(diagnosis.recommendations)}")
    """

    # 5. Auto-fix generation (requires API key)
    print("🔧 Step 5: Fix generation...")
    print("   ⚠ Skipping (requires ANTHROPIC_API_KEY)")
    print("   Example: auto_fixer.generate_fix(diagnosis)\n")

    # 6. GitHub PR creation (requires GitHub token)
    print("🚀 Step 6: PR creation...")
    print("   ⚠ Skipping (requires GITHUB_TOKEN)")
    print("   Example: pr_creator.create_pr(diagnosis, fix, codebase_path)\n")

    # 7. Anomaly detection with ML
    print("🎯 Step 7: ML-based anomaly detection...")
    print("   Collecting metrics history for training...")
    for i in range(15):
        metrics_collector.collect()
        if i % 5 == 0:
            print(f"   Collected {i+1} samples...")

    anomaly_detector = AnomalyDetector()
    anomaly_detector.train(metrics_collector.history)
    print(f"   ✓ Trained on {len(metrics_collector.history)} samples")

    # Test detection
    is_anomaly, score = anomaly_detector.detect(metrics)
    print(f"   Current metrics anomaly: {is_anomaly} (score: {score:.2f})\n")

    print("✅ Example completed!")
    print("\n📚 Next steps:")
    print("   1. Set up your .env file with API keys")
    print("   2. Run the API server: python -m src.api.main")
    print("   3. Try the CLI: python -m src.cli.main analyze --logs examples/sample_logs.txt")
    print("   4. Open the dashboard: cd src/ui && npm run dev")


if __name__ == "__main__":
    main()
