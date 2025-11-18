"""
Performance optimization module.

Provides caching, rate limiting, batch processing, and background tasks.
"""

from src.performance.cache import (
    CacheBackend,
    get_cache,
    cached,
    CacheManager,
    cache_analysis_result,
    get_cached_analysis,
    cache_metrics,
    get_cached_metrics,
)

from src.performance.rate_limit import (
    RateLimiter,
    RateLimitMiddleware,
    rate_limit,
)

from src.performance.batch import (
    BatchProcessor,
    BatchResult,
    DatabaseBatchWriter,
    batch_api_calls,
    parallel_map,
)

from src.performance.tasks import (
    celery_app,
    run_system_analysis,
    cleanup_old_data,
    send_notification,
    generate_and_apply_fix,
    export_historical_data,
    get_task_status,
    cancel_task,
    get_active_tasks,
)

__all__ = [
    # Cache
    "CacheBackend",
    "get_cache",
    "cached",
    "CacheManager",
    "cache_analysis_result",
    "get_cached_analysis",
    "cache_metrics",
    "get_cached_metrics",
    # Rate limiting
    "RateLimiter",
    "RateLimitMiddleware",
    "rate_limit",
    # Batch processing
    "BatchProcessor",
    "BatchResult",
    "DatabaseBatchWriter",
    "batch_api_calls",
    "parallel_map",
    # Background tasks
    "celery_app",
    "run_system_analysis",
    "cleanup_old_data",
    "send_notification",
    "generate_and_apply_fix",
    "export_historical_data",
    "get_task_status",
    "cancel_task",
    "get_active_tasks",
]
