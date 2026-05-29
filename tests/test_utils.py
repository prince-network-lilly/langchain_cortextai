"""Tests for cortexchain.utils (cache, rate_limiter, batch)"""
import os
import time
import tempfile
from cortexchain.utils.cache import LLMCache
from cortexchain.utils.rate_limiter import RateLimiter
from cortexchain.utils.batch import BatchProcessor, BatchResult


class TestLLMCache:
    def test_set_and_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMCache(cache_dir=tmpdir, ttl_seconds=60)
            cache.set("hello prompt", "hello response")
            result = cache.get("hello prompt")
            assert result == "hello response"

    def test_miss_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMCache(cache_dir=tmpdir, ttl_seconds=60)
            assert cache.get("nonexistent") is None

    def test_expired_returns_none(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMCache(cache_dir=tmpdir, ttl_seconds=0)
            cache.set("prompt", "response")
            time.sleep(0.01)
            assert cache.get("prompt") is None

    def test_clear(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMCache(cache_dir=tmpdir)
            cache.set("a", "b")
            cache.clear()
            assert cache.get("a") is None

    def test_stats(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LLMCache(cache_dir=tmpdir)
            cache.set("x", "y")
            stats = cache.stats()
            assert stats["disk_entries"] == 1


class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = RateLimiter(max_calls=5, period=1.0)
        for _ in range(5):
            limiter.acquire()
        assert limiter.remaining == 0

    def test_decorator(self):
        limiter = RateLimiter(max_calls=10, period=1.0)
        call_count = 0

        @limiter
        def my_func():
            nonlocal call_count
            call_count += 1

        for _ in range(5):
            my_func()
        assert call_count == 5

    def test_reset(self):
        limiter = RateLimiter(max_calls=2, period=60.0)
        limiter.acquire()
        limiter.acquire()
        assert limiter.remaining == 0
        limiter.reset()
        assert limiter.remaining == 2


class TestBatchProcessor:
    def test_basic_batch(self):
        processor = BatchProcessor(
            chain_or_fn=lambda inputs: {"output": inputs["input"].upper()},
            max_workers=1,
        )
        results = processor.run(["hello", "world"])
        assert len(results) == 2
        assert results.success_rate == 1.0

    def test_error_handling(self):
        def flaky(inputs):
            if inputs["input"] == "fail":
                raise ValueError("boom")
            return {"output": inputs["input"]}

        processor = BatchProcessor(chain_or_fn=flaky, max_workers=1, on_error="continue")
        results = processor.run(["ok", "fail", "ok2"])
        assert len(results.successes) == 2
        assert len(results.failures) == 1

    def test_batch_result_summary(self):
        result = BatchResult(
            results=[
                {"index": 0, "status": "success", "output": "a"},
                {"index": 1, "status": "error", "output": None},
            ],
            total_duration=1.5,
        )
        assert "1/2" in result.summary()
        assert result.success_rate == 0.5
