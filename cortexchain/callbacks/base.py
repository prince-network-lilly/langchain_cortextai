from abc import ABC
from typing import Any, Dict, List, Optional
import time


class BaseCallback(ABC):
    """Base class for callbacks. Override any method you want to hook into."""

    def on_llm_start(self, prompt: str, **kwargs) -> None:
        pass

    def on_llm_end(self, response: str, **kwargs) -> None:
        pass

    def on_llm_error(self, error: Exception, **kwargs) -> None:
        pass

    def on_chain_start(self, chain_name: str, inputs: Dict, **kwargs) -> None:
        pass

    def on_chain_end(self, chain_name: str, outputs: Dict, **kwargs) -> None:
        pass

    def on_chain_error(self, chain_name: str, error: Exception, **kwargs) -> None:
        pass

    def on_tool_start(self, tool_name: str, tool_input: str, **kwargs) -> None:
        pass

    def on_tool_end(self, tool_name: str, output: str, **kwargs) -> None:
        pass

    def on_tool_error(self, tool_name: str, error: Exception, **kwargs) -> None:
        pass

    def on_agent_action(self, action: str, tool_input: str, **kwargs) -> None:
        pass

    def on_agent_finish(self, output: str, **kwargs) -> None:
        pass


class CallbackManager:
    """Manages a list of callbacks and dispatches events to all of them."""

    def __init__(self, callbacks: Optional[List[BaseCallback]] = None):
        self.callbacks = callbacks or []

    def add(self, callback: BaseCallback) -> None:
        self.callbacks.append(callback)

    def remove(self, callback: BaseCallback) -> None:
        self.callbacks.remove(callback)

    def _dispatch(self, method_name: str, **kwargs) -> None:
        for cb in self.callbacks:
            method = getattr(cb, method_name, None)
            if method:
                try:
                    method(**kwargs)
                except Exception:
                    pass  # Never let a callback crash the main flow

    def on_llm_start(self, prompt: str, **kwargs) -> None:
        self._dispatch("on_llm_start", prompt=prompt, **kwargs)

    def on_llm_end(self, response: str, **kwargs) -> None:
        self._dispatch("on_llm_end", response=response, **kwargs)

    def on_llm_error(self, error: Exception, **kwargs) -> None:
        self._dispatch("on_llm_error", error=error, **kwargs)

    def on_chain_start(self, chain_name: str, inputs: Dict, **kwargs) -> None:
        self._dispatch("on_chain_start", chain_name=chain_name, inputs=inputs, **kwargs)

    def on_chain_end(self, chain_name: str, outputs: Dict, **kwargs) -> None:
        self._dispatch("on_chain_end", chain_name=chain_name, outputs=outputs, **kwargs)

    def on_chain_error(self, chain_name: str, error: Exception, **kwargs) -> None:
        self._dispatch("on_chain_error", chain_name=chain_name, error=error, **kwargs)

    def on_tool_start(self, tool_name: str, tool_input: str, **kwargs) -> None:
        self._dispatch("on_tool_start", tool_name=tool_name, tool_input=tool_input, **kwargs)

    def on_tool_end(self, tool_name: str, output: str, **kwargs) -> None:
        self._dispatch("on_tool_end", tool_name=tool_name, output=output, **kwargs)

    def on_tool_error(self, tool_name: str, error: Exception, **kwargs) -> None:
        self._dispatch("on_tool_error", tool_name=tool_name, error=error, **kwargs)

    def on_agent_action(self, action: str, tool_input: str, **kwargs) -> None:
        self._dispatch("on_agent_action", action=action, tool_input=tool_input, **kwargs)

    def on_agent_finish(self, output: str, **kwargs) -> None:
        self._dispatch("on_agent_finish", output=output, **kwargs)
