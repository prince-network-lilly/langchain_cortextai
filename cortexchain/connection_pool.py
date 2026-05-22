"""Connection pooling and session management for CortexLLM."""
import threading
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass, field


@dataclass
class SessionConfig:
    """Configuration for session management."""
    pool_size: int = 4
    max_idle_time: float = 300.0
    retry_on_disconnect: bool = True
    health_check_interval: float = 60.0


class ConnectionPool:
    """Thread-safe connection pool for LIGHTClient instances.

    Reuses client connections to avoid repeated authentication handshakes
    and TCP connection setup overhead.

    Usage:
        pool = ConnectionPool(pool_size=4)
        client = pool.acquire()
        try:
            response = client.post(url, data=data)
        finally:
            pool.release(client)

        # Or use as context manager:
        with pool.connection() as client:
            response = client.post(url, data=data)
    """

    def __init__(self, pool_size: int = 4, client_factory=None):
        self._pool_size = pool_size
        self._factory = client_factory or self._default_factory
        self._pool: list = []
        self._in_use: set = set()
        self._lock = threading.Lock()
        self._condition = threading.Condition(self._lock)
        self._created = 0
        self._total_acquires = 0
        self._total_releases = 0

    @staticmethod
    def _default_factory():
        from light_client import LIGHTClient
        return LIGHTClient()

    def acquire(self, timeout: float = 30.0):
        """Acquire a client from the pool. Blocks if all clients are in use."""
        deadline = time.time() + timeout

        with self._condition:
            while True:
                if self._pool:
                    client = self._pool.pop()
                    self._in_use.add(id(client))
                    self._total_acquires += 1
                    return client

                if self._created < self._pool_size:
                    client = self._factory()
                    self._created += 1
                    self._in_use.add(id(client))
                    self._total_acquires += 1
                    return client

                remaining = deadline - time.time()
                if remaining <= 0:
                    raise TimeoutError(
                        f"Could not acquire connection within {timeout}s. "
                        f"Pool size: {self._pool_size}, in use: {len(self._in_use)}"
                    )
                self._condition.wait(timeout=remaining)

    def release(self, client):
        """Return a client to the pool."""
        with self._condition:
            self._in_use.discard(id(client))
            self._pool.append(client)
            self._total_releases += 1
            self._condition.notify()

    def connection(self):
        """Context manager for acquiring/releasing a connection."""
        return _PooledConnection(self)

    @property
    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "pool_size": self._pool_size,
                "available": len(self._pool),
                "in_use": len(self._in_use),
                "created": self._created,
                "total_acquires": self._total_acquires,
                "total_releases": self._total_releases,
            }

    def close(self):
        """Close all connections in the pool."""
        with self._lock:
            self._pool.clear()
            self._in_use.clear()
            self._created = 0


class _PooledConnection:
    """Context manager for pool.connection()."""

    def __init__(self, pool: ConnectionPool):
        self._pool = pool
        self._client = None

    def __enter__(self):
        self._client = self._pool.acquire()
        return self._client

    def __exit__(self, *exc):
        if self._client:
            self._pool.release(self._client)
            self._client = None


class PooledCortexLLM:
    """CortexLLM that uses connection pooling for better throughput.

    Ideal for high-concurrency scenarios (web servers, batch processing).

    Usage:
        llm = PooledCortexLLM(agent_name="my-agent", pool_size=8)
        result = llm.invoke("Hello")  # Uses pooled connection
        print(llm.pool_stats)  # View pool metrics
    """

    def __init__(
        self,
        agent_name: str,
        base_url: str = "https://api.cortex.lilly.com",
        default_knowledge: bool = False,
        pool_size: int = 4,
    ):
        self.agent_name = agent_name
        self.base_url = base_url.rstrip("/")
        self.default_knowledge = default_knowledge
        self._pool = ConnectionPool(pool_size=pool_size)

    def _build_url(self) -> str:
        url = f"{self.base_url}/model/ask/{self.agent_name}"
        if self.default_knowledge:
            url += "?default_knowledge=true"
        return url

    def invoke(self, prompt: str, chat_history: str = ""):
        from cortexchain.schema import LLMResult

        data: dict = {"q": prompt}
        if chat_history:
            data["chat_history"] = chat_history

        with self._pool.connection() as client:
            resp = client.post(self._build_url(), data=data)

        raw = resp.json()
        return LLMResult(
            message=raw.get("message", ""),
            llm_model=raw.get("llm_model", ""),
            llm_model_display_name=raw.get("llm_model_display_name", ""),
            source_metadata=raw.get("source_metadata", []),
            steps=raw.get("steps", []),
            raw=raw,
        )

    def __call__(self, prompt: str, chat_history: str = "") -> str:
        return self.invoke(prompt, chat_history).message

    @property
    def pool_stats(self) -> Dict[str, Any]:
        return self._pool.stats

    def close(self):
        self._pool.close()

    def __repr__(self) -> str:
        return f"PooledCortexLLM(agent_name={self.agent_name!r}, pool_size={self._pool._pool_size})"

    def __del__(self):
        self.close()
