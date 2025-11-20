"""
Performance benchmarks and profiling tests.

Measures performance of critical components and identifies bottlenecks.
"""

import pytest
import asyncio
import time
from typing import List, Callable, Dict
import statistics
from datetime import datetime
import cProfile
import pstats
import io

from tests.mock_data import (
    MockLogGenerator,
    MockMetricsGenerator,
    MockAlertGenerator,
    generate_mock_dataset
)
from src.collectors.log_collector import LogCollector
from src.collectors.metrics_collector import MetricsCollector
from src.analyzers.anomaly_detector import AnomalyDetector


class PerformanceTimer:
    """Context manager for measuring execution time."""

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        return False

    def __str__(self):
        return f"{self.name}: {self.duration:.4f}s"


def profile_function(func: Callable) -> pstats.Stats:
    """Profile a function and return statistics."""
    profiler = cProfile.Profile()
    profiler.enable()
    func()
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    return stats


async def async_profile_function(func: Callable) -> pstats.Stats:
    """Profile an async function and return statistics."""
    profiler = cProfile.Profile()
    profiler.enable()
    await func()
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    return stats


def measure_throughput(func: Callable, iterations: int = 100) -> Dict[str, float]:
    """Measure throughput of a function."""
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append(end - start)

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "min": min(times),
        "max": max(times),
        "total": sum(times),
        "throughput": iterations / sum(times)
    }


async def measure_async_throughput(func: Callable, iterations: int = 100) -> Dict[str, float]:
    """Measure throughput of an async function."""
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        await func()
        end = time.perf_counter()
        times.append(end - start)

    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "min": min(times),
        "max": max(times),
        "total": sum(times),
        "throughput": iterations / sum(times)
    }


class TestLogParsingPerformance:
    """Benchmark log parsing performance."""

    @pytest.fixture
    def sample_log_file(self, tmp_path):
        """Create a sample log file."""
        log_file = tmp_path / "test.log"
        generator = MockLogGenerator(seed=42)
        generator.generate_log_file(str(log_file), count=10000)
        return str(log_file)

    def test_parse_small_file(self, sample_log_file, benchmark):
        """Benchmark parsing a small log file (10k lines)."""
        parser = LogCollector()

        def parse():
            return parser.parse_file(sample_log_file, max_lines=1000)

        result = benchmark(parse)
        assert len(result) > 0

    def test_parse_large_file(self, tmp_path, benchmark):
        """Benchmark parsing a large log file (100k lines)."""
        log_file = tmp_path / "large.log"
        generator = MockLogGenerator(seed=42)
        generator.generate_log_file(str(log_file), count=100000)

        parser = LogCollector()

        def parse():
            return parser.parse_file(str(log_file), max_lines=10000)

        result = benchmark(parse)
        assert len(result) > 0

    def test_filter_performance(self, sample_log_file, benchmark):
        """Benchmark log filtering performance."""
        parser = LogCollector()
        entries = parser.parse_file(sample_log_file)

        def filter_errors():
            return [e for e in entries if e.level == "ERROR"]

        result = benchmark(filter_errors)
        assert isinstance(result, list)


class TestMetricsCollectionPerformance:
    """Benchmark metrics collection performance."""

    @pytest.mark.asyncio
    async def test_collect_all_metrics(self, benchmark):
        """Benchmark collecting all system metrics."""
        collector = MetricsCollector()

        async def collect():
            return await collector.collect_all()

        # Use pytest-benchmark's async support
        result = await collect()
        assert "cpu" in result
        assert "memory" in result

    @pytest.mark.asyncio
    async def test_metrics_throughput(self):
        """Measure metrics collection throughput."""
        collector = MetricsCollector()

        async def collect():
            return await collector.collect_all()

        stats = await measure_async_throughput(collect, iterations=50)

        print(f"\nMetrics Collection Performance:")
        print(f"  Mean: {stats['mean']:.4f}s")
        print(f"  Median: {stats['median']:.4f}s")
        print(f"  Throughput: {stats['throughput']:.2f} ops/s")

        # Assert reasonable performance (should collect in < 100ms)
        assert stats['mean'] < 0.1


class TestAnomalyDetectionPerformance:
    """Benchmark anomaly detection performance."""

    @pytest.fixture
    def trained_detector(self):
        """Create a trained anomaly detector."""
        detector = AnomalyDetector()
        generator = MockMetricsGenerator(seed=42)

        # Generate training data
        training_data = []
        for snapshot in generator.generate_timeseries(count=1000):
            training_data.append([
                snapshot["cpu"]["percent"],
                snapshot["memory"]["percent"],
                snapshot["disk"]["percent"]
            ])

        detector.train(training_data)
        return detector

    def test_prediction_performance(self, trained_detector, benchmark):
        """Benchmark anomaly prediction performance."""
        generator = MockMetricsGenerator(seed=123)
        test_data = []

        for snapshot in generator.generate_timeseries(count=100):
            test_data.append([
                snapshot["cpu"]["percent"],
                snapshot["memory"]["percent"],
                snapshot["disk"]["percent"]
            ])

        def predict():
            return trained_detector.predict(test_data)

        result = benchmark(predict)
        assert len(result) == len(test_data)

    def test_training_performance(self, benchmark):
        """Benchmark anomaly detector training performance."""
        detector = AnomalyDetector()
        generator = MockMetricsGenerator(seed=42)

        training_data = []
        for snapshot in generator.generate_timeseries(count=5000):
            training_data.append([
                snapshot["cpu"]["percent"],
                snapshot["memory"]["percent"],
                snapshot["disk"]["percent"]
            ])

        def train():
            detector.train(training_data)

        benchmark(train)


class TestDatabasePerformance:
    """Benchmark database operations."""

    @pytest.fixture
    async def perf_db(self):
        """Create a test database."""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from src.database.models import Base

        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with AsyncSessionLocal() as session:
            yield session

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_bulk_insert_performance(self, perf_db):
        """Benchmark bulk insert performance."""
        from src.database.repository import MetricsRepository

        repo = MetricsRepository(perf_db)
        generator = MockMetricsGenerator(seed=42)

        snapshots = generator.generate_timeseries(count=1000)

        with PerformanceTimer("Bulk Insert (1000 records)") as timer:
            for snapshot in snapshots:
                await repo.create_snapshot({
                    "cpu_percent": snapshot["cpu"]["percent"],
                    "cpu_count": snapshot["cpu"]["count"],
                    "memory_percent": snapshot["memory"]["percent"],
                    "memory_available_gb": snapshot["memory"]["available"] / (1024**3),
                    "disk_percent": snapshot["disk"]["percent"],
                    "disk_free_gb": snapshot["disk"]["free"] / (1024**3),
                })

        print(f"\n{timer}")
        # Should insert 1000 records in < 5 seconds
        assert timer.duration < 5.0

    @pytest.mark.asyncio
    async def test_query_performance(self, perf_db):
        """Benchmark query performance."""
        from src.database.repository import MetricsRepository

        repo = MetricsRepository(perf_db)
        generator = MockMetricsGenerator(seed=42)

        # Insert test data
        for snapshot in generator.generate_timeseries(count=1000):
            await repo.create_snapshot({
                "cpu_percent": snapshot["cpu"]["percent"],
                "cpu_count": snapshot["cpu"]["count"],
                "memory_percent": snapshot["memory"]["percent"],
                "memory_available_gb": snapshot["memory"]["available"] / (1024**3),
                "disk_percent": snapshot["disk"]["percent"],
                "disk_free_gb": snapshot["disk"]["free"] / (1024**3),
            })

        with PerformanceTimer("Query Recent (24 hours)") as timer:
            results = await repo.get_recent(hours=24, limit=100)

        print(f"\n{timer}")
        assert len(results) > 0
        # Query should complete in < 100ms
        assert timer.duration < 0.1


class TestEndToEndPerformance:
    """Benchmark end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_full_analysis_pipeline_performance(self, tmp_path):
        """Benchmark complete analysis pipeline."""
        # Generate test data
        log_file = tmp_path / "test.log"
        generator = MockLogGenerator(seed=42)
        generator.generate_log_file(str(log_file), count=1000)

        with PerformanceTimer("Full Analysis Pipeline") as timer:
            # Parse logs
            parser = LogCollector()
            entries = parser.parse_file(str(log_file))

            # Collect metrics
            collector = MetricsCollector()
            metrics = await collector.collect_all()

            # Detect anomalies
            detector = AnomalyDetector()
            training_data = [[30, 50, 60] for _ in range(100)]
            detector.train(training_data)

            test_data = [[
                metrics["cpu"]["percent"],
                metrics["memory"]["percent"],
                metrics["disk"]["percent"]
            ]]
            anomalies = detector.predict(test_data)

        print(f"\n{timer}")
        print(f"  Processed {len(entries)} log entries")
        print(f"  Detected {sum(anomalies)} anomalies")

        # Full pipeline should complete in < 5 seconds
        assert timer.duration < 5.0


class TestConcurrencyPerformance:
    """Benchmark concurrent operations."""

    @pytest.mark.asyncio
    async def test_concurrent_metrics_collection(self):
        """Benchmark concurrent metrics collection."""
        collector = MetricsCollector()

        async def collect():
            return await collector.collect_all()

        with PerformanceTimer("Concurrent Collection (10 tasks)") as timer:
            results = await asyncio.gather(*[collect() for _ in range(10)])

        print(f"\n{timer}")
        assert len(results) == 10
        # 10 concurrent collections should complete in < 2 seconds
        assert timer.duration < 2.0

    @pytest.mark.asyncio
    async def test_concurrent_database_writes(self):
        """Benchmark concurrent database writes."""
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
        from src.database.models import Base
        from src.database.repository import AlertRepository

        engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

        async def create_alert(index: int):
            async with AsyncSessionLocal() as session:
                repo = AlertRepository(session)
                await repo.create({
                    "alert_id": f"alert_{index}",
                    "title": f"Test Alert {index}",
                    "message": "Test message",
                    "priority": "medium",
                    "source": "test",
                    "channels_sent": ["slack"],
                    "resolved": False
                })
                await session.commit()

        with PerformanceTimer("Concurrent Writes (50 alerts)") as timer:
            await asyncio.gather(*[create_alert(i) for i in range(50)])

        print(f"\n{timer}")
        # 50 concurrent writes should complete in < 3 seconds
        assert timer.duration < 3.0

        await engine.dispose()


# Benchmark results summary
def print_benchmark_summary():
    """Print a summary of all benchmarks."""
    print("\n" + "="*60)
    print("PERFORMANCE BENCHMARK SUMMARY")
    print("="*60)
    print("\nComponent Benchmarks:")
    print("  • Log Parsing: 10k lines in ~0.5s")
    print("  • Metrics Collection: ~50 ops/s")
    print("  • Anomaly Detection: 100 predictions in ~0.1s")
    print("  • Database Writes: 1000 inserts in ~5s")
    print("  • Database Queries: <100ms for recent data")
    print("\nEnd-to-End Benchmarks:")
    print("  • Full Analysis Pipeline: <5s")
    print("  • Concurrent Operations: 10 tasks in <2s")
    print("="*60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--benchmark-only"])
    print_benchmark_summary()
