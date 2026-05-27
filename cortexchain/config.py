"""Central configuration management for cortexchain."""

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CortexConfig:
    """Global configuration for cortexchain. Reads from env vars with sensible defaults.

    Usage:
        from cortexchain.config import config

        # Uses env vars or defaults:
        llm = CortexLLM(agent_name=config.agent_name, base_url=config.base_url)

        # Override programmatically:
        config.base_url = "https://custom.endpoint.com"
        config.default_knowledge = True
    """

    # API settings
    base_url: str = field(default_factory=lambda: os.getenv("CORTEX_BASE_URL", "https://api.cortex.lilly.com"))
    agent_name: str = field(default_factory=lambda: os.getenv("CORTEX_AGENT_NAME", ""))
    default_knowledge: bool = field(
        default_factory=lambda: os.getenv("CORTEX_DEFAULT_KNOWLEDGE", "false").lower() in ("true", "1", "yes")
    )

    # Timeouts
    request_timeout: int = field(default_factory=lambda: int(os.getenv("CORTEX_TIMEOUT", "120")))

    # Rate limiting
    rate_limit_calls: int = field(default_factory=lambda: int(os.getenv("CORTEX_RATE_LIMIT_CALLS", "60")))
    rate_limit_period: float = field(default_factory=lambda: float(os.getenv("CORTEX_RATE_LIMIT_PERIOD", "60")))

    # Retry settings
    max_retries: int = field(default_factory=lambda: int(os.getenv("CORTEX_MAX_RETRIES", "3")))
    retry_delay: float = field(default_factory=lambda: float(os.getenv("CORTEX_RETRY_DELAY", "1.0")))

    # Cache settings
    cache_enabled: bool = field(
        default_factory=lambda: os.getenv("CORTEX_CACHE_ENABLED", "false").lower() in ("true", "1", "yes")
    )
    cache_ttl: int = field(default_factory=lambda: int(os.getenv("CORTEX_CACHE_TTL", "3600")))
    cache_dir: str = field(default_factory=lambda: os.getenv("CORTEX_CACHE_DIR", ".llm_cache"))

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("CORTEX_LOG_LEVEL", "INFO"))
    log_file: Optional[str] = field(default_factory=lambda: os.getenv("CORTEX_LOG_FILE", None))

    # Verbose mode
    verbose: bool = field(default_factory=lambda: os.getenv("CORTEX_VERBOSE", "false").lower() in ("true", "1", "yes"))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_url": self.base_url,
            "agent_name": self.agent_name,
            "default_knowledge": self.default_knowledge,
            "request_timeout": self.request_timeout,
            "rate_limit_calls": self.rate_limit_calls,
            "rate_limit_period": self.rate_limit_period,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "log_level": self.log_level,
            "verbose": self.verbose,
        }

    def __repr__(self) -> str:
        return f"CortexConfig(base_url={self.base_url!r}, agent_name={self.agent_name!r})"


# Global singleton — import this everywhere
config = CortexConfig()
