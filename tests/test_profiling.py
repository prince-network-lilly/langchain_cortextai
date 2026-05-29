"""Tests for cortexchain.profiling"""
import time
from cortexchain.profiling import Profiler, LatencyTracker, enable_profiling, disable_profiling


class TestProfiler:
    def test_track_decorator(self):
        p = Profiler(enabled=True)

        @p.track("test_op")
        def slow_fn():
            time.sleep(0.01)
            return 42

        result = slow_fn()
        assert result == 42
        assert p.record_count == 1
        stats = p.get_stats("test_op")
        assert stats["count"] == 1
        assert stats["mean_ms"] >= 5

    def test_measure_context_manager(self):
        p = Profiler(enabled=True)

        with p.measure("block"):
            time.sleep(0.01)

        stats = p.get_stats("block")
        assert stats["count"] == 1
        assert stats["mean_ms"] >= 5

    def test_disabled_no_records(self):
        p = Profiler(enabled=False)

        @p.track("noop")
        def fast_fn():
            return "ok"

        fast_fn()
        assert p.record_count == 0

    def test_multiple_records_stats(self):
        p = Profiler(enabled=True)

        for _ in range(10):
            with p.measure("repeated"):
                time.sleep(0.001)

        stats = p.get_stats("repeated")
        assert stats["count"] == 10
        assert stats["min_ms"] <= stats["mean_ms"] <= stats["max_ms"]

    def test_summary(self):
        p = Profiler(enabled=True)
        with p.measure("op_a"):
            pass
        with p.measure("op_b"):
            pass

        summary = p.summary()
        assert "op_a" in summary
        assert "op_b" in summary

    def test_reset(self):
        p = Profiler(enabled=True)
        with p.measure("x"):
            pass
        assert p.record_count == 1
        p.reset()
        assert p.record_count == 0

    def test_max_records_cap(self):
        p = Profiler(enabled=True, max_records=5)
        for _ in range(20):
            with p.measure("flood"):
                pass
        assert p.record_count == 5


class TestLatencyTracker:
    def test_record_and_compliance(self):
        tracker = LatencyTracker(slo_ms=100)
        tracker.record("api", 50)
        tracker.record("api", 80)
        tracker.record("api", 150)

        assert tracker.slo_compliance("api") == pytest.approx(2 / 3)

    def test_all_within_slo(self):
        tracker = LatencyTracker(slo_ms=1000)
        for _ in range(10):
            tracker.record("fast", 100)
        assert tracker.slo_compliance("fast") == 1.0

    def test_empty_operation(self):
        tracker = LatencyTracker(slo_ms=100)
        assert tracker.slo_compliance("unknown") == 1.0

    def test_report(self):
        tracker = LatencyTracker(slo_ms=200)
        tracker.record("op1", 100)
        tracker.record("op1", 300)
        tracker.record("op2", 50)

        report = tracker.report()
        assert "op1" in report
        assert "op2" in report
        assert report["op1"]["count"] == 2
        assert report["op2"]["slo_compliance"] == 1.0

    def test_window_size(self):
        tracker = LatencyTracker(slo_ms=100, window_size=5)
        for i in range(20):
            tracker.record("limited", 50)
        report = tracker.report()
        assert report["limited"]["count"] == 5


import pytest
