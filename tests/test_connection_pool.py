"""Tests for cortexchain.connection_pool"""
import threading
import time
import pytest
from unittest.mock import MagicMock
from cortexchain.connection_pool import ConnectionPool, PooledCortexLLM


class TestConnectionPool:
    def test_acquire_and_release(self):
        factory = MagicMock(return_value="client_1")
        pool = ConnectionPool(pool_size=2, client_factory=factory)

        client = pool.acquire()
        assert client == "client_1"
        assert pool.stats["in_use"] == 1

        pool.release(client)
        assert pool.stats["in_use"] == 0
        assert pool.stats["available"] == 1

    def test_reuses_connections(self):
        call_count = 0

        def counting_factory():
            nonlocal call_count
            call_count += 1
            return f"client_{call_count}"

        pool = ConnectionPool(pool_size=2, client_factory=counting_factory)

        c1 = pool.acquire()
        pool.release(c1)
        c2 = pool.acquire()

        assert c1 == c2
        assert call_count == 1

    def test_pool_limit(self):
        factory = MagicMock(side_effect=lambda: MagicMock())
        pool = ConnectionPool(pool_size=2, client_factory=factory)

        c1 = pool.acquire()
        c2 = pool.acquire()

        with pytest.raises(TimeoutError):
            pool.acquire(timeout=0.1)

        pool.release(c1)
        c3 = pool.acquire(timeout=0.1)
        assert c3 is not None

    def test_context_manager(self):
        factory = MagicMock(return_value="ctx_client")
        pool = ConnectionPool(pool_size=2, client_factory=factory)

        with pool.connection() as client:
            assert client == "ctx_client"
            assert pool.stats["in_use"] == 1

        assert pool.stats["in_use"] == 0

    def test_concurrent_access(self):
        factory = MagicMock(side_effect=lambda: MagicMock())
        pool = ConnectionPool(pool_size=4, client_factory=factory)
        results = []

        def worker():
            with pool.connection() as client:
                time.sleep(0.01)
                results.append(True)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(results) == 8
        assert pool.stats["in_use"] == 0

    def test_stats(self):
        factory = MagicMock(return_value="client")
        pool = ConnectionPool(pool_size=3, client_factory=factory)

        c1 = pool.acquire()
        stats = pool.stats
        assert stats["pool_size"] == 3
        assert stats["in_use"] == 1
        assert stats["total_acquires"] == 1
        pool.release(c1)

    def test_close(self):
        factory = MagicMock(return_value="client")
        pool = ConnectionPool(pool_size=2, client_factory=factory)
        pool.acquire()
        pool.close()
        assert pool.stats["available"] == 0
        assert pool.stats["created"] == 0
