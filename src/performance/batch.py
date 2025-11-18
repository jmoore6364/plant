"""
Async batch processing system.

Efficiently processes large batches of operations with concurrency control.
"""

import asyncio
import logging
from typing import List, Callable, Any, Optional, TypeVar, Generic
from dataclasses import dataclass
from datetime import datetime
import time

logger = logging.getLogger(__name__)

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class BatchResult(Generic[T, R]):
    """Result of batch processing."""
    successful: List[tuple[T, R]]
    failed: List[tuple[T, Exception]]
    total_items: int
    successful_count: int
    failed_count: int
    duration_seconds: float
    throughput: float


class BatchProcessor(Generic[T, R]):
    """Process items in batches with concurrency control."""

    def __init__(
        self,
        batch_size: int = 100,
        max_concurrency: int = 10,
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ):
        self.batch_size = batch_size
        self.max_concurrency = max_concurrency
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

    async def process(
        self,
        items: List[T],
        processor: Callable[[T], Any],
        on_success: Optional[Callable[[T, R], None]] = None,
        on_error: Optional[Callable[[T, Exception], None]] = None
    ) -> BatchResult[T, R]:
        """
        Process items in batches.

        Args:
            items: List of items to process
            processor: Async function to process each item
            on_success: Optional callback for successful items
            on_error: Optional callback for failed items

        Returns:
            BatchResult with processing statistics
        """
        start_time = time.time()

        successful = []
        failed = []

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def process_item(item: T) -> tuple[bool, T, Any]:
            """Process a single item with retry logic."""
            async with semaphore:
                for attempt in range(self.retry_attempts):
                    try:
                        result = await processor(item)

                        if on_success:
                            await on_success(item, result)

                        return True, item, result

                    except Exception as e:
                        if attempt == self.retry_attempts - 1:
                            # Final attempt failed
                            logger.error(f"Failed to process item after {self.retry_attempts} attempts: {e}")

                            if on_error:
                                await on_error(item, e)

                            return False, item, e
                        else:
                            # Retry with delay
                            await asyncio.sleep(self.retry_delay * (attempt + 1))

        # Process items in batches
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]

            logger.info(f"Processing batch {i // self.batch_size + 1} ({len(batch)} items)")

            # Process batch concurrently
            results = await asyncio.gather(
                *[process_item(item) for item in batch],
                return_exceptions=False
            )

            # Categorize results
            for success, item, result in results:
                if success:
                    successful.append((item, result))
                else:
                    failed.append((item, result))

        # Calculate statistics
        duration = time.time() - start_time
        total_items = len(items)
        successful_count = len(successful)
        failed_count = len(failed)
        throughput = total_items / duration if duration > 0 else 0

        logger.info(
            f"Batch processing complete: {successful_count} successful, "
            f"{failed_count} failed, {duration:.2f}s, {throughput:.2f} items/s"
        )

        return BatchResult(
            successful=successful,
            failed=failed,
            total_items=total_items,
            successful_count=successful_count,
            failed_count=failed_count,
            duration_seconds=duration,
            throughput=throughput
        )

    async def process_stream(
        self,
        items_generator: Any,
        processor: Callable[[T], Any],
        flush_interval: float = 5.0
    ):
        """
        Process items from an async generator/stream.

        Args:
            items_generator: Async generator yielding items
            processor: Async function to process each item
            flush_interval: Flush batch after this many seconds
        """
        batch = []
        last_flush = time.time()
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def process_item(item: T):
            async with semaphore:
                try:
                    return await processor(item)
                except Exception as e:
                    logger.error(f"Error processing item: {e}")
                    raise

        async def flush_batch():
            """Process current batch."""
            if not batch:
                return

            logger.info(f"Flushing batch of {len(batch)} items")
            await asyncio.gather(
                *[process_item(item) for item in batch],
                return_exceptions=True
            )
            batch.clear()

        # Process items from generator
        async for item in items_generator:
            batch.append(item)

            # Flush if batch is full or time interval elapsed
            if len(batch) >= self.batch_size or (time.time() - last_flush) >= flush_interval:
                await flush_batch()
                last_flush = time.time()

        # Flush remaining items
        await flush_batch()


class DatabaseBatchWriter:
    """Batch database writes for better performance."""

    def __init__(self, session, batch_size: int = 100):
        self.session = session
        self.batch_size = batch_size
        self.batch = []
        self.total_written = 0

    async def add(self, obj):
        """Add object to batch."""
        self.batch.append(obj)

        if len(self.batch) >= self.batch_size:
            await self.flush()

    async def flush(self):
        """Write batch to database."""
        if not self.batch:
            return

        try:
            self.session.add_all(self.batch)
            await self.session.commit()

            self.total_written += len(self.batch)
            logger.info(f"Batch write: {len(self.batch)} objects (total: {self.total_written})")

            self.batch.clear()

        except Exception as e:
            logger.error(f"Batch write failed: {e}")
            await self.session.rollback()
            raise

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.flush()


# Utility functions
async def batch_api_calls(
    urls: List[str],
    fetch_func: Callable[[str], Any],
    max_concurrency: int = 10
) -> List[Any]:
    """
    Make multiple API calls in parallel with concurrency control.

    Args:
        urls: List of URLs to fetch
        fetch_func: Async function to fetch each URL
        max_concurrency: Maximum concurrent requests

    Returns:
        List of responses
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def fetch_with_semaphore(url: str):
        async with semaphore:
            return await fetch_func(url)

    return await asyncio.gather(
        *[fetch_with_semaphore(url) for url in urls],
        return_exceptions=True
    )


async def chunk_iterable(iterable, chunk_size: int):
    """
    Yield chunks from an iterable.

    Args:
        iterable: Any iterable
        chunk_size: Size of each chunk

    Yields:
        Chunks of items
    """
    chunk = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []

    if chunk:
        yield chunk


async def parallel_map(
    func: Callable[[T], R],
    items: List[T],
    max_workers: int = 10
) -> List[R]:
    """
    Map function over items in parallel.

    Args:
        func: Async function to apply
        items: Items to process
        max_workers: Maximum parallel workers

    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(max_workers)

    async def process(item):
        async with semaphore:
            return await func(item)

    return await asyncio.gather(*[process(item) for item in items])
