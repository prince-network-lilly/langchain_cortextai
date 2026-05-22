import time
from typing import Dict
from cortexchain.callbacks.base import BaseCallback


class ConsoleCallback(BaseCallback):
    """Prints all events to the console with timing info. Useful for debugging."""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._start_times: Dict[str, float] = {}

    def on_llm_start(self, prompt: str, **kwargs) -> None:
        self._start_times["llm"] = time.time()
        if self.verbose:
            preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
            print(f"\n{'='*60}")
            print(f"[LLM Start] Prompt: {preview}")

    def on_llm_end(self, response: str, **kwargs) -> None:
        elapsed = time.time() - self._start_times.get("llm", time.time())
        if self.verbose:
            preview = response[:150] + "..." if len(response) > 150 else response
            print(f"[LLM End] ({elapsed:.2f}s) Response: {preview}")
            print(f"{'='*60}")

    def on_llm_error(self, error: Exception, **kwargs) -> None:
        print(f"[LLM Error] {error}")

    def on_chain_start(self, chain_name: str, inputs: Dict, **kwargs) -> None:
        self._start_times[f"chain_{chain_name}"] = time.time()
        if self.verbose:
            print(f"\n[Chain Start] {chain_name} | inputs: {list(inputs.keys())}")

    def on_chain_end(self, chain_name: str, outputs: Dict, **kwargs) -> None:
        elapsed = time.time() - self._start_times.get(f"chain_{chain_name}", time.time())
        if self.verbose:
            print(f"[Chain End] {chain_name} ({elapsed:.2f}s) | outputs: {list(outputs.keys())}")

    def on_chain_error(self, chain_name: str, error: Exception, **kwargs) -> None:
        print(f"[Chain Error] {chain_name}: {error}")

    def on_tool_start(self, tool_name: str, tool_input: str, **kwargs) -> None:
        self._start_times[f"tool_{tool_name}"] = time.time()
        if self.verbose:
            print(f"  [Tool Start] {tool_name}({tool_input!r})")

    def on_tool_end(self, tool_name: str, output: str, **kwargs) -> None:
        elapsed = time.time() - self._start_times.get(f"tool_{tool_name}", time.time())
        if self.verbose:
            preview = output[:100] + "..." if len(output) > 100 else output
            print(f"  [Tool End] {tool_name} ({elapsed:.2f}s) -> {preview}")

    def on_tool_error(self, tool_name: str, error: Exception, **kwargs) -> None:
        print(f"  [Tool Error] {tool_name}: {error}")

    def on_agent_action(self, action: str, tool_input: str, **kwargs) -> None:
        if self.verbose:
            print(f"  [Agent Action] {action}({tool_input!r})")

    def on_agent_finish(self, output: str, **kwargs) -> None:
        if self.verbose:
            print(f"  [Agent Finish] {output[:200]}")
