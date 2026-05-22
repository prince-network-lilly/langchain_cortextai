# Changelog

All notable changes to **cortexchain** will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-22

### Added
- Connection pooling (`cortexchain/connection_pool.py`)
  - `ConnectionPool` — thread-safe pool with acquire/release/context manager
  - `PooledCortexLLM` — high-throughput LLM wrapper using pooled connections
- Profiling and telemetry (`cortexchain/profiling.py`)
  - `Profiler` with `@track` decorator and `measure()` context manager
  - `LatencyTracker` with SLO compliance monitoring
  - `enable_profiling()` / `disable_profiling()` global controls
- Complete README rewrite with architecture diagram, 10 quick-start examples, badges
- Production-grade `.gitignore` covering all artifacts

### Changed
- **Version 1.0.0** — production release
- All version references updated across package

## [0.7.0] - 2026-05-22

### Added
- Security scanning CI (`.github/workflows/security.yml`)
  - pip-audit vulnerability check
  - Safety dependency scan
  - Bandit SAST (Static Application Security Testing)
  - TruffleHog secrets detection
  - CodeQL semantic analysis
- Dependabot configuration (`.github/dependabot.yml`)
- Pre-commit hooks (`.pre-commit-config.yaml`)
  - detect-secrets, black, isort, bandit, large file check
- Prompt injection defense (`cortexchain/security.py`)
  - `detect_injection()` — 15+ pattern-based rules
  - `sanitize_input()` — HTML strip, control chars, length limit
  - `SecurePromptTemplate` — sanitizes all template variables
  - `InputSanitizer` — composable sanitizer with `.wrap(chain)`
  - `redact_sensitive()` — PII redaction (email, phone, SSN, tokens)
- Security tests (`tests/test_security.py`) — 20 test cases
- `SECURITY.md` — vulnerability reporting policy

## [0.6.0] - 2026-05-22

### Added
- MkDocs documentation site (`mkdocs.yml` + `docs/` with 14 pages)
- GitHub Actions docs deployment (`.github/workflows/docs.yml`)
- Getting Started guides: installation, quick start, configuration
- Core Concepts docs: LLM, Chains, Agents, Graph
- API Reference: full signatures for all modules
- Example docs: basic usage, RAG pipeline, multi-agent, MLOps
- `.env.example` with all 15+ configuration variables
- `CONTRIBUTING.md` with dev setup, code quality, and contribution guidelines

## [0.5.0] - 2026-05-22

### Added
- `py.typed` marker for PEP 561 type-checking support
- Integration test suite with full end-to-end chain testing (`tests/test_integration.py`)
- Shared test fixtures via `tests/conftest.py`
- `CHANGELOG.md` for tracking version history
- `pytest.ini` configuration for async test support

### Changed
- Dev dependencies expanded: pytest-cov, pytest-asyncio, flake8, black, isort, mypy

## [0.4.0] - 2026-05-22

### Added
- GitHub Actions CI/CD workflow (`.github/workflows/ci.yml`)
  - Matrix testing on Python 3.9–3.12
  - Linting (flake8, black, isort)
  - Type checking (mypy)
  - Coverage reporting
  - Package build validation
- Async support (`cortexchain/async_support.py`)
  - `AsyncCortexLLM` with `ainvoke()` and `abatch()`
  - `AsyncLLMChain` with `ainvoke()`, `arun()`, `abatch()`
  - `AsyncSequentialChain` for async pipelines
- Input validation (`cortexchain/validation.py`)
  - `@validate_inputs` decorator (required fields, types, custom validators, max_length)
  - `@validate_not_empty` decorator
  - `@validate_schema` decorator
  - `InputValidator` composable class with `.wrap(chain)` support
- Exception hierarchy (`cortexchain/exceptions.py`)
  - `CortexChainError`, `LLMError`, `ChainError`, `ToolError`, `GraphError`, etc.
- Configuration management (`cortexchain/config.py`)
  - `CortexConfig` dataclass reading from environment variables
- Logging integration (`cortexchain/logging.py`)
  - `setup_logging()`, `get_logger()`, `set_level()`, `quiet()`, `verbose()`
- Test suite: 11 test files, 80+ test cases

## [0.3.0] - 2026-05-21

### Added
- Streaming support (`cortexchain/streaming/`)
  - `StreamingCortexLLM` with simulated token streaming
  - `StreamingChain` for streaming chain outputs
  - `stream_to_stdout()` utility
- Toolkits (`cortexchain/toolkits/`)
  - `MLOpsToolkit` — data validation + experiment tracking + pipeline monitoring
  - `DataToolkit` — file + SQL + HTTP tools
  - `DevToolkit` — Python REPL + shell + file tools
  - `APIToolkit` — HTTP + health check tools
- Production utilities (`cortexchain/utils/`)
  - `@retry` decorator with `RetryConfig`
  - `FallbackChain` with ordered fallbacks
  - `LLMCache` (disk-backed with TTL)
  - `RateLimiter` (token bucket algorithm)
  - `RateLimitedLLM` wrapper
  - `BatchProcessor` with parallel execution and error handling

## [0.2.0] - 2026-05-21

### Added
- Graph execution engine (`cortexchain/graph/`)
  - `StateGraph` with `add_node()`, `add_edge()`, `add_conditional_edges()`
  - `CompiledGraph` with `invoke()` and `stream()`
  - `MemoryCheckpointer` and `FileCheckpointer`
  - Human-in-the-loop: `HumanApprovalNode`, `InterruptibleGraph`, `@require_approval`
  - Subgraphs: `SubgraphNode`, `ParallelNode`, `ParallelThreadedNode`
  - Visualization: `visualize_graph()`, `print_graph()`
- Agent system (`cortexchain/agents/`)
  - `ReActAgent` — Thought/Action/Observation loop
  - `AgentExecutor` — tool execution with max iterations
  - `SupervisorAgent` + `WorkerAgent` — multi-agent orchestration
  - `PlanAndExecuteAgent` — decompose, execute, replan pattern
- MLOps tools
  - `DataValidationTool` — schema/null/type validation
  - `ExperimentTrackerTool` — log/compare/best experiments
  - `PipelineMonitorTool` — status/health/alerts
  - `APIHealthCheckTool` — batch endpoint checking
  - `ShellTool` — safe command execution with whitelist

## [0.1.0] - 2026-05-21

### Added
- Initial release
- `CortexLLM` — wrapper for Lilly Cortex `/model/ask` API
- `PromptTemplate` with `|` pipe operator and `PromptHub`
- `ConversationBufferMemory` and `ConversationWindowMemory`
- Chains: `LLMChain`, `ConversationChain`, `SimpleSequentialChain`, `RouterChain`, `RetrievalQAChain`, `StructuredOutputChain`, `MapReduceChain`, `RefineChain`
- Tools: `BaseTool`, `FunctionTool`, `@tool` decorator, `PythonREPLTool`, `HTTPRequestTool`, `ReadFileTool`, `WriteFileTool`, `ListDirectoryTool`, `SQLDatabaseTool`
- Output parsers: `JSONOutputParser`, `ListOutputParser`, `RegexParser`
- Callbacks: `BaseCallback`, `CallbackManager`, `ConsoleCallback`, `FileLoggerCallback`
- Document loaders: `TextLoader`, `CSVLoader`, `JSONLoader`
- Text splitters: `CharacterTextSplitter`, `RecursiveCharacterTextSplitter`
- Retrievers: `TFIDFRetriever` (zero-dependency TF-IDF with cosine similarity)
- Schema: `LLMResult`, `Message`, `Document`, `AgentAction`, `AgentFinish`, `GraphState`
- PEP 508 install support via `pip install git+...`
