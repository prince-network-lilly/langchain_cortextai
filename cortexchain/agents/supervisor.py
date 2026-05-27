"""Multi-agent system — supervisor delegates tasks to specialized worker agents."""

import re
from typing import Callable, Dict, List, Optional

from cortexchain.agents.executor import AgentExecutor
from cortexchain.agents.react import ReActAgent
from cortexchain.llm.cortex import CortexLLM
from cortexchain.tools.base import BaseTool

_SUPERVISOR_TEMPLATE = """\
You are a supervisor managing a team of specialized workers.
Given a user request, decide which worker should handle it (or if it needs multiple workers).

Available workers:
{worker_descriptions}

Rules:
- Respond with ONLY the worker name to delegate to.
- If the task is complete, respond with "FINISH".
- If the task needs multiple steps, delegate to one worker at a time.

Conversation so far:
{history}

User request: {input}

Which worker should handle this next (or FINISH)?
Worker:"""


class WorkerAgent:
    """A specialized worker agent with a name, description, and executor."""

    def __init__(
        self,
        name: str,
        description: str,
        llm: CortexLLM,
        tools: List[BaseTool] = None,
        executor: Optional[AgentExecutor] = None,
    ):
        self.name = name
        self.description = description
        if executor:
            self.executor = executor
        else:
            tools = tools or []
            agent = ReActAgent(llm=llm, tools=tools)
            self.executor = AgentExecutor(agent=agent, tools=tools)

    def run(self, task: str) -> str:
        return self.executor.run(task)


class SupervisorAgent:
    """Orchestrates multiple worker agents using an LLM-based supervisor."""

    def __init__(
        self,
        llm: CortexLLM,
        workers: List[WorkerAgent],
        max_rounds: int = 10,
        verbose: bool = False,
    ):
        self.llm = llm
        self.workers = {w.name: w for w in workers}
        self.max_rounds = max_rounds
        self.verbose = verbose

    def _worker_descriptions(self) -> str:
        return "\n".join(f"- {w.name}: {w.description}" for w in self.workers.values())

    def invoke(self, inputs: Dict) -> Dict:
        user_input = inputs.get("input", "")
        history = []
        final_output = ""

        for round_num in range(self.max_rounds):
            history_str = "\n".join(history) if history else "(none)"
            prompt = _SUPERVISOR_TEMPLATE.format(
                worker_descriptions=self._worker_descriptions(),
                history=history_str,
                input=user_input,
            )
            decision = self.llm(prompt).strip()

            if self.verbose:
                print(f"\n[Supervisor Round {round_num + 1}] -> {decision}")

            if "FINISH" in decision.upper():
                break

            # Find the worker
            chosen_worker = None
            for name in self.workers:
                if name.lower() in decision.lower():
                    chosen_worker = self.workers[name]
                    break

            if not chosen_worker:
                history.append(f"Supervisor: Could not find worker '{decision}'")
                continue

            # Delegate to worker
            if self.verbose:
                print(f"  [Delegating to '{chosen_worker.name}']")

            worker_result = chosen_worker.run(user_input)
            history.append(f"{chosen_worker.name}: {worker_result}")
            final_output = worker_result

            if self.verbose:
                print(f"  [Result]: {worker_result[:200]}")

        return {"output": final_output, "history": history}

    def run(self, question: str) -> str:
        return self.invoke({"input": question})["output"]
