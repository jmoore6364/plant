"""
Configuration schema with Pydantic validation.

Defines the structure and validation rules for application configuration.
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List, Dict, Any
from enum import Enum


class LogLevel(str, Enum):
    """Supported log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Environment(str, Enum):
    """Supported environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: str = Field(
        default="sqlite+aiosqlite:///./data/system_health.db",
        description="Database connection URL"
    )
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=100)
    pool_timeout: int = Field(default=30, ge=1, le=300)
    echo: bool = Field(default=False, description="Echo SQL queries")

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v:
            raise ValueError("Database URL cannot be empty")
        return v


class AIConfig(BaseModel):
    """AI service configuration."""
    provider: str = Field(default="anthropic", description="AI provider (anthropic/openai)")
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    model: str = Field(default="claude-3-sonnet-20240229")
    max_tokens: int = Field(default=4096, ge=100, le=100000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout: int = Field(default=120, ge=10, le=600)

    @model_validator(mode='after')
    def validate_api_keys(self):
        # Only enforce API keys in production or when explicitly configured
        import os
        env = os.getenv('APP_ENV', 'development')
        if env == 'production':
            if self.provider == 'anthropic' and not self.anthropic_api_key:
                raise ValueError("anthropic_api_key required when provider is 'anthropic'")
            if self.provider == 'openai' and not self.openai_api_key:
                raise ValueError("openai_api_key required when provider is 'openai'")
        return self


class APIConfig(BaseModel):
    """API server configuration."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1, le=32)
    reload: bool = Field(default=False)
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    request_timeout: int = Field(default=300, ge=10, le=3600)


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: LogLevel = Field(default=LogLevel.INFO)
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file: Optional[str] = None
    max_bytes: int = Field(default=10485760, ge=1024)  # 10MB
    backup_count: int = Field(default=5, ge=1, le=100)


class SlackNotificationConfig(BaseModel):
    """Slack notification configuration."""
    enabled: bool = True
    webhook_url: Optional[str] = None
    token: Optional[str] = None
    channel: str = "#alerts"
    username: str = "System Health Bot"


class DiscordNotificationConfig(BaseModel):
    """Discord notification configuration."""
    enabled: bool = False
    webhook_url: Optional[str] = None
    username: str = "System Health Bot"


class EmailNotificationConfig(BaseModel):
    """Email notification configuration."""
    enabled: bool = False
    smtp_host: Optional[str] = None
    smtp_port: int = Field(default=587, ge=1, le=65535)
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    from_address: Optional[str] = None
    to_addresses: List[str] = Field(default_factory=list)
    use_tls: bool = True


class PagerDutyNotificationConfig(BaseModel):
    """PagerDuty notification configuration."""
    enabled: bool = False
    api_key: Optional[str] = None
    integration_key: Optional[str] = None
    service_id: Optional[str] = None


class NotificationsConfig(BaseModel):
    """Notifications configuration."""
    slack: SlackNotificationConfig = Field(default_factory=SlackNotificationConfig)
    discord: DiscordNotificationConfig = Field(default_factory=DiscordNotificationConfig)
    email: EmailNotificationConfig = Field(default_factory=EmailNotificationConfig)
    pagerduty: PagerDutyNotificationConfig = Field(default_factory=PagerDutyNotificationConfig)
    deduplication_window_minutes: int = Field(default=30, ge=1, le=1440)


class GitHubConfig(BaseModel):
    """GitHub integration configuration."""
    token: Optional[str] = None
    repo: Optional[str] = None
    default_branch: str = "main"
    create_prs: bool = True
    auto_merge: bool = False


class CacheConfig(BaseModel):
    """Cache configuration."""
    enabled: bool = True
    redis_url: Optional[str] = Field(default="redis://localhost:6379/0")
    ttl_seconds: int = Field(default=300, ge=10, le=86400)
    max_connections: int = Field(default=10, ge=1, le=100)


class SecurityConfig(BaseModel):
    """Security configuration."""
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = Field(default=1440, ge=15, le=43200)  # 1 day default
    api_keys_enabled: bool = True
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_period_seconds: int = Field(default=60, ge=1)
    cors_enabled: bool = True
    allowed_hosts: List[str] = Field(default_factory=lambda: ["*"])


class MonitoringConfig(BaseModel):
    """Monitoring and observability configuration."""
    metrics_enabled: bool = True
    prometheus_enabled: bool = False
    prometheus_port: int = Field(default=9090, ge=1, le=65535)
    tracing_enabled: bool = False
    jaeger_host: Optional[str] = None


class RetentionConfig(BaseModel):
    """Data retention configuration."""
    metrics_days: int = Field(default=30, ge=1, le=365)
    alerts_days: int = Field(default=90, ge=1, le=730)
    diagnoses_days: int = Field(default=180, ge=1, le=730)
    fixes_days: int = Field(default=180, ge=1, le=730)
    prs_days: int = Field(default=365, ge=1, le=1825)
    auto_cleanup_enabled: bool = True
    cleanup_schedule_cron: str = "0 2 * * *"  # 2 AM daily


class FeatureFlagsConfig(BaseModel):
    """Feature flags configuration."""
    ai_analysis: bool = True
    auto_fix: bool = False
    auto_pr: bool = False
    notifications: bool = True
    database: bool = True
    cache: bool = True
    monitoring: bool = False


class AppConfig(BaseModel):
    """Main application configuration."""

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT)
    debug: bool = Field(default=False)

    # Component configs
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    api: APIConfig = Field(default_factory=APIConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    notifications: NotificationsConfig = Field(default_factory=NotificationsConfig)
    github: GitHubConfig = Field(default_factory=GitHubConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    retention: RetentionConfig = Field(default_factory=RetentionConfig)
    feature_flags: FeatureFlagsConfig = Field(default_factory=FeatureFlagsConfig)

    # Custom settings
    custom: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
        validate_assignment = True

    @field_validator('environment')
    @classmethod
    def validate_environment(cls, v):
        if isinstance(v, str):
            return Environment(v.lower())
        return v

    @model_validator(mode='after')
    def validate_production_settings(self):
        """Validate critical production settings."""
        if self.environment == Environment.PRODUCTION:
            # Ensure critical settings are configured for production
            if self.security.jwt_secret_key == "change-me-in-production":
                raise ValueError(
                    "JWT secret key must be changed in production environment"
                )

            if self.database.url.startswith("sqlite"):
                import warnings
                warnings.warn(
                    "SQLite is not recommended for production use",
                    UserWarning
                )

        return self

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == Environment.DEVELOPMENT

    def is_testing(self) -> bool:
        """Check if running in testing."""
        return self.environment == Environment.TESTING
