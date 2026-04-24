import re
from typing import Dict, List, Union

from cortexchain.llm.cortex import CortexLLM
from cortexchain.schema import AgentAction, AgentFinish
from cortexchain.tools.base import BaseTool

_REACT_TEMPLATE = """\
Answer the following question as best you can. You have access to the following tools:

{tool_descriptions}

Use EXACTLY this format:

Thought: think about what to do next
Action: one of [{tool_names}]
Action Input: the input to pass to the action
Observation: the result (filled in by the system)
... (repeat Thought/Action/Action Input/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer to the original question

Begin!

Question: {input}
Thought:"""

_ACTION_RE = re.compile(
    r"Action:\s*(.+?)\s*\nAction Input:\s*(.+?)(?:\n|$)", re.IGNORECASE
)
_FINAL_RE = re.compile(r"Final Answer:\s*(.+)", re.IGNORECASE | re.DOTALL)


class ReActAgent:
    """ReAct-style agent that reasons and acts using the provided tools."""

    def __init__(self, llm: CortexLLM, tools: List[BaseTool]):
        self.llm = llm
        self.tools = {t.name: t for t in tools}

    def _tool_descriptions(self) -> str:
        return "\n".join(
            f"- {t.name}: {t.description}" for t in self.tools.values()
        )

    def plan(
        self, scratchpad: str, question: str
    ) -> Union[AgentAction, AgentFinish]:
        """Send current state to LLM and parse its next step."""
        prompt = _REACT_TEMPLATE.format(
            tool_descriptions=self._tool_descriptions(),
            tool_names=", ".join(self.tools.keys()),
            input=question,
        )
        if scratchpad:
            prompt += f"\n{scratchpad}"

        response = self.llm(prompt)

        final_match = _FINAL_RE.search(response)
        if final_match:
            return AgentFinish(output=final_match.group(1).strip(), log=response)

        action_match = _ACTION_RE.search(response)
        if action_match:
            return AgentAction(
                tool=action_match.group(1).strip(),
                tool_input=action_match.group(2).strip(),
                log=response,
            )

        # LLM gave a direct answer without the expected format
        return AgentFinish(output=response.strip(), log=response)
