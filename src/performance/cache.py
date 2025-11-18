"""
Redis caching layer for performance optimization.

Provides decorators and utilities for caching expensive operations.
"""

import redis.asyncio as redis
import json
import hashlib
import logging
from typing import Any, Optional, Callable, Union
from datetime import timedelta
from functools import wraps
import pickle

from src.config import get_config

logger = logging.getLogger(__name__)


class CacheBackend:
    """Redis cache backend with async support."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 300,
        max_connections: int = 10
    ):
        config = get_config()
        self.redis_url = redis_url or config.cache.redis_url
        self.default_ttl = default_ttl or config.cache.ttl_seconds
        self.max_connections = max_connections or config.cache.max_connections

        self.client: Optional[redis.Redis] = None
        self._connection_pool: Optional[redis.ConnectionPool] = None

    async def connect(self):
        """Connect to Redis."""
        if self.client is None:
            try:
                self._connection_pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    max_connections=self.max_connections,
                    decode_responses=False  # Handle binary data
                )
                self.client = redis.Redis(connection_pool=self._connection_pool)
                await self.client.ping()
                logger.info(f"Connected to Redis: {self.redis_url}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.client = None

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.client:
            await self.client.close()
            if self._connection_pool:
                await self._connection_pool.disconnect()
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.client:
            await self.connect()

        if not self.client:
            return None

        try:
            value = await self.client.get(key)
            if value:
                # Try to unpickle, fall back to JSON
                try:
                    return pickle.loads(value)
                except:
                    return json.loads(value.decode('utf-8'))
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        if not self.client:
            await self.connect()

        if not self.client:
            return False

        try:
            ttl = ttl or self.default_ttl

            # Try to pickle, fall back to JSON
            try:
                serialized = pickle.dumps(value)
            except:
                serialized = json.dumps(value).encode('utf-8')

            await self.client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.client:
            await self.connect()

        if not self.client:
            return False

        try:
            await self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    async def clear(self, pattern: str = "*") -> int:
        """Clear cache keys matching pattern."""
        if not self.client:
            await self.connect()

        if not self.client:
            return 0

        try:
            keys = []
            async for key in self.client.scan_iter(pattern):
                keys.append(key)

            if keys:
                return await self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.client:
            await self.connect()

        if not self.client:
            return False

        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking cache existence: {e}")
            return False

    async def get_ttl(self, key: str) -> int:
        """Get TTL for a key."""
        if not self.client:
            await self.connect()

        if not self.client:
            return -1

        try:
            return await self.client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL: {e}")
            return -1

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a counter."""
        if not self.client:
            await self.connect()

        if not self.client:
            return 0

        try:
            return await self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing: {e}")
            return 0


# Global cache instance
_cache: Optional[CacheBackend] = None


def get_cache() -> CacheBackend:
    """Get global cache instance."""
    global _cache
    if _cache is None:
        _cache = CacheBackend()
    return _cache


def generate_cache_key(*args, prefix: str = "", **kwargs) -> str:
    """Generate cache key from arguments."""
    # Create key from args and kwargs
    key_parts = [prefix] if prefix else []

    # Add positional args
    for arg in args:
        if isinstance(arg, (str, int, float, bool)):
            key_parts.append(str(arg))
        else:
            # Hash complex objects
            key_parts.append(hashlib.md5(str(arg).encode()).hexdigest()[:8])

    # Add keyword args
    for k, v in sorted(kwargs.items()):
        if isinstance(v, (str, int, float, bool)):
            key_parts.append(f"{k}={v}")
        else:
            key_parts.append(f"{k}={hashlib.md5(str(v).encode()).hexdigest()[:8]}")

    return ":".join(key_parts)


def cached(
    ttl: Optional[int] = None,
    key_prefix: str = "",
    key_builder: Optional[Callable] = None
):
    """
    Cache decorator for async functions.

    Args:
        ttl: Time to live in seconds
        key_prefix: Prefix for cache key
        key_builder: Custom function to build cache key
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache()

            # Build cache key
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # Use function name as prefix if not provided
                prefix = key_prefix or f"{func.__module__}.{func.__name__}"
                cache_key = generate_cache_key(*args, prefix=prefix, **kwargs)

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value

            # Execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(cache_key, result, ttl=ttl)

            return result

        # Add cache control methods
        async def invalidate(*args, **kwargs):
            """Invalidate cache for specific arguments."""
            cache = get_cache()
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                prefix = key_prefix or f"{func.__module__}.{func.__name__}"
                cache_key = generate_cache_key(*args, prefix=prefix, **kwargs)
            await cache.delete(cache_key)

        async def clear_all():
            """Clear all cache entries for this function."""
            cache = get_cache()
            prefix = key_prefix or f"{func.__module__}.{func.__name__}"
            await cache.clear(f"{prefix}:*")

        wrapper.invalidate = invalidate
        wrapper.clear_all = clear_all

        return wrapper

    return decorator


class CacheManager:
    """Manage cache operations with statistics."""

    def __init__(self):
        self.cache = get_cache()
        self.hits = 0
        self.misses = 0
        self.errors = 0

    async def get_stats(self) -> dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        stats = {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "total_requests": total,
            "hit_rate": f"{hit_rate:.2f}%"
        }

        # Get Redis info if available
        if self.cache.client:
            try:
                info = await self.cache.client.info("stats")
                stats["redis"] = {
                    "total_commands_processed": info.get("total_commands_processed"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses"),
                }
            except Exception as e:
                logger.error(f"Error getting Redis stats: {e}")

        return stats

    async def clear_all(self):
        """Clear entire cache."""
        return await self.cache.clear()

    async def get_keys(self, pattern: str = "*") -> list:
        """Get all keys matching pattern."""
        if not self.cache.client:
            await self.cache.connect()

        if not self.cache.client:
            return []

        keys = []
        try:
            async for key in self.cache.client.scan_iter(pattern):
                keys.append(key.decode('utf-8') if isinstance(key, bytes) else key)
        except Exception as e:
            logger.error(f"Error getting keys: {e}")

        return keys


# Convenience functions for common caching patterns
async def cache_analysis_result(run_id: str, result: dict, ttl: int = 3600):
    """Cache analysis result."""
    cache = get_cache()
    key = f"analysis:{run_id}"
    await cache.set(key, result, ttl=ttl)


async def get_cached_analysis(run_id: str) -> Optional[dict]:
    """Get cached analysis result."""
    cache = get_cache()
    key = f"analysis:{run_id}"
    return await cache.get(key)


async def cache_metrics(metrics: dict, ttl: int = 60):
    """Cache current metrics."""
    cache = get_cache()
    key = "metrics:current"
    await cache.set(key, metrics, ttl=ttl)


async def get_cached_metrics() -> Optional[dict]:
    """Get cached metrics."""
    cache = get_cache()
    key = "metrics:current"
    return await cache.get(key)
