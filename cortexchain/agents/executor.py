from typing import Dict, List

from cortexchain.agents.react import ReActAgent
from cortexchain.schema import AgentAction, AgentFinish
from cortexchain.tools.base import BaseTool


class AgentExecutor:
    """Runs a ReActAgent in a loop, executing tools until a final answer is reached."""

    def __init__(
        self,
        agent: ReActAgent,
        tools: List[BaseTool],
        max_iterations: int = 10,
        verbose: bool = False,
    ):
        self.agent = agent
        self.tools = {t.name: t for t in tools}
        self.max_iterations = max_iterations
        self.verbose = verbose

    @classmethod
    def from_agent_and_tools(
        cls,
        agent: ReActAgent,
        tools: List[BaseTool],
        **kwargs,
    ) -> "AgentExecutor":
        return cls(agent=agent, tools=tools, **kwargs)

    def invoke(self, inputs: Dict) -> Dict:
        question = inputs.get("input", inputs.get("question", ""))
        scratchpad = ""

        for iteration in range(self.max_iterations):
            step = self.agent.plan(scratchpad, question)

            if isinstance(step, AgentFinish):
                if self.verbose:
                    print(f"\n[Final Answer]: {step.output}")
                return {"output": step.output}

            if isinstance(step, AgentAction):
                if self.verbose:
                    print(f"\n[Action]: {step.tool}({step.tool_input!r})")

                tool_fn = self.tools.get(step.tool)
                if tool_fn is None:
                    observation = (
                        f"Unknown tool: {step.tool!r}. "
                        f"Available tools: {list(self.tools.keys())}"
                    )
                else:
                    observation = tool_fn.run(step.tool_input)

                if self.verbose:
                    print(f"[Observation]: {observation}")

                scratchpad += f"\n{step.log}\nObservation: {observation}\nThought:"

        return {"output": "Reached maximum iterations without a final answer."}

    def run(self, question: str) -> str:
        """Convenience method: pass a question string, get back the answer string."""
        return self.invoke({"input": question})["output"]
