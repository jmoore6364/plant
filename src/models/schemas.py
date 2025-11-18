"""Pydantic schemas for data validation and serialization."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class LogLevel(str, Enum):
    """Log severity levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """Supported log formats."""

    SYSLOG = "syslog"
    JSON = "json"
    APACHE = "apache"
    NGINX = "nginx"
    CUSTOM = "custom"


class LogEntry(BaseModel):
    """Represents a single log entry."""

    timestamp: datetime
    level: LogLevel
    message: str
    source: str
    raw_line: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    line_number: Optional[int] = None


class SystemMetrics(BaseModel):
    """System resource metrics."""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    load_average: Optional[List[float]] = None


class AnomalyType(str, Enum):
    """Types of detected anomalies."""

    CPU_SPIKE = "cpu_spike"
    MEMORY_LEAK = "memory_leak"
    DISK_FULL = "disk_full"
    ERROR_BURST = "error_burst"
    SLOW_RESPONSE = "slow_response"
    CRASH_PATTERN = "crash_pattern"
    UNUSUAL_TRAFFIC = "unusual_traffic"


class Anomaly(BaseModel):
    """Detected anomaly in logs or metrics."""

    id: str
    type: AnomalyType
    severity: str  # "low", "medium", "high", "critical"
    timestamp: datetime
    description: str
    affected_component: str
    confidence_score: float
    evidence: List[str] = Field(default_factory=list)
    metrics: Optional[SystemMetrics] = None
    logs: List[LogEntry] = Field(default_factory=list)


class IssueSeverity(str, Enum):
    """Issue severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IssueCategory(str, Enum):
    """Categories of identified issues."""

    PERFORMANCE = "performance"
    SECURITY = "security"
    RELIABILITY = "reliability"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    CODE_ERROR = "code_error"


class Diagnosis(BaseModel):
    """AI-generated diagnosis of an issue."""

    issue_id: str
    summary: str
    root_cause: str
    severity: IssueSeverity
    category: IssueCategory
    affected_files: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    reasoning: str
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FixType(str, Enum):
    """Types of fixes that can be generated."""

    CODE_CHANGE = "code_change"
    CONFIG_UPDATE = "config_update"
    DEPENDENCY_UPDATE = "dependency_update"
    INFRASTRUCTURE = "infrastructure"
    DOCUMENTATION = "documentation"


class GeneratedFix(BaseModel):
    """AI-generated fix for an issue."""

    fix_id: str
    diagnosis_id: str
    fix_type: FixType
    title: str
    description: str
    file_changes: Dict[str, str] = Field(default_factory=dict)  # filepath: new_content
    validation_passed: bool = False
    test_commands: List[str] = Field(default_factory=list)
    rollback_plan: str = ""
    estimated_impact: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PRStatus(str, Enum):
    """Status of a pull request."""

    CREATED = "created"
    UPDATED = "updated"
    MERGED = "merged"
    CLOSED = "closed"
    FAILED = "failed"


class PullRequest(BaseModel):
    """Pull request information."""

    pr_id: str
    fix_id: str
    branch_name: str
    pr_number: Optional[int] = None
    pr_url: Optional[str] = None
    title: str
    body: str
    status: PRStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    merged_at: Optional[datetime] = None


class AnalysisRequest(BaseModel):
    """Request for log/metrics analysis."""

    log_file_path: Optional[str] = None
    log_content: Optional[str] = None
    metrics: Optional[SystemMetrics] = None
    include_ai_analysis: bool = True
    auto_fix: bool = False
    auto_pr: bool = False


class AnalysisResult(BaseModel):
    """Result of analysis."""

    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    logs_analyzed: int = 0
    anomalies: List[Anomaly] = Field(default_factory=list)
    diagnoses: List[Diagnosis] = Field(default_factory=list)
    fixes: List[GeneratedFix] = Field(default_factory=list)
    prs: List[PullRequest] = Field(default_factory=list)
    summary: str = ""
    processing_time_ms: float = 0.0
