"""LLM client for AI-powered analysis and code generation."""

from typing import List, Optional, Dict, Any
from anthropic import Anthropic
import json
from datetime import datetime

from src.config import settings
from src.models.schemas import (
    LogEntry,
    SystemMetrics,
    Anomaly,
    Diagnosis,
    IssueSeverity,
    IssueCategory,
    GeneratedFix,
    FixType,
)


class LLMClient:
    """Client for interacting with LLMs (Claude, GPT-4) for analysis."""

    def __init__(self, provider: str = "anthropic") -> None:
        """
        Initialize the LLM client.

        Args:
            provider: LLM provider ("anthropic" or "openai")
        """
        self.provider = provider

        if provider == "anthropic":
            if not settings.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            self.model = "claude-3-5-sonnet-20241022"
        elif provider == "openai":
            if not settings.openai_api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.model = "gpt-4-turbo-preview"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def analyze_logs(
        self,
        logs: List[LogEntry],
        anomalies: Optional[List[Anomaly]] = None,
        metrics: Optional[SystemMetrics] = None,
    ) -> Diagnosis:
        """
        Analyze logs using LLM to generate diagnosis.

        Args:
            logs: Log entries to analyze
            anomalies: Detected anomalies (optional)
            metrics: Current system metrics (optional)

        Returns:
            Diagnosis object with AI analysis
        """
        # Build context
        context = self._build_log_context(logs, anomalies, metrics)

        # Create prompt
        prompt = f"""You are an expert DevOps engineer analyzing system logs and metrics.

Analyze the following data and provide a diagnosis:

{context}

Provide your analysis in the following JSON format:
{{
    "summary": "Brief summary of the issue",
    "root_cause": "Detailed explanation of the root cause",
    "severity": "low|medium|high|critical",
    "category": "performance|security|reliability|resource|configuration|code_error",
    "affected_files": ["list", "of", "files"],
    "recommendations": ["list", "of", "recommendations"],
    "reasoning": "Step-by-step reasoning for your diagnosis",
    "confidence": 0.85
}}

Focus on:
1. Identifying the root cause of errors or anomalies
2. Assessing impact and severity
3. Providing actionable recommendations
4. Identifying specific files or components affected"""

        # Call LLM
        response = self._call_llm(prompt)

        # Parse response
        try:
            analysis = json.loads(response)
        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            analysis = {
                "summary": "Analysis completed",
                "root_cause": response[:500],
                "severity": "medium",
                "category": "reliability",
                "affected_files": [],
                "recommendations": ["Review the detailed analysis"],
                "reasoning": response,
                "confidence": 0.7,
            }

        # Create Diagnosis object
        return Diagnosis(
            issue_id=f"issue_{datetime.utcnow().isoformat()}",
            summary=analysis.get("summary", ""),
            root_cause=analysis.get("root_cause", ""),
            severity=IssueSeverity(analysis.get("severity", "medium")),
            category=IssueCategory(analysis.get("category", "reliability")),
            affected_files=analysis.get("affected_files", []),
            recommendations=analysis.get("recommendations", []),
            reasoning=analysis.get("reasoning", ""),
            confidence=analysis.get("confidence", 0.7),
        )

    def generate_fix(
        self, diagnosis: Diagnosis, codebase_context: Optional[str] = None
    ) -> GeneratedFix:
        """
        Generate code fix based on diagnosis.

        Args:
            diagnosis: Issue diagnosis
            codebase_context: Optional context about the codebase

        Returns:
            GeneratedFix with code changes
        """
        prompt = f"""You are an expert software engineer. Generate a fix for the following diagnosed issue:

**Summary**: {diagnosis.summary}
**Root Cause**: {diagnosis.root_cause}
**Category**: {diagnosis.category}
**Severity**: {diagnosis.severity}
**Affected Files**: {', '.join(diagnosis.affected_files) if diagnosis.affected_files else 'Unknown'}

**Recommendations**:
{chr(10).join(f"- {rec}" for rec in diagnosis.recommendations)}

{f"**Codebase Context**:{chr(10)}{codebase_context}" if codebase_context else ""}

Generate a fix in the following JSON format:
{{
    "fix_type": "code_change|config_update|dependency_update|infrastructure|documentation",
    "title": "Clear title for the fix",
    "description": "Detailed description of what the fix does",
    "file_changes": {{
        "path/to/file.py": "complete new file content or patch",
        "path/to/config.yml": "updated config"
    }},
    "test_commands": ["pytest tests/", "npm test"],
    "rollback_plan": "Steps to rollback if needed",
    "estimated_impact": "Description of impact"
}}

Generate production-ready code that:
1. Fixes the root cause
2. Includes error handling
3. Follows best practices
4. Is well-commented
5. Includes validation"""

        response = self._call_llm(prompt)

        try:
            fix_data = json.loads(response)
        except json.JSONDecodeError:
            # Fallback
            fix_data = {
                "fix_type": "code_change",
                "title": f"Fix for {diagnosis.summary}",
                "description": response[:500],
                "file_changes": {},
                "test_commands": [],
                "rollback_plan": "Revert commit",
                "estimated_impact": "Medium",
            }

        return GeneratedFix(
            fix_id=f"fix_{datetime.utcnow().isoformat()}",
            diagnosis_id=diagnosis.issue_id,
            fix_type=FixType(fix_data.get("fix_type", "code_change")),
            title=fix_data.get("title", ""),
            description=fix_data.get("description", ""),
            file_changes=fix_data.get("file_changes", {}),
            test_commands=fix_data.get("test_commands", []),
            rollback_plan=fix_data.get("rollback_plan", ""),
            estimated_impact=fix_data.get("estimated_impact", ""),
        )

    def create_pr_description(
        self, diagnosis: Diagnosis, fix: GeneratedFix
    ) -> Dict[str, str]:
        """
        Create PR title and description.

        Args:
            diagnosis: Issue diagnosis
            fix: Generated fix

        Returns:
            Dictionary with 'title' and 'body'
        """
        prompt = f"""Create a GitHub pull request title and description for the following fix:

**Issue**: {diagnosis.summary}
**Severity**: {diagnosis.severity}
**Fix**: {fix.title}
**Description**: {fix.description}

**Changes**:
{chr(10).join(f"- {file}" for file in fix.file_changes.keys())}

Create a professional PR in this format:
{{
    "title": "Concise PR title (< 72 chars)",
    "body": "Markdown formatted PR description with:\\n## Problem\\n## Solution\\n## Testing\\n## Impact"
}}"""

        response = self._call_llm(prompt)

        try:
            pr_data = json.loads(response)
            return {
                "title": pr_data.get("title", fix.title),
                "body": pr_data.get("body", fix.description),
            }
        except json.JSONDecodeError:
            return {
                "title": fix.title[:72],
                "body": f"""## Problem
{diagnosis.summary}

## Solution
{fix.description}

## Root Cause
{diagnosis.root_cause}

## Testing
{chr(10).join(f"- `{cmd}`" for cmd in fix.test_commands)}

## Impact
{fix.estimated_impact}
""",
            }

    def _build_log_context(
        self,
        logs: List[LogEntry],
        anomalies: Optional[List[Anomaly]] = None,
        metrics: Optional[SystemMetrics] = None,
    ) -> str:
        """Build context string from logs, anomalies, and metrics."""
        context_parts = []

        # Add metrics
        if metrics:
            context_parts.append(f"""**System Metrics**:
- CPU: {metrics.cpu_percent:.1f}%
- Memory: {metrics.memory_percent:.1f}% ({metrics.memory_available_mb:.0f} MB available)
- Disk: {metrics.disk_usage_percent:.1f}% ({metrics.disk_free_gb:.2f} GB free)
- Processes: {metrics.process_count}
""")

        # Add anomalies
        if anomalies:
            context_parts.append("**Detected Anomalies**:")
            for anomaly in anomalies[:5]:  # Limit to 5
                context_parts.append(f"- [{anomaly.severity}] {anomaly.description}")
                if anomaly.evidence:
                    context_parts.append(f"  Evidence: {', '.join(anomaly.evidence[:3])}")
            context_parts.append("")

        # Add log summary
        error_logs = [log for log in logs if log.level.value in ("ERROR", "CRITICAL")]
        context_parts.append(f"**Logs Summary**:")
        context_parts.append(f"- Total logs: {len(logs)}")
        context_parts.append(f"- Errors: {len(error_logs)}")
        context_parts.append("")

        # Add sample error logs
        if error_logs:
            context_parts.append("**Sample Error Logs**:")
            for log in error_logs[:10]:  # Limit to 10
                timestamp = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                context_parts.append(f"[{timestamp}] [{log.level.value}] {log.message[:200]}")
            context_parts.append("")

        return "\n".join(context_parts)

    def _call_llm(self, prompt: str, max_tokens: int = 4096) -> str:
        """Call the LLM with the given prompt."""
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content

        raise ValueError(f"Unsupported provider: {self.provider}")
