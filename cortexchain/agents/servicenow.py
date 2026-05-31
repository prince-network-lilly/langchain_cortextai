"""High-level ServiceNow agent — caller supplies the LLM (and optionally the
executor); this class owns the three table tools and the tool-use retry loop.

Usage A — caller provides the LLM, class builds the executor:
    from cortexchain import CortexLLM
    from cortexchain.agents import ServiceNowAgent

    llm = CortexLLM(agent_name="my-agent")
    snow = ServiceNowAgent(
        llm=llm,
        instance_url="https://acme.service-now.com",
        user="svc_account",
        password="hunter2",
        assignment_group="GCCP-CMO-GLB",
    )
    print(snow.ask("top 5 open incidents assigned to Jaimin"))

Usage B — caller provides a fully-wired AgentExecutor (already has tools):
    snow = ServiceNowAgent.from_executor(
        executor=my_executor,
        instance_url="...", user="...", password="...",
    )
"""

from typing import List, Optional

from cortexchain.agents.executor import AgentExecutor
from cortexchain.agents.react import ReActAgent
from cortexchain.llm.cortex import CortexLLM
from cortexchain.tools.base import BaseTool
from cortexchain.tools.servicenow import (
    ChangeRequestSearchTool,
    IncidentSearchTool,
    ServiceRequestSearchTool,
)


_RETRY_PREAMBLE = (
    "REMINDER: your previous attempt did not call any tool. You MUST emit:\n"
    "Action: <tool_name>\nAction Input: <JSON object>\n"
    "before any Final Answer. Try again.\n\n"
)


class ServiceNowAgent:
    """ServiceNow Q&A wrapper. Caller owns the LLM/executor wiring; this class
    owns the three Table API tools and the retry loop that forces tool use."""

    def __init__(
        self,
        llm: CortexLLM,
        instance_url: str,
        user: str,
        password: str,
        assignment_group: Optional[str] = None,
        verbose: bool = False,
        max_iterations: int = 1,
        max_retries: int = 1,
    ):
        self._max_retries = max_retries
        self._tool_calls = {"count": 0}

        common = dict(
            instance_url=instance_url,
            user=user,
            password=password,
            default_assignment_group=assignment_group,
        )
        tools: List[BaseTool] = [
            self._wrap(ChangeRequestSearchTool(**common)),
            self._wrap(ServiceRequestSearchTool(**common)),
            self._wrap(IncidentSearchTool(**common)),
        ]
        self._executor = AgentExecutor(
            agent=ReActAgent(llm=llm, tools=tools),
            tools=tools,
            verbose=verbose,
            max_iterations=max_iterations,
        )

    @classmethod
    def from_executor(
        cls,
        executor: AgentExecutor,
        max_retries: int = 2,
    ) -> "ServiceNowAgent":
        """Wrap an already-built executor. Use when you've wired your own
        agent/tools and just want the retry loop and a friendlier surface."""
        obj = cls.__new__(cls)
        obj._executor = executor
        obj._max_retries = max_retries
        obj._tool_calls = {"count": 0}
        # Instrument whatever tools the executor was built with so the
        # retry loop can detect skipped tool calls.
        for tool in executor.tools.values():
            obj._wrap(tool)
        return obj

    # ---- internals -----------------------------------------------------

    def _wrap(self, tool: BaseTool) -> BaseTool:
        """Patch tool.run() so we know whether the agent actually invoked it."""
        if getattr(tool, "_snow_counted", False):
            return tool
        original_run = tool.run

        def counted_run(tool_input: str) -> str:
            self._tool_calls["count"] += 1
            return original_run(tool_input)

        tool.run = counted_run
        tool._snow_counted = True
        return tool

    # ---- public API ----------------------------------------------------

    def ask(self, prompt: str) -> str:
        """Run a natural-language query, retrying if the LLM skips tool use."""
        question = prompt
        last_result = ""
        for _ in range(self._max_retries + 1):
            self._tool_calls["count"] = 0
            last_result = self._executor.run(question)
            if self._tool_calls["count"] > 0:
                return last_result
            question = _RETRY_PREAMBLE + prompt
        return (
            f"Could not get the model to call a tool after "
            f"{self._max_retries + 1} attempts.\n{last_result}"
        )

    def __call__(self, prompt: str) -> str:
        return self.ask(prompt)