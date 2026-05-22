# Configuration

CortexChain reads configuration from environment variables. All settings have sensible defaults.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CORTEX_BASE_URL` | `https://api.cortex.lilly.com` | Cortex API base URL |
| `CORTEX_AGENT_NAME` | `""` | Default agent name |
| `CORTEX_DEFAULT_KNOWLEDGE` | `false` | Enable default knowledge base |
| `CORTEX_TIMEOUT` | `120` | Request timeout in seconds |
| `CORTEX_RATE_LIMIT_CALLS` | `60` | Max API calls per period |
| `CORTEX_RATE_LIMIT_PERIOD` | `60` | Rate limit period in seconds |
| `CORTEX_MAX_RETRIES` | `3` | Max retry attempts on failure |
| `CORTEX_RETRY_DELAY` | `1.0` | Delay between retries (seconds) |
| `CORTEX_CACHE_ENABLED` | `false` | Enable response caching |
| `CORTEX_CACHE_TTL` | `3600` | Cache time-to-live (seconds) |
| `CORTEX_CACHE_DIR` | `.llm_cache` | Cache directory path |
| `CORTEX_LOG_LEVEL` | `INFO` | Logging level |
| `CORTEX_LOG_FILE` | `None` | Log file path (optional) |
| `CORTEX_VERBOSE` | `false` | Enable verbose/debug output |

## Programmatic Configuration

```python
from cortexchain.config import config

# Override settings at runtime
config.base_url = "https://custom.endpoint.com"
config.agent_name = "my-agent"
config.cache_enabled = True
config.verbose = True

# View current config
print(config.to_dict())
```

## Using CortexConfig Directly

```python
from cortexchain.config import CortexConfig

# Create a custom config (doesn't affect global)
my_config = CortexConfig(
    base_url="https://staging.cortex.lilly.com",
    agent_name="staging-agent",
    max_retries=5,
)
```

## Logging Setup

```python
from cortexchain.logging import setup_logging, quiet, verbose

# Full setup
setup_logging(level="DEBUG", log_file="app.log")

# Quick toggles
verbose()  # DEBUG level
quiet()    # WARNING only
```

## Production Recommendations

```bash
# .env for production
CORTEX_CACHE_ENABLED=true
CORTEX_CACHE_TTL=1800
CORTEX_RATE_LIMIT_CALLS=30
CORTEX_MAX_RETRIES=5
CORTEX_LOG_LEVEL=WARNING
CORTEX_LOG_FILE=/var/log/cortexchain.log
```
