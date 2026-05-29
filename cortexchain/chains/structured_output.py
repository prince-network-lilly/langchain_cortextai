"""StructuredOutputChain — forces LLM to return valid JSON matching a schema."""
import json
from typing import Any, Dict, List, Optional

from cortexchain.chains.base import BaseChain
from cortexchain.llm.cortex import CortexLLM
from cortexchain.output_parsers.json_parser import JSONOutputParser
from cortexchain.prompts.templates import PromptTemplate

_STRUCTURED_TEMPLATE = """\
{instruction}

{format_instructions}

Input: {input}

Respond with ONLY the JSON object (no other text):"""


class StructuredOutputChain(BaseChain):
    """Chain that forces LLM output into a specific JSON schema with auto-retry on parse failure."""

    def __init__(
        self,
        llm: CortexLLM,
        schema: Dict[str, str],
        instruction: str = "Extract information from the input.",
        max_retries: int = 2,
    ):
        self.llm = llm
        self.schema = schema
        self.instruction = instruction
        self.max_retries = max_retries
        self.parser = JSONOutputParser(schema=schema)

    def invoke(self, inputs: Dict) -> Dict:
        input_text = inputs.get("input", "")
        format_instructions = self.parser.get_format_instructions()

        prompt = _STRUCTURED_TEMPLATE.format(
            instruction=self.instruction,
            format_instructions=format_instructions,
            input=input_text,
        )

        last_error = None
        for attempt in range(self.max_retries + 1):
            response = self.llm(prompt)
            try:
                parsed = self.parser.parse(response)
                return {"output": parsed, "raw_response": response}
            except ValueError as e:
                last_error = e
                # Add error feedback to prompt for retry
                prompt += (
                    f"\n\nYour previous response was invalid: {e}\n"
                    "Please try again with ONLY valid JSON:"
                )

        return {
            "output": {},
            "raw_response": response,
            "error": str(last_error),
        }

    def run(self, input_text: str) -> Dict:
        return self.invoke({"input": input_text})["output"]

    @property
    def _default_input_key(self) -> str:
        return "input"
