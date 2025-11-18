"""Automated fix generation and application."""

from typing import List, Optional, Dict
from pathlib import Path
import subprocess
import tempfile
import shutil

from src.models.schemas import (
    LogEntry,
    SystemMetrics,
    Anomaly,
    Diagnosis,
    GeneratedFix,
    FixType,
)
from src.ai.llm_client import LLMClient
from src.analyzers.log_analyzer import LogAnalyzer
from src.analyzers.anomaly_detector import AnomalyDetector


class AutoFixer:
    """Automatically generates and applies fixes for detected issues."""

    def __init__(self, llm_client: Optional[LLMClient] = None) -> None:
        """
        Initialize the auto fixer.

        Args:
            llm_client: LLM client for fix generation (creates new one if not provided)
        """
        self.llm_client = llm_client or LLMClient()
        self.log_analyzer = LogAnalyzer()
        self.fix_templates = self._load_fix_templates()

    def analyze_and_diagnose(
        self,
        logs: List[LogEntry],
        metrics: Optional[SystemMetrics] = None,
        anomalies: Optional[List[Anomaly]] = None,
    ) -> Diagnosis:
        """
        Analyze logs and generate diagnosis.

        Args:
            logs: Log entries to analyze
            metrics: System metrics (optional)
            anomalies: Detected anomalies (optional)

        Returns:
            Diagnosis from LLM analysis
        """
        # Analyze logs if no anomalies provided
        if anomalies is None:
            log_analysis = self.log_analyzer.analyze(logs)
            anomalies = log_analysis.get("anomalies", [])

        # Generate diagnosis using LLM
        diagnosis = self.llm_client.analyze_logs(logs, anomalies, metrics)

        return diagnosis

    def generate_fix(
        self, diagnosis: Diagnosis, codebase_path: Optional[str] = None
    ) -> GeneratedFix:
        """
        Generate fix for diagnosed issue.

        Args:
            diagnosis: Issue diagnosis
            codebase_path: Path to codebase for context

        Returns:
            Generated fix with code changes
        """
        # Get codebase context if path provided
        codebase_context = None
        if codebase_path and diagnosis.affected_files:
            codebase_context = self._get_codebase_context(
                codebase_path, diagnosis.affected_files
            )

        # Try template-based fix first
        template_fix = self._try_template_fix(diagnosis)
        if template_fix:
            return template_fix

        # Generate fix using LLM
        fix = self.llm_client.generate_fix(diagnosis, codebase_context)

        return fix

    def validate_fix(self, fix: GeneratedFix, codebase_path: str) -> bool:
        """
        Validate a generated fix.

        Args:
            fix: Fix to validate
            codebase_path: Path to codebase

        Returns:
            True if fix is valid
        """
        # Create temporary directory for validation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy codebase to temp directory
            temp_codebase = Path(temp_dir) / "codebase"
            shutil.copytree(codebase_path, temp_codebase, symlinks=True)

            try:
                # Apply changes
                for file_path, content in fix.file_changes.items():
                    full_path = temp_codebase / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content)

                # Run validation commands
                for test_cmd in fix.test_commands:
                    if not self._run_test_command(test_cmd, str(temp_codebase)):
                        return False

                return True

            except Exception as e:
                print(f"Validation error: {e}")
                return False

    def apply_fix(
        self, fix: GeneratedFix, codebase_path: str, dry_run: bool = False
    ) -> bool:
        """
        Apply fix to actual codebase.

        Args:
            fix: Fix to apply
            codebase_path: Path to codebase
            dry_run: If True, don't actually apply changes

        Returns:
            True if successful
        """
        if dry_run:
            print("DRY RUN - Changes that would be made:")
            for file_path, content in fix.file_changes.items():
                print(f"  - {file_path} ({len(content)} bytes)")
            return True

        try:
            codebase = Path(codebase_path)

            # Apply changes
            for file_path, content in fix.file_changes.items():
                full_path = codebase / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Backup original file
                if full_path.exists():
                    backup_path = full_path.with_suffix(full_path.suffix + ".bak")
                    shutil.copy(full_path, backup_path)

                # Write new content
                full_path.write_text(content)

            return True

        except Exception as e:
            print(f"Error applying fix: {e}")
            return False

    def _load_fix_templates(self) -> Dict[str, Dict]:
        """Load predefined fix templates for common issues."""
        return {
            "memory_leak": {
                "pattern": r"out of memory|oom",
                "fix_type": FixType.CONFIG_UPDATE,
                "template": {
                    "docker-compose.yml": """
services:
  app:
    mem_limit: 2g
    mem_reservation: 1g
""",
                },
            },
            "connection_pool": {
                "pattern": r"too many connections|connection pool",
                "fix_type": FixType.CONFIG_UPDATE,
                "template": {
                    "config/database.yml": """
pool:
  max_size: 20
  min_size: 5
  timeout: 30
""",
                },
            },
            "missing_error_handling": {
                "pattern": r"uncaught exception|unhandled error",
                "fix_type": FixType.CODE_CHANGE,
                "template": None,  # Requires LLM generation
            },
        }

    def _try_template_fix(self, diagnosis: Diagnosis) -> Optional[GeneratedFix]:
        """Try to apply a template-based fix."""
        # Check if diagnosis matches any template
        for template_name, template_data in self.fix_templates.items():
            # Simple pattern matching (could be more sophisticated)
            if template_data.get("template") and any(
                template_name in rec.lower() for rec in diagnosis.recommendations
            ):
                return GeneratedFix(
                    fix_id=f"template_fix_{diagnosis.issue_id}",
                    diagnosis_id=diagnosis.issue_id,
                    fix_type=template_data["fix_type"],
                    title=f"Apply {template_name} fix",
                    description=f"Template-based fix for {template_name}",
                    file_changes=template_data["template"],
                    test_commands=["echo 'Template fix applied'"],
                    rollback_plan="Restore from backup",
                    estimated_impact="Low",
                )

        return None

    def _get_codebase_context(
        self, codebase_path: str, affected_files: List[str]
    ) -> str:
        """Get context from affected files in codebase."""
        context_parts = []
        codebase = Path(codebase_path)

        for file_path in affected_files[:5]:  # Limit to 5 files
            full_path = codebase / file_path
            if full_path.exists() and full_path.is_file():
                try:
                    content = full_path.read_text(encoding="utf-8", errors="ignore")
                    # Limit content size
                    if len(content) > 5000:
                        content = content[:5000] + "\n... (truncated)"
                    context_parts.append(f"**{file_path}**:\n```\n{content}\n```\n")
                except Exception:
                    pass

        return "\n".join(context_parts)

    def _run_test_command(self, command: str, cwd: str) -> bool:
        """Run a test command and return success status."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                timeout=60,
                text=True,
            )
            return result.returncode == 0
        except subprocess.TimeoutExpired:
            print(f"Test command timed out: {command}")
            return False
        except Exception as e:
            print(f"Error running test: {e}")
            return False

    def create_fix_report(
        self, diagnosis: Diagnosis, fix: GeneratedFix, validation_result: bool
    ) -> str:
        """
        Create a detailed report about the fix.

        Args:
            diagnosis: Issue diagnosis
            fix: Generated fix
            validation_result: Whether validation passed

        Returns:
            Markdown-formatted report
        """
        report = f"""# Fix Report

## Issue Summary
**Severity**: {diagnosis.severity.value.upper()}
**Category**: {diagnosis.category.value}
**Summary**: {diagnosis.summary}

## Root Cause
{diagnosis.root_cause}

## Generated Fix
**Type**: {fix.fix_type.value}
**Title**: {fix.title}
**Description**: {fix.description}

## Changes
"""
        for file_path in fix.file_changes.keys():
            report += f"- `{file_path}`\n"

        report += f"""
## Testing
"""
        for cmd in fix.test_commands:
            report += f"- `{cmd}`\n"

        report += f"""
## Validation
**Status**: {'✅ PASSED' if validation_result else '❌ FAILED'}

## Impact
{fix.estimated_impact}

## Rollback Plan
{fix.rollback_plan}

## Recommendations
"""
        for rec in diagnosis.recommendations:
            report += f"- {rec}\n"

        return report
