# API Reference: Utilities

## Retry

### @retry Decorator

```python
from cortexchain import retry, RetryConfig

@retry(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(LLMError,))
def call_api():
    ...

# Or with RetryConfig
config = RetryConfig(max_attempts=5, delay=0.5, backoff=2.0)

@retry(config=config)
def call_api():
    ...
```

### FallbackChain

```python
class FallbackChain:
    def __init__(self, chains: List[BaseChain])
    def invoke(self, inputs: Dict) -> Dict  # Tries each chain until one succeeds
```

## Cache

### LLMCache

```python
class LLMCache:
    def __init__(self, cache_dir: str = ".llm_cache", ttl_seconds: int = 3600)
    def get(self, prompt: str) -> Optional[str]
    def set(self, prompt: str, response: str) -> None
    def clear(self) -> None
    def stats(self) -> Dict[str, Any]  # {"disk_entries": int, ...}
```

## Rate Limiting

### RateLimiter

```python
class RateLimiter:
    def __init__(self, max_calls: int, period: float = 60.0)
    def acquire(self) -> None  # Blocks if limit reached
    def reset(self) -> None
    @property
    def remaining(self) -> int

    # Also works as a decorator:
    @limiter
    def my_function(): ...
```

### RateLimitedLLM

```python
class RateLimitedLLM:
    def __init__(self, llm: CortexLLM, max_calls: int = 60, period: float = 60.0)
    def invoke(self, prompt: str, chat_history: str = "") -> LLMResult
```

## Batch Processing

### BatchProcessor

```python
class BatchProcessor:
    def __init__(self, chain_or_fn: Callable, max_workers: int = 4, on_error: str = "raise")
    def run(self, inputs: List[str]) -> BatchResult
```

### BatchResult

```python
class BatchResult:
    results: List[Dict]
    total_duration: float

    @property
    def successes(self) -> List[Dict]
    @property
    def failures(self) -> List[Dict]
    @property
    def success_rate(self) -> float
    def summary(self) -> str
```

## Validation

### Decorators

```python
@validate_inputs(required=["key"], types={"key": str}, max_length={"key": 5000}, validators={"k": lambda v: v > 0})
def my_func(inputs): ...

@validate_not_empty("query", "context")
def my_func(inputs): ...

@validate_schema({"name": str, "age": int})
def my_func(inputs): ...
```

### InputValidator (composable)

```python
class InputValidator:
    def require(self, *keys: str) -> InputValidator
    def type_check(self, schema: Dict[str, type]) -> InputValidator
    def add_rule(self, key: str, check: Callable, message: str) -> InputValidator
    def max_length(self, key: str, length: int) -> InputValidator
    def validate(self, inputs: Dict) -> List[str]  # Returns error list
    def wrap(self, chain) -> chain  # Patches chain.invoke() with validation
```

## Configuration

### CortexConfig

```python
@dataclass
class CortexConfig:
    base_url: str
    agent_name: str
    default_knowledge: bool
    request_timeout: int
    rate_limit_calls: int
    rate_limit_period: float
    max_retries: int
    retry_delay: float
    cache_enabled: bool
    cache_ttl: int
    cache_dir: str
    log_level: str
    log_file: Optional[str]
    verbose: bool

    def to_dict(self) -> Dict[str, Any]
```

Global singleton: `from cortexchain.config import config`

## Logging

```python
def setup_logging(level: str = "INFO", log_file: str = None, format_string: str = None) -> Logger
def get_logger(name: str = None) -> Logger
def set_level(level: str) -> None
def quiet() -> None     # Set to WARNING
def verbose() -> None   # Set to DEBUG
```

## Exceptions

```python
CortexChainError              # Base
├── LLMError                  # API call failures
│   ├── LLMConnectionError   # Network unreachable
│   ├── LLMTimeoutError      # Request timeout
│   └── LLMRateLimitError    # Rate limited
├── ChainError                # Chain execution failure
├── OutputParserError         # Parsing failure
├── ToolError                 # Tool execution failure
├── GraphError                # Graph execution failure
│   ├── GraphNodeNotFoundError
│   └── GraphCycleError
├── ValidationError           # Input validation
├── ConfigError               # Configuration issues
└── RetryExhaustedError       # All retries failed
```
