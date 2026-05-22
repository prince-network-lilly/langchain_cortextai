import json
import time
from datetime import datetime
from typing import Dict
from cortexchain.callbacks.base import BaseCallback


class FileLoggerCallback(BaseCallback):
    """Logs all events to a JSONL file for audit/analysis."""

    def __init__(self, log_file: str = "cortexchain.log"):
        self.log_file = log_file

    def _log(self, event_type: str, data: Dict) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event_type,
            **data,
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def on_llm_start(self, prompt: str, **kwargs) -> None:
        self._log("llm_start", {"prompt_length": len(prompt), "prompt_preview": prompt[:200]})

    def on_llm_end(self, response: str, **kwargs) -> None:
        self._log("llm_end", {"response_length": len(response), "response_preview": response[:200]})

    def on_llm_error(self, error: Exception, **kwargs) -> None:
        self._log("llm_error", {"error": str(error)})

    def on_chain_start(self, chain_name: str, inputs: Dict, **kwargs) -> None:
        self._log("chain_start", {"chain": chain_name, "input_keys": list(inputs.keys())})

    def on_chain_end(self, chain_name: str, outputs: Dict, **kwargs) -> None:
        self._log("chain_end", {"chain": chain_name, "output_keys": list(outputs.keys())})

    def on_chain_error(self, chain_name: str, error: Exception, **kwargs) -> None:
        self._log("chain_error", {"chain": chain_name, "error": str(error)})

    def on_tool_start(self, tool_name: str, tool_input: str, **kwargs) -> None:
        self._log("tool_start", {"tool": tool_name, "input": tool_input})

    def on_tool_end(self, tool_name: str, output: str, **kwargs) -> None:
        self._log("tool_end", {"tool": tool_name, "output": output[:500]})

    def on_tool_error(self, tool_name: str, error: Exception, **kwargs) -> None:
        self._log("tool_error", {"tool": tool_name, "error": str(error)})

    def on_agent_action(self, action: str, tool_input: str, **kwargs) -> None:
        self._log("agent_action", {"action": action, "input": tool_input})

    def on_agent_finish(self, output: str, **kwargs) -> None:
        self._log("agent_finish", {"output": output[:500]})
