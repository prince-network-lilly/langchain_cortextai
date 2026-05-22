# Installation

## Requirements

- Python 3.9 or higher
- Access to Eli Lilly internal network (for `light_client` dependency)

## Standard Install

```bash
pip install git+https://github.com/prince-network-lilly/langchain_cortextai.git
```

This installs `cortexchain` and its sole dependency (`light_client`) automatically.

## Install with Dev Dependencies

For development (testing, linting, type checking):

```bash
pip install "cortexchain[dev] @ git+https://github.com/prince-network-lilly/langchain_cortextai.git"
```

This adds: pytest, pytest-cov, pytest-asyncio, flake8, black, isort, mypy.

## Install from Source

```bash
git clone https://github.com/prince-network-lilly/langchain_cortextai.git
cd langchain_cortextai
pip install -e ".[dev]"
```

## Verify Installation

```python
import cortexchain
print(cortexchain.__version__)  # Should print 0.6.0
```

## Environment Setup

Copy the example environment file:

```bash
cp .env.example .env
```

At minimum, set your agent name:

```bash
CORTEX_AGENT_NAME=your-cortex-agent-name
```

See [Configuration](configuration.md) for all available settings.
