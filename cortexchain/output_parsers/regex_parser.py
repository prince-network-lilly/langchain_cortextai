import re
from typing import Dict, Optional


class RegexParser:
    """Parses LLM output using a regex pattern with named capture groups."""

    def __init__(self, pattern: str, output_keys: Optional[list] = None):
        self.pattern = pattern
        self._regex = re.compile(pattern, re.DOTALL)
        self.output_keys = output_keys

    def parse(self, text: str) -> Dict[str, str]:
        match = self._regex.search(text)
        if not match:
            raise ValueError(
                f"Could not parse output with pattern {self.pattern!r}.\nOutput was:\n{text}"
            )
        result = match.groupdict()
        if not result:
            # Fall back to numbered groups
            groups = match.groups()
            if self.output_keys and len(groups) == len(self.output_keys):
                result = dict(zip(self.output_keys, groups))
            else:
                result = {f"group_{i}": g for i, g in enumerate(groups)}
        return {k: v.strip() if v else "" for k, v in result.items()}

    def get_format_instructions(self) -> str:
        keys = self.output_keys or list(self._regex.groupindex.keys())
        if keys:
            return f"Your response must contain these fields: {', '.join(keys)}"
        return "Respond in the expected format."

    def __repr__(self) -> str:
        return f"RegexParser(pattern={self.pattern!r})"
