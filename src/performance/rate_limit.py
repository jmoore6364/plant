"""
API rate limiting middleware.

Implements sliding window rate limiting using Redis.
"""

import time
import logging
from typing import Optional, Callable
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

from src.performance.cache import get_cache

logger = logging.getLogger(__name__)


class RateLimiter:
    """Sliding window rate limiter using Redis."""

    def __init__(
        self,
        requests: int = 100,
        window_seconds: int = 60,
        key_prefix: str = "rate_limit"
    ):
        self.requests = requests
        self.window_seconds = window_seconds
        self.key_prefix = key_prefix
        self.cache = get_cache()

    async def is_allowed(self, identifier: str) -> tuple[bool, dict]:
        """
        Check if request is allowed.

        Returns:
            (allowed, info_dict) where info_dict contains limit info
        """
        cache_key = f"{self.key_prefix}:{identifier}"
        current_time = int(time.time())
        window_start = current_time - self.window_seconds

        await self.cache.connect()

        if not self.cache.client:
            # If Redis is down, allow the request
            return True, {}

        try:
            # Use a sorted set with scores as timestamps
            pipe = self.cache.client.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(cache_key, 0, window_start)

            # Count current entries
            pipe.zcard(cache_key)

            # Add current request
            pipe.zadd(cache_key, {f"{current_time}:{id(self)}": current_time})

            # Set expiry
            pipe.expire(cache_key, self.window_seconds + 10)

            results = await pipe.execute()
            current_count = results[1]

            # Check if limit exceeded
            allowed = current_count < self.requests

            info = {
                "limit": self.requests,
                "remaining": max(0, self.requests - current_count - 1),
                "reset": current_time + self.window_seconds,
                "retry_after": self.window_seconds if not allowed else None
            }

            return allowed, info

        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # On error, allow the request
            return True, {}

    async def reset(self, identifier: str):
        """Reset rate limit for identifier."""
        cache_key = f"{self.key_prefix}:{identifier}"
        await self.cache.delete(cache_key)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting."""

    def __init__(
        self,
        app,
        requests: int = 100,
        window_seconds: int = 60,
        identifier_func: Optional[Callable] = None
    ):
        super().__init__(app)
        self.rate_limiter = RateLimiter(requests, window_seconds)
        self.identifier_func = identifier_func or self._default_identifier

    def _default_identifier(self, request: Request) -> str:
        """Default identifier: use client IP."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)

        # Get identifier
        identifier = self.identifier_func(request)

        # Check rate limit
        allowed, info = await self.rate_limiter.is_allowed(identifier)

        if not allowed:
            # Rate limit exceeded
            logger.warning(f"Rate limit exceeded for {identifier}")
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={
                    "X-RateLimit-Limit": str(info["limit"]),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(info["reset"]),
                    "Retry-After": str(info["retry_after"])
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset"])

        return response


def rate_limit(requests: int = 100, window_seconds: int = 60):
    """
    Decorator for rate limiting specific endpoints.

    Usage:
        @app.get("/api/data")
        @rate_limit(requests=10, window_seconds=60)
        async def get_data():
            ...
    """
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract request from args
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # No request found, skip rate limiting
                return await func(*args, **kwargs)

            # Create rate limiter
            limiter = RateLimiter(requests, window_seconds)
            identifier = request.client.host if request.client else "unknown"

            # Check rate limit
            allowed, info = await limiter.is_allowed(identifier)

            if not allowed:
                raise HTTPException(
                    status_code=HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                    headers={
                        "Retry-After": str(info["retry_after"])
                    }
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator
