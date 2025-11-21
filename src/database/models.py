"""SQLAlchemy database models for historical tracking."""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON, ForeignKey, Index
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class AnalysisRun(Base):
    """Tracks each analysis run."""

    __tablename__ = "analysis_runs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), unique=True, index=True)
    run_id = Column(String(100), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Run metadata
    trigger = Column(String(50))  # manual, scheduled, alert, etc.
    status = Column(String(20), default="pending")  # pending, running, completed, failed

    # Analysis parameters
    log_file_path = Column(String(500))
    logs_analyzed = Column(Integer, default=0)

    # Results summary
    anomalies_found = Column(Integer, default=0)
    diagnoses_generated = Column(Integer, default=0)
    fixes_generated = Column(Integer, default=0)
    prs_created = Column(Integer, default=0)

    # Processing metrics
    processing_time_ms = Column(Float)
    success = Column(Boolean, default=True)
    error_message = Column(Text)

    # Relationships
    alerts = relationship("AlertHistory", back_populates="analysis_run", cascade="all, delete-orphan")
    diagnoses = relationship("DiagnosisHistory", back_populates="analysis_run", cascade="all, delete-orphan")
    fixes = relationship("FixHistory", back_populates="analysis_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_analysis_timestamp', 'timestamp'),
        Index('idx_analysis_success', 'success'),
    )


class MetricsSnapshot(Base):
    """Stores system metrics snapshots for historical analysis."""

    __tablename__ = "metrics_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # System metrics
    cpu_percent = Column(Float, nullable=False)
    memory_percent = Column(Float, nullable=False)
    memory_available_mb = Column(Float, nullable=False)
    disk_usage_percent = Column(Float, nullable=False)
    disk_free_gb = Column(Float, nullable=False)
    network_bytes_sent = Column(Integer, nullable=False)
    network_bytes_recv = Column(Integer, nullable=False)
    process_count = Column(Integer, nullable=False)
    load_average = Column(JSON)  # Stores list of floats

    # Derived flags
    cpu_anomaly = Column(Boolean, default=False)
    memory_anomaly = Column(Boolean, default=False)
    disk_anomaly = Column(Boolean, default=False)

    __table_args__ = (
        Index('idx_metrics_timestamp', 'timestamp'),
        Index('idx_metrics_cpu', 'cpu_percent'),
        Index('idx_metrics_memory', 'memory_percent'),
        Index('idx_metrics_anomalies', 'cpu_anomaly', 'memory_anomaly', 'disk_anomaly'),
    )

    @property
    def disk_percent(self):
        """Alias for disk_usage_percent for backwards compatibility."""
        return self.disk_usage_percent


class AlertHistory(Base):
    """Historical record of all alerts sent."""

    __tablename__ = "alert_history"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(100), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Alert details
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(String(20), index=True, nullable=False)
    source = Column(String(100), index=True, nullable=False)

    # Grouping and deduplication
    fingerprint = Column(String(100), index=True)
    group_key = Column(String(100), index=True)

    # Classification
    tags = Column(JSON)  # List of tags
    extra_metadata = Column(JSON)  # Additional metadata

    # Status tracking
    resolved = Column(Boolean, default=False, index=True)
    resolved_at = Column(DateTime)
    resolution_time_minutes = Column(Float)  # Time to resolve

    # Notification results
    channels_sent = Column(JSON)  # List of channels
    notification_success = Column(Boolean, default=True)

    # Relationships
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.id"))
    analysis_run = relationship("AnalysisRun", back_populates="alerts")

    __table_args__ = (
        Index('idx_alert_timestamp', 'timestamp'),
        Index('idx_alert_priority', 'priority'),
        Index('idx_alert_resolved', 'resolved'),
        Index('idx_alert_fingerprint', 'fingerprint'),
    )


class DiagnosisHistory(Base):
    """Historical record of AI diagnoses."""

    __tablename__ = "diagnosis_history"

    id = Column(Integer, primary_key=True, index=True)
    diagnosis_id = Column(String(100), unique=True, index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Diagnosis details
    summary = Column(String(1000), nullable=False)
    root_cause = Column(Text, nullable=False)
    severity = Column(String(20), index=True, nullable=False)
    category = Column(String(50), index=True, nullable=False)

    # Analysis
    affected_files = Column(JSON)  # List of file paths
    recommendations = Column(JSON)  # List of recommendations
    reasoning = Column(Text)
    confidence = Column(Float)

    # Outcome tracking
    fix_applied = Column(Boolean, default=False)
    fix_successful = Column(Boolean)
    user_feedback = Column(String(20))  # helpful, not_helpful, incorrect

    # Relationships
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.id"))
    analysis_run = relationship("AnalysisRun", back_populates="diagnoses")

    __table_args__ = (
        Index('idx_diagnosis_timestamp', 'timestamp'),
        Index('idx_diagnosis_severity', 'severity'),
        Index('idx_diagnosis_category', 'category'),
    )


class FixHistory(Base):
    """Historical record of generated fixes."""

    __tablename__ = "fix_history"

    id = Column(Integer, primary_key=True, index=True)
    fix_id = Column(String(100), unique=True, index=True, nullable=False)
    diagnosis_id = Column(String(100), index=True, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Fix details
    fix_type = Column(String(50), index=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)

    # Changes
    file_changes = Column(JSON)  # Dict of filepath: content
    test_commands = Column(JSON)  # List of test commands

    # Validation
    validation_passed = Column(Boolean, default=False)
    validation_errors = Column(Text)

    # Application tracking
    applied = Column(Boolean, default=False)
    applied_at = Column(DateTime)
    rollback_performed = Column(Boolean, default=False)

    # Effectiveness
    issue_recurred = Column(Boolean)
    time_to_recurrence_hours = Column(Float)

    # Relationships
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.id"))
    analysis_run = relationship("AnalysisRun", back_populates="fixes")
    prs = relationship("PRHistory", back_populates="fix", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_fix_timestamp', 'timestamp'),
        Index('idx_fix_type', 'fix_type'),
        Index('idx_fix_applied', 'applied'),
    )


class PRHistory(Base):
    """Historical record of pull requests."""

    __tablename__ = "pr_history"

    id = Column(Integer, primary_key=True, index=True)
    pr_id = Column(String(100), unique=True, index=True, nullable=False)
    fix_id = Column(String(100), ForeignKey("fix_history.fix_id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # PR details
    pr_number = Column(Integer, index=True)
    pr_url = Column(String(500))
    branch_name = Column(String(200))
    title = Column(String(500), nullable=False)

    # Status
    status = Column(String(20), index=True, nullable=False)  # created, merged, closed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    merged_at = Column(DateTime)
    closed_at = Column(DateTime)

    # Metrics
    time_to_merge_hours = Column(Float)
    commits_count = Column(Integer)
    files_changed = Column(Integer)

    # Reviews and checks
    review_status = Column(String(20))  # approved, changes_requested, pending
    checks_passed = Column(Boolean)
    checks_failed = Column(Integer)

    # Relationships
    fix = relationship("FixHistory", back_populates="prs")

    __table_args__ = (
        Index('idx_pr_timestamp', 'timestamp'),
        Index('idx_pr_status', 'status'),
        Index('idx_pr_merged', 'merged_at'),
    )


class SystemHealthScore(Base):
    """Tracks overall system health score over time."""

    __tablename__ = "system_health_scores"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Scores (0-100)
    overall_score = Column(Float, nullable=False)
    reliability_score = Column(Float, nullable=False)
    performance_score = Column(Float, nullable=False)
    security_score = Column(Float, nullable=False)

    # Metrics
    uptime_percent = Column(Float)
    mttr_minutes = Column(Float)  # Mean Time To Resolution
    alert_count_24h = Column(Integer)
    critical_alerts_24h = Column(Integer)
    issues_resolved_24h = Column(Integer)

    # Trends
    score_trend = Column(String(20))  # improving, stable, declining

    __table_args__ = (
        Index('idx_health_timestamp', 'timestamp'),
        Index('idx_health_score', 'overall_score'),
    )


class IssueRecurrence(Base):
    """Tracks recurring issues for pattern detection."""

    __tablename__ = "issue_recurrences"

    id = Column(Integer, primary_key=True, index=True)

    # Issue identification
    issue_fingerprint = Column(String(100), index=True, nullable=False)
    issue_title = Column(String(500), nullable=False)
    issue_category = Column(String(50), index=True)

    # Recurrence tracking
    first_occurrence = Column(DateTime, nullable=False, index=True)
    last_occurrence = Column(DateTime, nullable=False)
    occurrence_count = Column(Integer, default=1, nullable=False)

    # Pattern analysis
    average_interval_hours = Column(Float)
    is_periodic = Column(Boolean, default=False)
    severity_trend = Column(String(20))  # escalating, stable, decreasing

    # Resolution tracking
    times_fixed = Column(Integer, default=0)
    average_fix_duration_hours = Column(Float)
    permanent_fix_applied = Column(Boolean, default=False)

    __table_args__ = (
        Index('idx_recurrence_fingerprint', 'issue_fingerprint'),
        Index('idx_recurrence_count', 'occurrence_count'),
        Index('idx_recurrence_periodic', 'is_periodic'),
    )


class DataRetentionLog(Base):
    """Logs data retention and cleanup operations."""

    __tablename__ = "data_retention_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Operation details
    operation_type = Column(String(50), nullable=False)  # cleanup, archive, export
    table_name = Column(String(100), nullable=False)

    # Results
    records_affected = Column(Integer, default=0)
    records_deleted = Column(Integer, default=0)
    records_archived = Column(Integer, default=0)

    # Configuration
    retention_days = Column(Integer)
    archive_path = Column(String(500))

    # Status
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    duration_seconds = Column(Float)

    __table_args__ = (
        Index('idx_retention_timestamp', 'timestamp'),
        Index('idx_retention_operation', 'operation_type'),
    )
