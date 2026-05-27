"""Profiling and telemetry hooks for measuring LLM and chain latency."""

import time
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from functools import wraps


@dataclass
class TimingRecord:
    """A single timing measurement."""

    name: str
    duration_ms: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"TimingRecord({self.name}, {self.duration_ms:.1f}ms)"


class Profiler:
    """Collects timing data for LLM calls, chain executions, and tool runs.

    Usage:
        from cortexchain.profiling import profiler

        # Automatic profiling via decorator
        @profiler.track("llm_call")
        def call_llm(prompt):
            return llm(prompt)

        # Context manager
        with profiler.measure("chain_execution"):
            result = chain.invoke(inputs)

        # View results
        print(profiler.summary())
        print(profiler.get_stats("llm_call"))
    """

    def __init__(self, enabled: bool = True, max_records: int = 10000):
        self._enabled = enabled
        self._max_records = max_records
        self._records: List[TimingRecord] = []
        self._lock = threading.Lock()

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value

    def track(self, name: str, **metadata):
        """Decorator to time a function."""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                if not self._enabled:
                    return func(*args, **kwargs)
                start = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    elapsed = (time.perf_counter() - start) * 1000
                    self._record(name, elapsed, metadata)

            return wrapper

        return decorator

    @contextmanager
    def measure(self, name: str, **metadata):
        """Context manager to time a block."""
        if not self._enabled:
            yield
            return

        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            self._record(name, elapsed, metadata)

    def _record(self, name: str, duration_ms: float, metadata: Dict = None):
        record = TimingRecord(
            name=name,
            duration_ms=duration_ms,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        with self._lock:
            self._records.append(record)
            if len(self._records) > self._max_records:
                self._records = self._records[-self._max_records :]

    def get_records(self, name: str = None) -> List[TimingRecord]:
        """Get timing records, optionally filtered by name."""
        with self._lock:
            if name:
                return [r for r in self._records if r.name == name]
            return list(self._records)

    def get_stats(self, name: str) -> Dict[str, Any]:
        """Get statistics for a named measurement."""
        records = self.get_records(name)
        if not records:
            return {"name": name, "count": 0}

        durations = [r.duration_ms for r in records]
        durations.sort()
        count = len(durations)

        return {
            "name": name,
            "count": count,
            "mean_ms": sum(durations) / count,
            "min_ms": durations[0],
            "max_ms": durations[-1],
            "median_ms": durations[count // 2],
            "p95_ms": durations[int(count * 0.95)] if count >= 20 else durations[-1],
            "p99_ms": durations[int(count * 0.99)] if count >= 100 else durations[-1],
            "total_ms": sum(durations),
        }

    def summary(self) -> str:
        """Human-readable summary of all profiled operations."""
        with self._lock:
            names = sorted(set(r.name for r in self._records))

        if not names:
            return "No profiling data collected."

        lines = ["=" * 60, "CortexChain Profiling Summary", "=" * 60]
        for name in names:
            stats = self.get_stats(name)
            lines.append(
                f"  {name:30s}  count={stats['count']:4d}  "
                f"mean={stats['mean_ms']:8.1f}ms  "
                f"min={stats['min_ms']:8.1f}ms  "
                f"max={stats['max_ms']:8.1f}ms"
            )
        lines.append("=" * 60)
        return "\n".join(lines)

    def reset(self):
        """Clear all profiling data."""
        with self._lock:
            self._records.clear()

    @property
    def record_count(self) -> int:
        with self._lock:
            return len(self._records)


# Global profiler instance
profiler = Profiler(enabled=False)


def enable_profiling():
    """Enable the global profiler."""
    profiler.enabled = True


def disable_profiling():
    """Disable the global profiler."""
    profiler.enabled = False


class LatencyTracker:
    """Tracks latency for specific operations over time windows.

    Useful for monitoring SLOs (Service Level Objectives).

    Usage:
        tracker = LatencyTracker(slo_ms=2000)
        tracker.record("llm_invoke", 1500)
        tracker.record("llm_invoke", 2500)
        print(tracker.slo_compliance("llm_invoke"))  # 0.5 (50% within SLO)
    """

    def __init__(self, slo_ms: float = 5000, window_size: int = 100):
        self._slo_ms = slo_ms
        self._window_size = window_size
        self._data: Dict[str, List[float]] = {}
        self._lock = threading.Lock()

    def record(self, operation: str, latency_ms: float):
        with self._lock:
            if operation not in self._data:
                self._data[operation] = []
            self._data[operation].append(latency_ms)
            if len(self._data[operation]) > self._window_size:
                self._data[operation] = self._data[operation][-self._window_size :]

    def slo_compliance(self, operation: str) -> float:
        """Return fraction of requests within SLO (0.0 to 1.0)."""
        with self._lock:
            records = self._data.get(operation, [])
        if not records:
            return 1.0
        within = sum(1 for r in records if r <= self._slo_ms)
        return within / len(records)

    def report(self) -> Dict[str, Dict[str, Any]]:
        """Get a report for all tracked operations."""
        with self._lock:
            operations = list(self._data.keys())

        result = {}
        for op in operations:
            with self._lock:
                records = list(self._data.get(op, []))
            if records:
                result[op] = {
                    "count": len(records),
                    "mean_ms": sum(records) / len(records),
                    "slo_compliance": self.slo_compliance(op),
                    "slo_target_ms": self._slo_ms,
                }
        return result
