# API Reference: LLM

## CortexLLM

```python
class CortexLLM:
    def __init__(self, agent_name: str, base_url: str = "https://api.cortex.lilly.com", default_knowledge: bool = False)
    def invoke(self, prompt: str, chat_history: str = "") -> LLMResult
    def __call__(self, prompt: str, chat_history: str = "") -> str
```

## AsyncCortexLLM

```python
class AsyncCortexLLM:
    def __init__(self, agent_name: str, base_url: str = "...", default_knowledge: bool = False, max_workers: int = 4)
    async def ainvoke(self, prompt: str, chat_history: str = "") -> LLMResult
    async def __call__(self, prompt: str, chat_history: str = "") -> str
    async def abatch(self, prompts: list, max_concurrency: int = 4) -> list
```

## StreamingCortexLLM

```python
class StreamingCortexLLM:
    def __init__(self, agent_name: str, chunk_size: int = 5)
    def stream(self, prompt: str) -> Iterator[str]
```

## RateLimitedLLM

```python
class RateLimitedLLM:
    def __init__(self, llm: CortexLLM, max_calls: int = 60, period: float = 60.0)
    def invoke(self, prompt: str, chat_history: str = "") -> LLMResult
    def __call__(self, prompt: str) -> str
```
