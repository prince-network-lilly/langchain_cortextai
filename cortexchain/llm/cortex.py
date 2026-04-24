from typing import Optional
from cortexchain.schema import LLMResult

try:
    from light_client import LIGHTClient
except ImportError as e:
    raise ImportError(
        "light_client is required. Install it in your environment before using CortexLLM."
    ) from e


class CortexLLM:
    """Wrapper around the Lilly Cortex /model/ask API endpoint."""

    def __init__(
        self,
        agent_name: str,
        base_url: str = "https://api.cortex.lilly.com",
        default_knowledge: bool = False,
    ):
        self.agent_name = agent_name
        self.base_url = base_url.rstrip("/")
        self.default_knowledge = default_knowledge
        self._client = LIGHTClient()

    def _build_url(self) -> str:
        url = f"{self.base_url}/model/ask/{self.agent_name}"
        if self.default_knowledge:
            url += "?default_knowledge=true"
        return url

    def invoke(self, prompt: str, chat_history: str = "") -> LLMResult:
        """Call the Cortex API and return a structured LLMResult."""
        data: dict = {"q": prompt}
        if chat_history:
            data["chat_history"] = chat_history
        resp = self._client.post(self._build_url(), data=data)
        raw = resp.json()
        return LLMResult(
            message=raw.get("message", ""),
            llm_model=raw.get("llm_model", ""),
            llm_model_display_name=raw.get("llm_model_display_name", ""),
            source_metadata=raw.get("source_metadata", []),
            steps=raw.get("steps", []),
            raw=raw,
        )

    def __call__(self, prompt: str, chat_history: str = "") -> str:
        return self.invoke(prompt, chat_history).message

    def __repr__(self) -> str:
        return f"CortexLLM(agent_name={self.agent_name!r})"
