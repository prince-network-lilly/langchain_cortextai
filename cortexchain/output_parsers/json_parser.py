import json
import re
from typing import Any, Dict, List, Optional


class JSONOutputParser:
    """Parses LLM output as JSON. Extracts JSON from markdown code blocks if needed."""

    def __init__(self, schema: Optional[Dict[str, str]] = None):
        self.schema = schema

    def parse(self, text: str) -> Dict[str, Any]:
        cleaned = self._extract_json(text)
        try:
            result = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Failed to parse JSON from LLM output: {e}\nOutput was:\n{text}"
            )
        if self.schema:
            self._validate(result)
        return result

    def _extract_json(self, text: str) -> str:
        # Try to find JSON in markdown code blocks
        match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        # Try to find raw JSON object or array
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    def _validate(self, data: Dict) -> None:
        for key, expected_type in self.schema.items():
            if key not in data:
                raise ValueError(f"Missing required key: {key!r}")

    def get_format_instructions(self) -> str:
        if self.schema:
            schema_str = json.dumps(
                {k: f"<{v}>" for k, v in self.schema.items()}, indent=2
            )
            return (
                "Respond with a valid JSON object using this exact schema:\n"
                f"```json\n{schema_str}\n```"
            )
        return "Respond with a valid JSON object."

    def __repr__(self) -> str:
        return f"JSONOutputParser(schema={self.schema})"
