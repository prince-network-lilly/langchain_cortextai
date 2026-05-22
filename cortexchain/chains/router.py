from typing import Callable, Dict, List, Optional
from cortexchain.chains.base import BaseChain
from cortexchain.chains.llm_chain import LLMChain
from cortexchain.llm.cortex import CortexLLM
from cortexchain.prompts.templates import PromptTemplate

_ROUTER_TEMPLATE = """\
Given the following input, select the most appropriate destination from the options below.

Destinations:
{destinations}

Input: {input}

Respond with ONLY the name of the destination (nothing else)."""


class RouterChain(BaseChain):
    """Routes input to one of several destination chains based on LLM classification."""

    def __init__(
        self,
        llm: CortexLLM,
        destination_chains: Dict[str, BaseChain],
        default_chain: Optional[BaseChain] = None,
        router_prompt: Optional[PromptTemplate] = None,
    ):
        self.llm = llm
        self.destination_chains = destination_chains
        self.default_chain = default_chain
        self.router_prompt = router_prompt or PromptTemplate.from_template(_ROUTER_TEMPLATE)

    def _build_destinations_str(self) -> str:
        lines = []
        for name, chain in self.destination_chains.items():
            desc = getattr(chain, "description", name)
            lines.append(f"- {name}: {desc}")
        return "\n".join(lines)

    def route(self, input_text: str) -> str:
        """Determine which destination to route to."""
        formatted = self.router_prompt.format(
            destinations=self._build_destinations_str(),
            input=input_text,
        )
        choice = self.llm(formatted).strip().lower()
        # Fuzzy match against destination names
        for name in self.destination_chains:
            if name.lower() in choice or choice in name.lower():
                return name
        return ""

    def invoke(self, inputs: Dict) -> Dict:
        input_text = inputs.get("input", "")
        destination = self.route(input_text)

        if destination and destination in self.destination_chains:
            chain = self.destination_chains[destination]
        elif self.default_chain:
            chain = self.default_chain
        else:
            return {"output": f"No matching destination for input: {input_text!r}", "route": "none"}

        result = chain(inputs)
        output_key = getattr(chain, "output_key", "text")
        output = result.get(output_key, result.get("output", result.get("response", "")))
        return {"output": output, "route": destination, "_chain_result": result}

    def run(self, input_text: str) -> str:
        return self.invoke({"input": input_text})["output"]

    @property
    def _default_input_key(self) -> str:
        return "input"
