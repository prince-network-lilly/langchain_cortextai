# Contributing to CortexChain

Thank you for your interest in contributing to **cortexchain**! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.9+
- Git
- Access to the Eli Lilly internal network (for `light_client` dependency)

### Clone & Install

```bash
git clone https://github.com/prince-network-lilly/langchain_cortextai.git
cd langchain_cortextai

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"
```

### Environment Setup

```bash
cp .env.example .env
# Edit .env with your Cortex agent name and preferences
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=cortexchain --cov-report=term-missing

# Run a specific test file
pytest tests/test_integration.py -v

# Run async tests only
pytest tests/test_async.py -v
```

## Code Quality

```bash
# Format code
black cortexchain/ tests/
isort cortexchain/ tests/

# Lint
flake8 cortexchain/ --max-line-length=120

# Type check
mypy cortexchain/ --ignore-missing-imports
```

## Project Structure

```
cortexchain/
├── __init__.py          # Package exports
├── schema.py            # Core data classes (LLMResult, Document, etc.)
├── config.py            # Configuration management
├── exceptions.py        # Exception hierarchy
├── logging.py           # Logging setup
├── validation.py        # Input validation decorators
├── async_support.py     # Async LLM and chain support
├── llm/                 # LLM wrappers
│   └── cortex.py        # CortexLLM (main API wrapper)
├── prompts/             # Prompt templates and hub
├── memory/              # Conversation memory
├── chains/              # Chain implementations
├── tools/               # Tool system (base + built-in + MLOps)
├── agents/              # Agent patterns (ReAct, Supervisor, Plan-Execute)
├── graph/               # StateGraph engine (LangGraph-like)
├── streaming/           # Streaming support
├── toolkits/            # Pre-built tool collections
├── output_parsers/      # JSON, List, Regex parsers
├── callbacks/           # Callback system
├── document_loaders/    # Text, CSV, JSON loaders
├── text_splitters/      # Character and recursive splitters
├── retrievers/          # TF-IDF retriever
└── utils/               # Retry, cache, rate limiter, batch
```

## Making Changes

### Branch Naming

```
feature/short-description
fix/bug-description
docs/what-changed
```

### Commit Messages

Follow conventional commits:

```
feat: add new tool for X
fix: handle empty response from Cortex API
docs: update README with new examples
test: add integration tests for router chain
refactor: simplify agent executor loop
```

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all tests pass: `pytest tests/ -v`
4. Ensure code is formatted: `black --check cortexchain/ tests/`
5. Open a PR with a clear description of what and why

## Adding a New Tool

1. Create `cortexchain/tools/your_tool.py`:

```python
from cortexchain.tools.base import BaseTool

class YourTool(BaseTool):
    name = "your_tool"
    description = "What this tool does"

    def run(self, tool_input: str) -> str:
        # Implementation here
        return result
```

2. Export in `cortexchain/__init__.py`
3. Add tests in `tests/test_tools.py`
4. Optionally add to a toolkit in `cortexchain/toolkits/`

## Adding a New Chain

1. Create `cortexchain/chains/your_chain.py`:

```python
from typing import Dict
from cortexchain.chains.base import BaseChain

class YourChain(BaseChain):
    def invoke(self, inputs: Dict) -> Dict:
        # Implementation here
        return {"output": result}
```

2. Export in `cortexchain/__init__.py`
3. Add tests in `tests/`

## Design Principles

- **Zero external dependencies** (beyond `light_client`) for core functionality
- **LangChain-compatible patterns** — users familiar with LangChain should feel at home
- **Production-first** — rate limiting, caching, retries, and validation built-in
- **Type safety** — all public APIs should have type annotations
- **Testable** — mock-friendly design, no hidden global state

## Questions?

Reach out to the team or open an issue on the repository.
