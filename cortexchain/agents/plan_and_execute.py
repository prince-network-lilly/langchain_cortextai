"""Plan-and-Execute agent — decomposes complex tasks into steps then executes them."""
import re
from typing import Dict, List, Optional

from cortexchain.llm.cortex import CortexLLM
from cortexchain.agents.executor import AgentExecutor
from cortexchain.agents.react import ReActAgent
from cortexchain.tools.base import BaseTool

_PLANNER_TEMPLATE = """\
You are a planner. Given a complex task, break it into a numbered list of simple steps.
Each step should be specific and actionable.

Task: {input}

Create a plan (numbered list of steps):"""

_EXECUTOR_TEMPLATE = """\
You are an executor. Complete the following step using the tools available to you.

Overall objective: {objective}
Current step: {step}
Previous results: {previous_results}

Complete this step and provide the result:"""

_REPLANNER_TEMPLATE = """\
You are a replanner. Given the original objective and progress so far, decide what to do next.

Original objective: {objective}
Completed steps and results:
{completed}

Remaining plan:
{remaining}

If the objective is fully achieved, respond with exactly: "DONE"
Otherwise, provide an updated remaining plan (numbered list):"""


class PlanAndExecuteAgent:
    """Decomposes a complex task into steps, executes each step, and replans if needed."""

    def __init__(
        self,
        llm: CortexLLM,
        tools: List[BaseTool] = None,
        executor: Optional[AgentExecutor] = None,
        max_steps: int = 10,
        replan: bool = True,
        verbose: bool = False,
    ):
        self.llm = llm
        self.tools = tools or []
        self.max_steps = max_steps
        self.replan = replan
        self.verbose = verbose

        if executor:
            self.executor = executor
        elif self.tools:
            agent = ReActAgent(llm=llm, tools=self.tools)
            self.executor = AgentExecutor(agent=agent, tools=self.tools)
        else:
            self.executor = None

    def _create_plan(self, task: str) -> List[str]:
        prompt = _PLANNER_TEMPLATE.format(input=task)
        response = self.llm(prompt)
        steps = re.findall(r"^\s*\d+[\.\)]\s*(.+)$", response, re.MULTILINE)
        return steps if steps else [response.strip()]

    def _execute_step(self, step: str, objective: str, previous: str) -> str:
        if self.executor:
            context = f"Objective: {objective}\nStep: {step}\nPrevious: {previous}"
            return self.executor.run(context)
        else:
            prompt = _EXECUTOR_TEMPLATE.format(
                objective=objective, step=step, previous_results=previous
            )
            return self.llm(prompt)

    def _replan(self, objective: str, completed: List[Dict], remaining: List[str]) -> List[str]:
        completed_str = "\n".join(
            f"  {i+1}. {c['step']} -> {c['result'][:100]}"
            for i, c in enumerate(completed)
        )
        remaining_str = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(remaining))

        prompt = _REPLANNER_TEMPLATE.format(
            objective=objective,
            completed=completed_str or "(none)",
            remaining=remaining_str or "(none)",
        )
        response = self.llm(prompt).strip()

        if "DONE" in response.upper():
            return []

        steps = re.findall(r"^\s*\d+[\.\)]\s*(.+)$", response, re.MULTILINE)
        return steps if steps else []

    def invoke(self, inputs: Dict) -> Dict:
        objective = inputs.get("input", inputs.get("objective", ""))

        if self.verbose:
            print(f"\n[Plan-and-Execute] Objective: {objective}")

        # Phase 1: Plan
        plan = self._create_plan(objective)
        if self.verbose:
            print(f"[Plan] {len(plan)} steps:")
            for i, s in enumerate(plan):
                print(f"  {i+1}. {s}")

        # Phase 2: Execute
        completed = []
        for step_num in range(self.max_steps):
            if not plan:
                break

            current_step = plan.pop(0)
            if self.verbose:
                print(f"\n[Execute Step {step_num + 1}] {current_step}")

            previous_str = "; ".join(
                f"{c['step']}: {c['result'][:80]}" for c in completed[-3:]
            )
            result = self._execute_step(current_step, objective, previous_str)
            completed.append({"step": current_step, "result": result})

            if self.verbose:
                print(f"  [Result] {result[:150]}")

            # Phase 3: Replan if enabled and steps remain
            if self.replan and plan:
                new_plan = self._replan(objective, completed, plan)
                if not new_plan:
                    if self.verbose:
                        print("[Replanner] Objective achieved!")
                    break
                plan = new_plan

        final_result = completed[-1]["result"] if completed else "No steps executed."
        return {
            "output": final_result,
            "steps": completed,
            "plan": plan,
        }

    def run(self, task: str) -> str:
        return self.invoke({"input": task})["output"]
