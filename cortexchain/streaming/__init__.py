"""Streaming support — stream LLM responses and chain outputs."""

from typing import Callable, Dict, Generator, Optional

from cortexchain.llm.cortex import CortexLLM
from cortexchain.schema import LLMResult


class StreamingCortexLLM:
    """CortexLLM wrapper that yields response in simulated chunks.

    Note: If the Cortex API supports streaming (SSE), override _stream_raw().
    Default implementation simulates streaming by yielding word-by-word.
    """

    def __init__(
        self,
        agent_name: str,
        base_url: str = "https://api.cortex.lilly.com",
        default_knowledge: bool = False,
        chunk_size: int = 5,
    ):
        self._llm = CortexLLM(
            agent_name=agent_name,
            base_url=base_url,
            default_knowledge=default_knowledge,
        )
        self.chunk_size = chunk_size

    def stream(self, prompt: str, chat_history: str = "") -> Generator[str, None, None]:
        """Yield response in chunks (words). Override for true SSE streaming."""
        result = self._llm.invoke(prompt, chat_history)
        words = result.message.split(" ")
        buffer = []
        for word in words:
            buffer.append(word)
            if len(buffer) >= self.chunk_size:
                yield " ".join(buffer) + " "
                buffer = []
        if buffer:
            yield " ".join(buffer)

    def invoke(self, prompt: str, chat_history: str = "") -> LLMResult:
        return self._llm.invoke(prompt, chat_history)

    def __call__(self, prompt: str, chat_history: str = "") -> str:
        return self._llm(prompt, chat_history)


class StreamingChain:
    """Wraps any chain to yield partial results as they're produced."""

    def __init__(self, chain, streaming_llm: Optional[StreamingCortexLLM] = None):
        self.chain = chain
        self.streaming_llm = streaming_llm

    def stream(self, inputs: Dict) -> Generator[Dict, None, None]:
        """Yield intermediate results. Final yield contains the complete result."""
        if hasattr(self.chain, "prompt") and self.streaming_llm:
            # Stream the LLM response
            formatted = self.chain.prompt.format(**inputs)
            accumulated = ""
            for chunk in self.streaming_llm.stream(formatted):
                accumulated += chunk
                yield {"chunk": chunk, "partial": accumulated, "done": False}
            yield {"chunk": "", "partial": accumulated, "done": True, "output": accumulated}
        else:
            # Fallback: just invoke and yield the full result
            result = self.chain.invoke(inputs) if hasattr(self.chain, "invoke") else self.chain(inputs)
            output_key = getattr(self.chain, "output_key", "text")
            output = result.get(output_key, result.get("output", ""))
            yield {"chunk": output, "partial": output, "done": True, "output": output}


def stream_to_stdout(stream_generator: Generator) -> str:
    """Utility: prints streaming output to console and returns full result."""
    full_output = ""
    for event in stream_generator:
        if event.get("chunk") and not event.get("done"):
            print(event["chunk"], end="", flush=True)
            full_output = event.get("partial", "")
        elif event.get("done"):
            full_output = event.get("output", event.get("partial", ""))
    print()
    return full_output
