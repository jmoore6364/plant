"""
Input validation and sanitization.

Protects against injection attacks and malicious input.
"""

import re
import html
import logging
from typing import Any, Optional
from fastapi import HTTPException
import bleach

logger = logging.getLogger(__name__)


class InputValidator:
    """Validate and sanitize user input."""

    # Regex patterns for common attacks
    SQL_INJECTION_PATTERN = re.compile(
        r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|--;|/\*|\*/|xp_|sp_)",
        re.IGNORECASE
    )

    XSS_PATTERN = re.compile(
        r"(<script|javascript:|onerror=|onload=|<iframe|<object|<embed)",
        re.IGNORECASE
    )

    COMMAND_INJECTION_PATTERN = re.compile(
        r"(;|\||&|`|\$\(|\${|<\(|>\()",
        re.IGNORECASE
    )

    PATH_TRAVERSAL_PATTERN = re.compile(
        r"(\.\.\/|\.\.\\|%2e%2e%2f|%2e%2e\\)",
        re.IGNORECASE
    )

    @staticmethod
    def sanitize_html(text: str, allowed_tags: list = None) -> str:
        """
        Sanitize HTML to prevent XSS.

        Args:
            text: Input HTML
            allowed_tags: List of allowed HTML tags

        Returns:
            Sanitized HTML
        """
        if allowed_tags is None:
            allowed_tags = []

        return bleach.clean(
            text,
            tags=allowed_tags,
            strip=True
        )

    @staticmethod
    def escape_html(text: str) -> str:
        """Escape HTML entities."""
        return html.escape(text)

    @staticmethod
    def validate_sql_safe(text: str) -> bool:
        """Check if text is safe from SQL injection."""
        return not InputValidator.SQL_INJECTION_PATTERN.search(text)

    @staticmethod
    def validate_xss_safe(text: str) -> bool:
        """Check if text is safe from XSS."""
        return not InputValidator.XSS_PATTERN.search(text)

    @staticmethod
    def validate_command_safe(text: str) -> bool:
        """Check if text is safe from command injection."""
        return not InputValidator.COMMAND_INJECTION_PATTERN.search(text)

    @staticmethod
    def validate_path_safe(path: str) -> bool:
        """Check if path is safe from traversal attacks."""
        return not InputValidator.PATH_TRAVERSAL_PATTERN.search(path)

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username (alphanumeric, underscore, hyphen)."""
        pattern = r'^[a-zA-Z0-9_-]{3,32}$'
        return re.match(pattern, username) is not None

    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        return re.match(pattern, url) is not None

    @staticmethod
    def sanitize_string(
        text: str,
        max_length: Optional[int] = None,
        allow_html: bool = False
    ) -> str:
        """
        Sanitize a string input.

        Args:
            text: Input text
            max_length: Maximum length
            allow_html: Whether to allow HTML (will be sanitized)

        Returns:
            Sanitized string
        """
        if not isinstance(text, str):
            text = str(text)

        # Trim whitespace
        text = text.strip()

        # Limit length
        if max_length and len(text) > max_length:
            text = text[:max_length]

        # Handle HTML
        if allow_html:
            text = InputValidator.sanitize_html(text, allowed_tags=['b', 'i', 'u', 'a', 'p'])
        else:
            text = InputValidator.escape_html(text)

        return text

    @staticmethod
    def validate_and_sanitize(
        text: str,
        check_sql: bool = True,
        check_xss: bool = True,
        check_command: bool = True,
        check_path: bool = False,
        max_length: Optional[int] = None
    ) -> str:
        """
        Validate and sanitize input.

        Args:
            text: Input text
            check_sql: Check for SQL injection
            check_xss: Check for XSS
            check_command: Check for command injection
            check_path: Check for path traversal
            max_length: Maximum length

        Returns:
            Sanitized text

        Raises:
            HTTPException if validation fails
        """
        if check_sql and not InputValidator.validate_sql_safe(text):
            logger.warning(f"SQL injection attempt detected: {text[:50]}")
            raise HTTPException(status_code=400, detail="Invalid input: potential SQL injection")

        if check_xss and not InputValidator.validate_xss_safe(text):
            logger.warning(f"XSS attempt detected: {text[:50]}")
            raise HTTPException(status_code=400, detail="Invalid input: potential XSS")

        if check_command and not InputValidator.validate_command_safe(text):
            logger.warning(f"Command injection attempt detected: {text[:50]}")
            raise HTTPException(status_code=400, detail="Invalid input: potential command injection")

        if check_path and not InputValidator.validate_path_safe(text):
            logger.warning(f"Path traversal attempt detected: {text[:50]}")
            raise HTTPException(status_code=400, detail="Invalid input: potential path traversal")

        return InputValidator.sanitize_string(text, max_length=max_length)


# Convenience functions
def sanitize(text: str, **kwargs) -> str:
    """Sanitize input text."""
    return InputValidator.validate_and_sanitize(text, **kwargs)


def validate_email(email: str) -> str:
    """Validate and return email."""
    if not InputValidator.validate_email(email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    return email.lower()


def validate_username(username: str) -> str:
    """Validate and return username."""
    if not InputValidator.validate_username(username):
        raise HTTPException(
            status_code=400,
            detail="Invalid username. Must be 3-32 characters, alphanumeric with underscore/hyphen"
        )
    return username


def validate_url(url: str) -> str:
    """Validate and return URL."""
    if not InputValidator.validate_url(url):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    return url
