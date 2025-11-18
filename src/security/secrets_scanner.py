"""
Secrets scanning for logs and output.

Detects and redacts sensitive information like API keys, passwords, tokens, etc.
"""

import re
import logging
from typing import List, Dict, Pattern

logger = logging.getLogger(__name__)


class SecretsScanner:
    """Scan and redact secrets from text."""

    # Regex patterns for common secrets
    PATTERNS: Dict[str, Pattern] = {
        "api_key": re.compile(r'\b[A-Za-z0-9]{32,}\b'),
        "aws_access_key": re.compile(r'AKIA[0-9A-Z]{16}'),
        "aws_secret_key": re.compile(r'[A-Za-z0-9/+=]{40}'),
        "github_token": re.compile(r'gh[pousr]_[A-Za-z0-9]{36,}'),
        "slack_token": re.compile(r'xox[baprs]-[0-9]{10,13}-[0-9]{10,13}-[A-Za-z0-9]{24,}'),
        "slack_webhook": re.compile(r'https://hooks\.slack\.com/services/T[A-Z0-9]{8,}/B[A-Z0-9]{8,}/[A-Za-z0-9]{24}'),
        "private_key": re.compile(r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----'),
        "jwt": re.compile(r'eyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*'),
        "password": re.compile(r'(password|passwd|pwd)["\']?\s*[:=]\s*["\']?([^\s"\']+)', re.IGNORECASE),
        "connection_string": re.compile(r'(mongodb|mysql|postgresql|redis)://[^\s]+'),
        "credit_card": re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b'),
        "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
        "ipv4_private": re.compile(r'\b(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3})\b'),
    }

    REDACTION_TEXT = "[REDACTED]"

    @classmethod
    def scan(cls, text: str) -> List[Dict[str, str]]:
        """
        Scan text for secrets.

        Args:
            text: Text to scan

        Returns:
            List of detected secrets with type and position
        """
        secrets = []

        for secret_type, pattern in cls.PATTERNS.items():
            matches = pattern.finditer(text)
            for match in matches:
                secrets.append({
                    "type": secret_type,
                    "value": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                })

        return secrets

    @classmethod
    def redact(cls, text: str, replacement: str = REDACTION_TEXT) -> str:
        """
        Redact secrets from text.

        Args:
            text: Text to redact
            replacement: Replacement text for secrets

        Returns:
            Redacted text
        """
        redacted = text

        for secret_type, pattern in cls.PATTERNS.items():
            redacted = pattern.sub(replacement, redacted)

        return redacted

    @classmethod
    def is_sensitive(cls, text: str) -> bool:
        """Check if text contains sensitive information."""
        return len(cls.scan(text)) > 0


class LogFilter(logging.Filter):
    """Logging filter to redact secrets."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log record to redact secrets."""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            record.msg = SecretsScanner.redact(record.msg)

        if hasattr(record, 'args') and record.args:
            redacted_args = tuple(
                SecretsScanner.redact(str(arg)) if isinstance(arg, str) else arg
                for arg in record.args
            )
            record.args = redacted_args

        return True


def setup_secrets_filtering():
    """Set up secrets filtering for all loggers."""
    root_logger = logging.getLogger()
    root_logger.addFilter(LogFilter())
    logger.info("Secrets filtering enabled for logging")


# Convenience functions
def redact_dict(data: dict, keys_to_redact: List[str] = None) -> dict:
    """
    Redact specific keys in a dictionary.

    Args:
        data: Dictionary to redact
        keys_to_redact: Keys to redact (case-insensitive)

    Returns:
        Redacted dictionary
    """
    if keys_to_redact is None:
        keys_to_redact = [
            "password", "passwd", "pwd", "secret", "token", "api_key",
            "apikey", "access_key", "private_key", "auth", "authorization"
        ]

    redacted = data.copy()

    for key in data:
        # Check if key matches any pattern to redact
        if any(pattern.lower() in key.lower() for pattern in keys_to_redact):
            redacted[key] = SecretsScanner.REDACTION_TEXT
        # Recursively redact nested dicts
        elif isinstance(data[key], dict):
            redacted[key] = redact_dict(data[key], keys_to_redact)
        # Redact strings that look like secrets
        elif isinstance(data[key], str):
            redacted[key] = SecretsScanner.redact(data[key])

    return redacted


def safe_log(message: str) -> str:
    """
    Make a message safe for logging by redacting secrets.

    Args:
        message: Message to log

    Returns:
        Redacted message
    """
    return SecretsScanner.redact(message)
