"""Command-line interface for Plant AI System Analyzer."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
from pathlib import Path
import time

from src.collectors.log_collector import LogCollector
from src.collectors.metrics_collector import MetricsCollector
from src.analyzers.log_analyzer import LogAnalyzer
from src.analyzers.anomaly_detector import AnomalyDetector
from src.ai.llm_client import LLMClient
from src.fixers.auto_fixer import AutoFixer
from src.github_integration.pr_creator import PRCreator
from src.models.schemas import LogFormat

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Plant - AI-Powered System Health Analyzer & Auto-Fixer"""
    pass


@cli.command()
@click.option("--logs", "-l", type=click.Path(exists=True), help="Log file to analyze")
@click.option("--format", "-f", type=click.Choice(["syslog", "json", "apache", "custom"]), default="custom")
@click.option("--ai/--no-ai", default=True, help="Use AI analysis")
@click.option("--fix/--no-fix", default=False, help="Generate fixes")
@click.option("--pr/--no-pr", default=False, help="Create PR for fixes")
def analyze(logs, format, ai, fix, pr):
    """Analyze logs and generate diagnosis."""
    console.print(Panel.fit("🔍 Plant AI System Analyzer", style="bold blue"))

    if not logs:
        console.print("[red]Error: No log file specified[/red]")
        return

    # Parse logs
    with console.status("[bold green]Parsing logs..."):
        log_collector = LogCollector()
        log_format = LogFormat(format)
        entries = log_collector.parse_file(logs, log_format)
        console.print(f"✓ Parsed {len(entries)} log entries")

    # Analyze logs
    with console.status("[bold green]Analyzing logs..."):
        log_analyzer = LogAnalyzer()
        analysis = log_analyzer.analyze(entries)
        console.print(f"✓ Analysis complete")

    # Display results
    _display_analysis(analysis)

    # AI analysis
    if ai:
        with console.status("[bold green]Running AI analysis..."):
            llm_client = LLMClient()
            anomalies = analysis.get("anomalies", [])
            diagnosis = llm_client.analyze_logs(entries, anomalies)
            console.print(f"✓ AI diagnosis complete")

        _display_diagnosis(diagnosis)

        # Generate fix
        if fix:
            with console.status("[bold green]Generating fix..."):
                auto_fixer = AutoFixer(llm_client)
                generated_fix = auto_fixer.generate_fix(diagnosis)
                console.print(f"✓ Fix generated")

            _display_fix(generated_fix)

            # Create PR
            if pr:
                codebase_path = click.prompt("Enter codebase path", type=str)
                with console.status("[bold green]Creating pull request..."):
                    pr_creator = PRCreator()
                    pull_request = pr_creator.create_pr(
                        diagnosis, generated_fix, codebase_path
                    )
                    console.print(f"✓ PR created")

                _display_pr(pull_request)


@cli.command()
@click.option("--interval", "-i", default=60, help="Collection interval in seconds")
@click.option("--duration", "-d", default=None, type=int, help="Total duration in seconds")
@click.option("--detect/--no-detect", default=True, help="Detect anomalies")
def monitor(interval, duration, detect):
    """Monitor system metrics continuously."""
    console.print(Panel.fit("📊 System Metrics Monitor", style="bold blue"))

    metrics_collector = MetricsCollector()
    anomaly_detector = AnomalyDetector() if detect else None

    start_time = time.time()

    try:
        while True:
            # Collect metrics
            metrics = metrics_collector.collect()

            # Display metrics
            _display_metrics(metrics)

            # Detect anomalies
            if detect and anomaly_detector and anomaly_detector.is_trained:
                is_anomaly, score = anomaly_detector.detect(metrics)
                if is_anomaly:
                    console.print(f"[red]⚠ Anomaly detected (score: {score:.2f})[/red]")

            # Check duration
            if duration and (time.time() - start_time) >= duration:
                break

            time.sleep(interval)

    except KeyboardInterrupt:
        console.print("\n[yellow]Monitoring stopped[/yellow]")


@cli.command()
@click.argument("diagnosis_id")
@click.option("--codebase", "-c", type=click.Path(exists=True), required=True)
@click.option("--dry-run", is_flag=True, help="Don't actually apply changes")
def fix(diagnosis_id, codebase, dry_run):
    """Apply a generated fix to the codebase."""
    console.print(Panel.fit("🔧 Applying Fix", style="bold blue"))

    # This would load the fix from storage
    console.print(f"[yellow]Fix application for {diagnosis_id} not fully implemented[/yellow]")
    console.print(f"Codebase: {codebase}")
    console.print(f"Dry run: {dry_run}")


@cli.command()
@click.option("--pr-number", "-n", type=int, required=True)
def pr_status(pr_number):
    """Check status of a pull request."""
    console.print(Panel.fit("📋 PR Status", style="bold blue"))

    try:
        pr_creator = PRCreator()
        status = pr_creator.get_pr_status(pr_number)
        _display_pr_status(status)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


def _display_analysis(analysis):
    """Display log analysis results."""
    console.print("\n[bold]📊 Analysis Results[/bold]")

    # Level distribution
    table = Table(title="Log Level Distribution")
    table.add_column("Level", style="cyan")
    table.add_column("Count", style="magenta")
    table.add_column("Percentage", style="green")

    level_dist = analysis.get("level_distribution", {})
    for level, data in level_dist.items():
        if data["count"] > 0:
            table.add_row(
                level,
                str(data["count"]),
                f"{data['percentage']:.1f}%"
            )

    console.print(table)

    # Error patterns
    patterns = analysis.get("error_patterns", {})
    if patterns:
        console.print("\n[bold]🔍 Error Patterns[/bold]")
        for pattern, data in patterns.items():
            if data["count"] > 0:
                console.print(f"  • {pattern}: {data['count']} occurrences")


def _display_diagnosis(diagnosis):
    """Display AI diagnosis."""
    console.print("\n[bold]🤖 AI Diagnosis[/bold]")
    console.print(Panel(
        f"[bold]Summary:[/bold] {diagnosis.summary}\n\n"
        f"[bold]Root Cause:[/bold] {diagnosis.root_cause}\n\n"
        f"[bold]Severity:[/bold] {diagnosis.severity.value.upper()}\n"
        f"[bold]Category:[/bold] {diagnosis.category.value}\n"
        f"[bold]Confidence:[/bold] {diagnosis.confidence:.1%}",
        title="Diagnosis",
        border_style="blue"
    ))

    if diagnosis.recommendations:
        console.print("\n[bold]💡 Recommendations:[/bold]")
        for rec in diagnosis.recommendations:
            console.print(f"  • {rec}")


def _display_fix(fix):
    """Display generated fix."""
    console.print("\n[bold]🔧 Generated Fix[/bold]")
    console.print(Panel(
        f"[bold]Title:[/bold] {fix.title}\n\n"
        f"[bold]Description:[/bold] {fix.description}\n\n"
        f"[bold]Type:[/bold] {fix.fix_type.value}\n"
        f"[bold]Files:[/bold] {len(fix.file_changes)}",
        title="Fix Details",
        border_style="green"
    ))

    console.print("\n[bold]📝 File Changes:[/bold]")
    for file_path in fix.file_changes.keys():
        console.print(f"  • {file_path}")


def _display_pr(pr):
    """Display PR information."""
    console.print("\n[bold]🚀 Pull Request[/bold]")
    if pr.pr_url:
        console.print(Panel(
            f"[bold]Title:[/bold] {pr.title}\n\n"
            f"[bold]Branch:[/bold] {pr.branch_name}\n"
            f"[bold]PR Number:[/bold] #{pr.pr_number}\n"
            f"[bold]URL:[/bold] {pr.pr_url}\n"
            f"[bold]Status:[/bold] {pr.status.value}",
            title="Pull Request Created ✓",
            border_style="green"
        ))
    else:
        console.print(f"[red]Failed to create PR: {pr.body}[/red]")


def _display_pr_status(status):
    """Display PR status."""
    console.print(f"\n[bold]State:[/bold] {status.get('state')}")
    console.print(f"[bold]Merged:[/bold] {status.get('merged')}")
    console.print(f"[bold]Mergeable:[/bold] {status.get('mergeable')}")

    checks = status.get('checks', [])
    if checks:
        console.print("\n[bold]Checks:[/bold]")
        for check in checks:
            status_icon = "✓" if check['conclusion'] == "success" else "✗"
            console.print(f"  {status_icon} {check['name']}: {check['status']}")


def _display_metrics(metrics):
    """Display system metrics."""
    table = Table(title=f"System Metrics - {metrics.timestamp.strftime('%H:%M:%S')}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    table.add_column("Status", style="green")

    def get_status(value, warning, critical):
        if value >= critical:
            return "🔴 Critical"
        elif value >= warning:
            return "🟡 Warning"
        return "🟢 OK"

    table.add_row(
        "CPU",
        f"{metrics.cpu_percent:.1f}%",
        get_status(metrics.cpu_percent, 70, 90)
    )
    table.add_row(
        "Memory",
        f"{metrics.memory_percent:.1f}%",
        get_status(metrics.memory_percent, 70, 85)
    )
    table.add_row(
        "Disk",
        f"{metrics.disk_usage_percent:.1f}%",
        get_status(metrics.disk_usage_percent, 80, 90)
    )
    table.add_row(
        "Processes",
        str(metrics.process_count),
        "🟢 OK"
    )

    console.print(table)


if __name__ == "__main__":
    cli()
