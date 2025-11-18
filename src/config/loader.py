"""
Configuration loader with YAML/TOML support.

Loads configuration from multiple sources with priority:
1. Environment variables (highest priority)
2. Config files (YAML/TOML)
3. Default values (lowest priority)
"""

import os
import yaml
import toml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

from src.config.schema import AppConfig
from src.config.secrets import SecretsManager

logger = logging.getLogger(__name__)


class ConfigFileHandler(FileSystemEventHandler):
    """Watch for config file changes and trigger reload."""

    def __init__(self, config_loader, file_path: str):
        self.config_loader = config_loader
        self.file_path = Path(file_path).resolve()

    def on_modified(self, event):
        if event.is_directory:
            return

        modified_path = Path(event.src_path).resolve()
        if modified_path == self.file_path:
            logger.info(f"Config file changed: {self.file_path}")
            self.config_loader.reload()


class ConfigLoader:
    """Load and manage application configuration."""

    def __init__(
        self,
        config_file: Optional[str] = None,
        environment: Optional[str] = None,
        enable_hot_reload: bool = False,
        enable_secrets: bool = True
    ):
        self.config_file = config_file or self._find_config_file()
        self.environment = environment or os.getenv("APP_ENV", "development")
        self.enable_hot_reload = enable_hot_reload
        self.enable_secrets = enable_secrets

        self._config: Optional[AppConfig] = None
        self._raw_config: Dict[str, Any] = {}
        self._observer: Optional[Observer] = None
        self._lock = threading.RLock()

        # Initialize secrets manager
        self.secrets_manager = None
        if enable_secrets:
            self.secrets_manager = SecretsManager()

        # Load initial configuration
        self.load()

        # Set up hot reload if enabled
        if enable_hot_reload and self.config_file:
            self._setup_hot_reload()

    def _find_config_file(self) -> Optional[str]:
        """Find config file in common locations."""
        possible_locations = [
            os.getenv("CONFIG_FILE"),
            "config.yaml",
            "config.yml",
            "config.toml",
            "config/app.yaml",
            "config/app.yml",
            "config/app.toml",
        ]

        for location in possible_locations:
            if location and Path(location).exists():
                return location

        return None

    def _load_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {file_path}")

        suffix = path.suffix.lower()

        try:
            with open(path, 'r') as f:
                if suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f) or {}
                elif suffix == '.toml':
                    return toml.load(f)
                else:
                    raise ValueError(f"Unsupported config file format: {suffix}")
        except Exception as e:
            logger.error(f"Error loading config file {file_path}: {e}")
            raise

    def _merge_environment_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge environment-specific configuration."""
        if self.environment in config:
            env_config = config[self.environment]
            # Merge environment config with defaults
            merged = config.get("default", {}).copy()
            merged.update(env_config)
            return merged

        return config.get("default", config)

    def _apply_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Override config with environment variables."""
        # Map of env vars to config paths
        env_mappings = {
            "DATABASE_URL": ["database", "url"],
            "LOG_LEVEL": ["logging", "level"],
            "API_HOST": ["api", "host"],
            "API_PORT": ["api", "port"],
            "ANTHROPIC_API_KEY": ["ai", "anthropic_api_key"],
            "OPENAI_API_KEY": ["ai", "openai_api_key"],
            "GITHUB_TOKEN": ["github", "token"],
            "SLACK_WEBHOOK": ["notifications", "slack", "webhook_url"],
            "SLACK_TOKEN": ["notifications", "slack", "token"],
            "DISCORD_WEBHOOK": ["notifications", "discord", "webhook_url"],
            "PAGERDUTY_API_KEY": ["notifications", "pagerduty", "api_key"],
            "REDIS_URL": ["cache", "redis_url"],
        }

        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value:
                # Navigate to nested dict and set value
                current = config
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                current[config_path[-1]] = value

        return config

    def _load_secrets(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Load secrets from secrets manager."""
        if not self.secrets_manager:
            return config

        # Identify secret placeholders (format: ${secret:path/to/secret})
        def replace_secrets(obj):
            if isinstance(obj, dict):
                return {k: replace_secrets(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_secrets(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${secret:"):
                # Extract secret path
                secret_path = obj[9:-1]  # Remove ${secret: and }
                secret_value = self.secrets_manager.get_secret(secret_path)
                return secret_value if secret_value else obj
            else:
                return obj

        return replace_secrets(config)

    def load(self) -> AppConfig:
        """Load configuration from all sources."""
        with self._lock:
            try:
                # Start with empty config
                config = {}

                # Load from file if exists
                if self.config_file:
                    logger.info(f"Loading config from: {self.config_file}")
                    config = self._load_file(self.config_file)

                # Merge environment-specific config
                config = self._merge_environment_config(config)

                # Apply environment variables (highest priority)
                config = self._apply_environment_variables(config)

                # Load secrets
                if self.enable_secrets:
                    config = self._load_secrets(config)

                # Store raw config
                self._raw_config = config

                # Validate and create typed config
                self._config = AppConfig(**config)

                logger.info(f"Configuration loaded successfully (environment: {self.environment})")
                return self._config

            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
                raise

    def reload(self):
        """Reload configuration from sources."""
        logger.info("Reloading configuration...")
        try:
            self.load()
            logger.info("Configuration reloaded successfully")
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")

    def _setup_hot_reload(self):
        """Set up file watcher for hot reload."""
        if not self.config_file:
            return

        try:
            config_path = Path(self.config_file).parent
            event_handler = ConfigFileHandler(self, self.config_file)

            self._observer = Observer()
            self._observer.schedule(event_handler, str(config_path), recursive=False)
            self._observer.start()

            logger.info(f"Hot reload enabled for: {self.config_file}")
        except Exception as e:
            logger.error(f"Error setting up hot reload: {e}")

    def stop_hot_reload(self):
        """Stop file watcher."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            logger.info("Hot reload stopped")

    def get(self) -> AppConfig:
        """Get current configuration."""
        with self._lock:
            if not self._config:
                self.load()
            return self._config

    def get_raw(self) -> Dict[str, Any]:
        """Get raw configuration dict."""
        with self._lock:
            return self._raw_config.copy()

    def update(self, **kwargs):
        """Update configuration values."""
        with self._lock:
            if not self._config:
                self.load()

            # Update config object
            for key, value in kwargs.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_hot_reload()


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """Get global config loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader(
            enable_hot_reload=os.getenv("ENABLE_HOT_RELOAD", "false").lower() == "true"
        )
    return _config_loader


def get_config() -> AppConfig:
    """Get current application configuration."""
    return get_config_loader().get()


def reload_config():
    """Reload application configuration."""
    get_config_loader().reload()
