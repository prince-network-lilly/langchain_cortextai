from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class LLMResult:
    message: str
    llm_model: str = ""
    llm_model_display_name: str = ""
    source_metadata: List[Any] = field(default_factory=list)
    steps: List[Any] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.message


@dataclass
class Message:
    role: str  # "human" or "ai"
    content: str

    def __str__(self) -> str:
        return f"{self.role}: {self.content}"


@dataclass
class Document:
    """A piece of text with associated metadata (used for RAG, loaders, splitters)."""
    page_content: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        return self.page_content

    def __len__(self) -> int:
        return len(self.page_content)


@dataclass
class AgentAction:
    tool: str
    tool_input: str
    log: str


@dataclass
class AgentFinish:
    output: str
    log: str


@dataclass
class GraphState:
    """State object passed through graph nodes."""
    data: Dict[str, Any] = field(default_factory=dict)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def update(self, other: Dict[str, Any]) -> None:
        self.data.update(other)

    def copy(self) -> "GraphState":
        return GraphState(data=self.data.copy())

