from typing import List
from cortexchain.schema import Message


class ConversationBufferMemory:
    """Stores the full conversation history as a list of Messages."""

    def __init__(self, human_prefix: str = "Human", ai_prefix: str = "AI"):
        self.messages: List[Message] = []
        self.human_prefix = human_prefix
        self.ai_prefix = ai_prefix

    def add_user_message(self, content: str) -> None:
        self.messages.append(Message(role="human", content=content))

    def add_ai_message(self, content: str) -> None:
        self.messages.append(Message(role="ai", content=content))

    def get_history_string(self) -> str:
        lines = []
        for msg in self.messages:
            prefix = self.human_prefix if msg.role == "human" else self.ai_prefix
            lines.append(f"{prefix}: {msg.content}")
        return "\n".join(lines)

    def clear(self) -> None:
        self.messages.clear()

    def __len__(self) -> int:
        return len(self.messages)

    def __repr__(self) -> str:
        return f"ConversationBufferMemory(messages={len(self.messages)})"


class ConversationWindowMemory(ConversationBufferMemory):
    """Keeps only the last k human/AI exchange pairs in context."""

    def __init__(self, k: int = 5, **kwargs):
        super().__init__(**kwargs)
        self.k = k

    def get_history_string(self) -> str:
        recent = self.messages[-(self.k * 2):]
        lines = []
        for msg in recent:
            prefix = self.human_prefix if msg.role == "human" else self.ai_prefix
            lines.append(f"{prefix}: {msg.content}")
        return "\n".join(lines)

    def __repr__(self) -> str:
        return f"ConversationWindowMemory(k={self.k}, messages={len(self.messages)})"
