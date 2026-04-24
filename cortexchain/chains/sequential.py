from typing import Dict, List
from cortexchain.chains.base import BaseChain


class SimpleSequentialChain(BaseChain):
    """Runs a list of chains in sequence, piping each output as the next input."""

    def __init__(self, chains: List[BaseChain], verbose: bool = False):
        self.chains = chains
        self.verbose = verbose

    def invoke(self, inputs: Dict) -> Dict:
        current_input = inputs.get(self.chains[0]._default_input_key, "")

        for i, chain in enumerate(self.chains):
            result = chain.invoke({chain._default_input_key: current_input})
            output_key = getattr(chain, "output_key", "text")
            current_input = result.get(output_key, "")

            if self.verbose:
                print(f"[Step {i + 1}/{len(self.chains)}] -> {current_input[:120]}")

        return {"output": current_input}

    def run(self, input_text: str) -> str:
        return self.invoke({"input": input_text})["output"]

    @property
    def _default_input_key(self) -> str:
        return "input"
