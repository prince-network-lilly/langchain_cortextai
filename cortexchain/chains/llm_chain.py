from typing import Dict
from cortexchain.chains.base import BaseChain
from cortexchain.llm.cortex import CortexLLM
from cortexchain.prompts.templates import PromptTemplate


class LLMChain(BaseChain):
    """Combines a PromptTemplate with a CortexLLM to produce text."""

    def __init__(self, llm: CortexLLM, prompt: PromptTemplate, output_key: str = "text"):
        self.llm = llm
        self.prompt = prompt
        self.output_key = output_key

    def invoke(self, inputs: Dict) -> Dict:
        formatted = self.prompt.format(**inputs)
        result = self.llm.invoke(formatted)
        return {self.output_key: result.message, "_result": result}

    def run(self, **kwargs) -> str:
        return self.invoke(kwargs)[self.output_key]

    @property
    def _default_input_key(self) -> str:
        non_history = [k for k in self.prompt.input_variables if k != "chat_history"]
        return non_history[0] if non_history else "input"

    def __repr__(self) -> str:
        return f"LLMChain(llm={self.llm!r}, output_key={self.output_key!r})"
