"""Rate limiter — throttle API calls to stay within rate limits."""
import time
import threading
from typing import Optional


class RateLimiter:
    """Token-bucket rate limiter for API calls.

    Usage:
        limiter = RateLimiter(max_calls=10, period=60)  # 10 calls per minute

        @limiter
        def call_api():
            ...

        # Or manual:
        limiter.acquire()
        call_api()
    """

    def __init__(self, max_calls: int = 10, period: float = 60.0):
        self.max_calls = max_calls
        self.period = period
        self._calls: list = []
        self._lock = threading.Lock()

    def acquire(self) -> None:
        """Block until a call slot is available."""
        while True:
            with self._lock:
                now = time.time()
                # Remove expired entries
                self._calls = [t for t in self._calls if now - t < self.period]
                if len(self._calls) < self.max_calls:
                    self._calls.append(now)
                    return
            # Wait before retrying
            sleep_time = self._calls[0] + self.period - time.time()
            if sleep_time > 0:
                time.sleep(min(sleep_time, 1.0))

    def __call__(self, func):
        """Use as a decorator to rate-limit a function."""
        def wrapper(*args, **kwargs):
            self.acquire()
            return func(*args, **kwargs)
        wrapper.__name__ = getattr(func, "__name__", "wrapped")
        return wrapper

    @property
    def remaining(self) -> int:
        """Number of calls remaining in the current window."""
        with self._lock:
            now = time.time()
            active = [t for t in self._calls if now - t < self.period]
            return self.max_calls - len(active)

    def reset(self) -> None:
        with self._lock:
            self._calls.clear()


class RateLimitedLLM:
    """Wraps a CortexLLM with rate limiting."""

    def __init__(self, llm, max_calls: int = 10, period: float = 60.0):
        self._llm = llm
        self._limiter = RateLimiter(max_calls=max_calls, period=period)

    def invoke(self, prompt: str, chat_history: str = ""):
        self._limiter.acquire()
        return self._llm.invoke(prompt, chat_history)

    def __call__(self, prompt: str, chat_history: str = "") -> str:
        self._limiter.acquire()
        return self._llm(prompt, chat_history)

    @property
    def remaining_calls(self) -> int:
        return self._limiter.remaining

    def __getattr__(self, name):
        return getattr(self._llm, name)
