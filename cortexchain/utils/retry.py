"""Retry and fallback utilities for resilient LLM calls."""

import time
import functools
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple, Type


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    retry_on: Tuple[Type[Exception], ...] = (Exception,)


def retry(
    config: Optional[RetryConfig] = None,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
):
    """Decorator that retries a function on failure with exponential backoff.

    Usage:
        @retry(max_retries=3)
        def call_api(): ...

        @retry(config=RetryConfig(max_retries=5, backoff_factor=3))
        def call_api(): ...
    """
    if config is None:
        config = RetryConfig(
            max_retries=max_retries,
            initial_delay=initial_delay,
            backoff_factor=backoff_factor,
        )

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = config.initial_delay
            last_exception = None

            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except config.retry_on as e:
                    last_exception = e
                    if attempt == config.max_retries:
                        raise
                    time.sleep(min(delay, config.max_delay))
                    delay *= config.backoff_factor

            raise last_exception

        return wrapper

    return decorator


class FallbackChain:
    """Tries multiple LLMs/chains in order; returns the first successful result."""

    def __init__(self, chains: List, verbose: bool = False):
        self.chains = chains
        self.verbose = verbose

    def invoke(self, inputs) -> dict:
        errors = []
        for i, chain in enumerate(self.chains):
            try:
                result = chain(inputs) if callable(chain) else chain.invoke(inputs)
                if self.verbose:
                    print(f"[Fallback] Chain #{i} succeeded")
                return result
            except Exception as e:
                errors.append(f"Chain #{i}: {e}")
                if self.verbose:
                    print(f"[Fallback] Chain #{i} failed: {e}")

        raise RuntimeError(f"All {len(self.chains)} chains failed:\n" + "\n".join(errors))

    def run(self, input_text: str) -> str:
        result = self.invoke({"input": input_text})
        for key in ("output", "text", "response", "answer"):
            if key in result:
                return result[key]
        return str(result)
