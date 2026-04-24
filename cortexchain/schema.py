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
class AgentAction:
    tool: str
    tool_input: str
    log: str


@dataclass
class AgentFinish:
    output: str
    log: str
