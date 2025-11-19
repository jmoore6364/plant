"""
Configuration management module.

Provides configuration loading, validation, and secrets management.
"""

from src.config.loader import ConfigLoader, get_config, get_config_loader, reload_config
from src.config.schema import AppConfig
from src.config.secrets import SecretsManager

# Alias for backward compatibility
settings = get_config()

__all__ = [
    "ConfigLoader",
    "AppConfig",
    "SecretsManager",
    "get_config",
    "get_config_loader",
    "reload_config",
    "settings",
]
