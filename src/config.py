"""Configuration management for the application."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AI API Keys
    anthropic_api_key: str = Field(default="", env="ANTHROPIC_API_KEY")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")

    # GitHub Configuration
    github_token: str = Field(default="", env="GITHUB_TOKEN")
    github_repo: str = Field(default="", env="GITHUB_REPO")
    github_default_branch: str = Field(default="main", env="GITHUB_DEFAULT_BRANCH")

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./plant.db", env="DATABASE_URL"
    )

    # API Configuration
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=True, env="API_RELOAD")

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env="SENTRY_DSN")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Analysis Settings
    anomaly_threshold: float = Field(default=0.85, env="ANOMALY_THRESHOLD")
    metrics_interval: int = Field(default=60, env="METRICS_INTERVAL")
    log_batch_size: int = Field(default=1000, env="LOG_BATCH_SIZE")

    # Auto-Fix Settings
    auto_fix_enabled: bool = Field(default=True, env="AUTO_FIX_ENABLED")
    auto_pr_enabled: bool = Field(default=False, env="AUTO_PR_ENABLED")
    require_approval: bool = Field(default=True, env="REQUIRE_APPROVAL")

    # Notification Settings
    notifications_enabled: bool = Field(default=True, env="NOTIFICATIONS_ENABLED")

    # Slack
    slack_webhook_url: Optional[str] = Field(default=None, env="SLACK_WEBHOOK_URL")
    slack_api_token: Optional[str] = Field(default=None, env="SLACK_API_TOKEN")
    slack_channel: Optional[str] = Field(default=None, env="SLACK_CHANNEL")

    # Discord
    discord_webhook_url: Optional[str] = Field(default=None, env="DISCORD_WEBHOOK_URL")

    # Email
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from_email: Optional[str] = Field(default=None, env="SMTP_FROM_EMAIL")
    smtp_to_emails: Optional[str] = Field(default=None, env="SMTP_TO_EMAILS")  # Comma-separated

    # PagerDuty
    pagerduty_integration_key: Optional[str] = Field(default=None, env="PAGERDUTY_INTEGRATION_KEY")

    # Alert Settings
    alert_dedup_window_minutes: int = Field(default=15, env="ALERT_DEDUP_WINDOW_MINUTES")
    alert_cooldown_minutes: int = Field(default=15, env="ALERT_COOLDOWN_MINUTES")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
