import re
from typing import List


class ListOutputParser:
    """Parses LLM output into a list of items (numbered or bullet-pointed)."""

    def __init__(self, separator: str = None):
        self.separator = separator

    def parse(self, text: str) -> List[str]:
        if self.separator:
            return [item.strip() for item in text.split(self.separator) if item.strip()]

        # Try numbered list: 1. item, 2. item, etc.
        numbered = re.findall(r"^\s*\d+[\.\)]\s*(.+)$", text, re.MULTILINE)
        if numbered:
            return [item.strip() for item in numbered]

        # Try bullet list: - item, * item, • item
        bullets = re.findall(r"^\s*[-*•]\s*(.+)$", text, re.MULTILINE)
        if bullets:
            return [item.strip() for item in bullets]

        # Fallback: split by newlines
        return [line.strip() for line in text.strip().split("\n") if line.strip()]

    def get_format_instructions(self) -> str:
        if self.separator:
            return f"Respond with items separated by '{self.separator}'."
        return "Respond with a numbered list (1. first item, 2. second item, ...)."

    def __repr__(self) -> str:
        return f"ListOutputParser(separator={self.separator!r})"
