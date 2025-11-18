"""
Security middleware for FastAPI.

Implements security headers, CORS, and request/response security.
"""

import logging
from typing import Callable
from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from src.config import get_config

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Security headers
        security_headers = {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",

            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",

            # XSS protection (legacy, but still useful)
            "X-XSS-Protection": "1; mode=block",

            # Strict Transport Security (HTTPS only)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",

            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",

            # Permissions policy
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",

            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self';"
            ),
        }

        for header, value in security_headers.items():
            response.headers[header] = value

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all API requests for security monitoring."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        response = await call_next(request)

        # Log response
        logger.info(
            f"Response: {request.method} {request.url.path} "
            f"status={response.status_code}"
        )

        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """Whitelist IP addresses for access."""

    def __init__(self, app, allowed_ips: list = None):
        super().__init__(app)
        self.allowed_ips = set(allowed_ips or [])

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.allowed_ips:
            # No whitelist configured, allow all
            return await call_next(request)

        client_ip = request.client.host if request.client else None

        # Check if IP is whitelisted
        if client_ip not in self.allowed_ips:
            logger.warning(f"Access denied for IP: {client_ip}")
            return StarletteResponse(
                content="Access denied",
                status_code=403
            )

        return await call_next(request)


def setup_cors(app, config=None):
    """
    Set up CORS middleware.

    Args:
        app: FastAPI application
        config: Application configuration
    """
    if config is None:
        config = get_config()

    if not config.security.cors_enabled:
        logger.info("CORS disabled")
        return

    origins = config.api.cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-RateLimit-*"],
    )

    logger.info(f"CORS enabled for origins: {origins}")


def setup_security_middleware(app):
    """
    Set up all security middleware.

    Args:
        app: FastAPI application
    """
    # Add security headers
    app.add_middleware(SecurityHeadersMiddleware)
    logger.info("Security headers middleware enabled")

    # Add request logging
    app.add_middleware(RequestLoggingMiddleware)
    logger.info("Request logging middleware enabled")

    # Set up CORS
    setup_cors(app)

    logger.info("Security middleware setup complete")
