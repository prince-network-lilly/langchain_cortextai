# CortexChain

[![CI](https://github.com/prince-network-lilly/langchain_cortextai/actions/workflows/ci.yml/badge.svg)](https://github.com/prince-network-lilly/langchain_cortextai/actions/workflows/ci.yml)
[![Security](https://github.com/prince-network-lilly/langchain_cortextai/actions/workflows/security.yml/badge.svg)](https://github.com/prince-network-lilly/langchain_cortextai/actions/workflows/security.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Version](https://img.shields.io/badge/version-1.0.0-green.svg)](https://github.com/prince-network-lilly/langchain_cortextai/releases)
[![License: Internal](https://img.shields.io/badge/license-Eli%20Lilly%20Internal-red.svg)]()

**A production-grade LangChain + LangGraph framework for the Lilly Cortex AI API.**

CortexChain lets you build AI-powered applications using familiar LangChain/LangGraph patterns — chains, agents, tools, graphs, memory — all wired to the internal Cortex AI platform with zero external AI dependencies.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CortexChain v1.0.0                        │
├─────────────┬──────────────┬──────────────┬─────────────────────┤
│   Chains    │    Agents    │    Graph     │      Utilities      │
│             │              │              │                     │
│ LLMChain    │ ReActAgent   │ StateGraph   │ RateLimiter         │
│ Sequential  │ Supervisor   │ Conditional  │ Cache (TTL)         │
│ Router      │ Plan&Execute │ Checkpoint   │ BatchProcessor      │
│ RAG (QA)    │ AgentExec    │ Human-Loop   │ Retry/Fallback      │
│ MapReduce   │ Multi-Agent  │ Subgraphs    │ ConnectionPool      │
│ Structured  │              │ Parallel     │ Profiler            │
├─────────────┼──────────────┼──────────────┼─────────────────────┤
│   Tools     │   Security   │  Prompts     │    Observability    │
│             │              │              │                     │
│ Python REPL │ Sanitizer    │ Templates    │ Callbacks           │
│ HTTP/REST   │ Injection    │ PromptHub    │ FileLogger (JSONL)  │
│ SQL (R/O)   │   Defense    │ Secure       │ Console Debug       │
│ File I/O    │ Redaction    │   Template   │ Profiling/Latency   │
│ Shell       │              │              │ Logging (Python)    │
│ Data Valid  │              │              │                     │
│ Experiment  │              │              │                     │
│ Pipeline    │              │              │                     │
│ API Health  │              │              │                     │
├─────────────┴──────────────┴──────────────┴─────────────────────┤
│                         CortexLLM Core                           │
│              (LIGHTClient → Cortex /model/ask API)               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Installation

```bash
# Standard install
pip install git+https://github.com/prince-network-lilly/langchain_cortextai.git

# With development tools (testing, linting, type checking)
pip install "cortexchain[dev] @ git+https://github.com/prince-network-lilly/langchain_cortextai.git"

# Pin a specific version
pip install git+https://github.com/prince-network-lilly/langchain_cortextai.git@v1.0.0

# From source
git clone https://github.com/prince-network-lilly/langchain_cortextai.git
cd langchain_cortextai
pip install -e ".[dev]"
```

**Requirements:** Python 3.9+ and access to the Eli Lilly internal network.

---

## Quick Start

### 1. Basic LLM Call

```python
from cortexchain import CortexLLM

llm = CortexLLM(agent_name="my-cortex-agent")
answer = llm("What is machine learning?")
print(answer)
```

### 2. Chain Pipeline

```python
from cortexchain import CortexLLM, LLMChain, PromptTemplate

llm = CortexLLM(agent_name="my-agent")
prompt = PromptTemplate(template="Summarize this for a {audience}: {text}")
chain = LLMChain(llm=llm, prompt=prompt)

result = chain.run(audience="executive", text="Long technical document...")
```

### 3. Conversation with Memory

```python
from cortexchain import CortexLLM, ConversationChain

llm = CortexLLM(agent_name="my-agent")
chat = ConversationChain(llm=llm)

print(chat("Hi, my name is Alice")["text"])
print(chat("What's my name?")["text"])  # Remembers "Alice"
```

### 4. Tool-Using Agent

```python
from cortexchain import CortexLLM, ReActAgent, AgentExecutor, tool

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

llm = CortexLLM(agent_name="my-agent")
agent = ReActAgent(llm=llm, tools=[calculator])
executor = AgentExecutor(agent=agent, tools=[calculator])
print(executor.run("What is 15 * 23 + 7?"))
```

### 5. Graph Workflow

```python
from cortexchain import StateGraph, END

graph = StateGraph()
graph.add_node("fetch", lambda s: {**s, "data": "fetched"})
graph.add_node("process", lambda s: {**s, "result": s["data"].upper()})
graph.add_edge("fetch", "process")
graph.add_edge("process", END)
graph.set_entry_point("fetch")

app = graph.compile()
result = app.invoke({"input": "go"})
# result["result"] == "FETCHED"
```

### 6. RAG (Retrieval-Augmented Generation)

```python
from cortexchain import CortexLLM, RetrievalQAChain, TFIDFRetriever, Document

docs = [
    Document(page_content="Our refund policy allows returns within 30 days."),
    Document(page_content="Shipping takes 3-5 business days."),
]
retriever = TFIDFRetriever.from_documents(docs, k=2)
llm = CortexLLM(agent_name="my-agent")

qa = RetrievalQAChain(llm=llm, retriever=retriever)
answer = qa.run(query="What is the refund policy?")
```

### 7. Secure Input Handling

```python
from cortexchain import InputSanitizer, LLMChain

sanitizer = InputSanitizer(check_injection=True)
safe_chain = sanitizer.wrap(my_chain)

safe_chain({"query": "Normal question"})  # Works
# safe_chain({"query": "Ignore all previous instructions"})  # Blocked!
```

### 8. Async & Batch Processing

```python
import asyncio
from cortexchain import AsyncCortexLLM

async def main():
    llm = AsyncCortexLLM(agent_name="my-agent")
    results = await llm.abatch([
        "Summarize document 1",
        "Summarize document 2",
        "Summarize document 3",
    ], max_concurrency=3)
    for r in results:
        print(r.message)

asyncio.run(main())
```

### 9. Multi-Agent Orchestration

```python
from cortexchain import CortexLLM, SupervisorAgent, WorkerAgent

llm = CortexLLM(agent_name="my-agent")

researcher = WorkerAgent(name="researcher", llm=llm, tools=[search_tool])
writer = WorkerAgent(name="writer", llm=llm, tools=[])

supervisor = SupervisorAgent(llm=llm, workers=[researcher, writer])
result = supervisor.run("Research AI trends and write a summary report")
```

### 10. Performance Profiling

```python
from cortexchain.profiling import profiler, enable_profiling

enable_profiling()

with profiler.measure("full_pipeline"):
    result = chain.invoke(inputs)

print(profiler.summary())
```

---

## Feature Overview

| Category | Components |
|----------|-----------|
| **LLM** | `CortexLLM`, `AsyncCortexLLM`, `PooledCortexLLM`, `StreamingCortexLLM`, `RateLimitedLLM` |
| **Chains** | `LLMChain`, `ConversationChain`, `SimpleSequentialChain`, `RouterChain`, `RetrievalQAChain`, `StructuredOutputChain`, `MapReduceChain`, `RefineChain` |
| **Memory** | `ConversationBufferMemory`, `ConversationWindowMemory` |
| **Tools** | `@tool` decorator, `PythonREPLTool`, `HTTPRequestTool`, `SQLDatabaseTool`, `ShellTool`, `ReadFileTool`, `WriteFileTool`, + 4 MLOps tools |
| **Agents** | `ReActAgent`, `AgentExecutor`, `SupervisorAgent`/`WorkerAgent`, `PlanAndExecuteAgent` |
| **Graph** | `StateGraph`, conditional edges, `MemoryCheckpointer`, `FileCheckpointer`, human-in-the-loop, subgraphs, parallel execution |
| **Security** | `sanitize_input()`, `detect_injection()`, `SecurePromptTemplate`, `InputSanitizer`, `redact_sensitive()` |
| **Utilities** | `@retry`, `FallbackChain`, `LLMCache`, `RateLimiter`, `BatchProcessor`, `ConnectionPool`, `Profiler` |
| **Validation** | `@validate_inputs`, `@validate_not_empty`, `@validate_schema`, `InputValidator` |
| **Observability** | `ConsoleCallback`, `FileLoggerCallback`, `setup_logging()`, `Profiler`, `LatencyTracker` |
| **Toolkits** | `MLOpsToolkit`, `DataToolkit`, `DevToolkit`, `APIToolkit` |

---

## Configuration

Copy `.env.example` to `.env` and set your values:

```bash
CORTEX_AGENT_NAME=your-agent-name
CORTEX_CACHE_ENABLED=true
CORTEX_RATE_LIMIT_CALLS=30
CORTEX_LOG_LEVEL=INFO
```

All configuration can also be set programmatically:

```python
from cortexchain.config import config

config.agent_name = "my-agent"
config.cache_enabled = True
config.verbose = True
```

See [Configuration Docs](docs/getting-started/configuration.md) for all 15+ options.

---

## Documentation

Full documentation is available in the `docs/` directory:

| Section | Description |
|---------|-------------|
| [Installation](docs/getting-started/installation.md) | Setup and install instructions |
| [Quick Start](docs/getting-started/quickstart.md) | 7 patterns to get started |
| [Configuration](docs/getting-started/configuration.md) | All env vars and settings |
| [LLM](docs/concepts/llm.md) | CortexLLM, async, rate limiting |
| [Chains](docs/concepts/chains.md) | All chain types explained |
| [Agents](docs/concepts/agents.md) | ReAct, Supervisor, Plan-Execute |
| [Graph](docs/concepts/graph.md) | StateGraph, checkpoints, human-in-loop |
| [API Reference](docs/api/) | Complete API signatures |
| [Examples](docs/examples/) | RAG, multi-agent, MLOps workflows |

To serve docs locally:
```bash
pip install mkdocs-material mkdocstrings[python]
mkdocs serve
```

---

## Development

```bash
# Setup
git clone https://github.com/prince-network-lilly/langchain_cortextai.git
cd langchain_cortextai
pip install -e ".[dev]"
pre-commit install

# Run tests
pytest tests/ -v --cov=cortexchain --cov-report=term-missing

# Lint & format
black cortexchain/ tests/
isort cortexchain/ tests/
flake8 cortexchain/ --max-line-length=120

# Type check
mypy cortexchain/ --ignore-missing-imports

# Security scan
bandit -r cortexchain/ -ll
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full development guidelines.

---

## Security

CortexChain includes built-in security features:

- **Prompt injection detection** — 15+ pattern-based rules with configurable response
- **Input sanitization** — HTML stripping, control char removal, length limits
- **Sensitive data redaction** — Automatic PII removal before logging
- **Tool safety** — Read-only DB mode, command whitelists, domain restrictions
- **CI/CD scanning** — Bandit SAST, pip-audit, TruffleHog secrets, CodeQL, Dependabot

See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## Project Stats

| Metric | Value |
|--------|-------|
| Public API exports | 120+ |
| Test files | 15 |
| Test cases | 110+ |
| Documentation pages | 14 |
| CI/CD workflows | 4 (test, lint, security, docs) |
| External AI dependencies | 0 (only `light_client`) |
| Python versions supported | 3.9, 3.10, 3.11, 3.12 |

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full version history.

---

## Roadmap

- [ ] WebSocket streaming from Cortex API (when available)
- [ ] Vector store integrations (FAISS, Chroma)
- [ ] LangSmith-compatible tracing export
- [ ] OpenTelemetry integration
- [ ] Multi-model routing (GPT-4, Claude, Llama via Cortex)

---

## License

Internal use only — Eli Lilly and Company.
