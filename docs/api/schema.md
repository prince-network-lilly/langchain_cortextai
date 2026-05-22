# API Reference: Schema

Core data classes used throughout CortexChain.

## LLMResult

```python
@dataclass
class LLMResult:
    message: str
    llm_model: str = ""
    llm_model_display_name: str = ""
    source_metadata: List[Any] = field(default_factory=list)
    steps: List[Any] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)
```

Returned by `CortexLLM.invoke()`. Access the text via `result.message` or `str(result)`.

## Message

```python
@dataclass
class Message:
    role: str   # "human" or "ai"
    content: str
```

Used internally by memory and conversation chains.

## Document

```python
@dataclass
class Document:
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
```

Used by document loaders, text splitters, and retrievers. Supports `len()` and `str()`.

## GraphState

```python
@dataclass
class GraphState:
    data: Dict[str, Any] = field(default_factory=dict)
```

Dict-like state object for graph nodes. Supports `[]`, `.get()`, `.update()`, `.copy()`.

## AgentAction

```python
@dataclass
class AgentAction:
    tool: str
    tool_input: str
    log: str
```

Represents a tool call decision made by an agent.

## AgentFinish

```python
@dataclass
class AgentFinish:
    output: str
    log: str
```

Represents the agent's final answer (no more tool calls needed).
