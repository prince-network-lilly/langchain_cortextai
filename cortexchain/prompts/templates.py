import re
from typing import List, Optional


class PromptTemplate:
    """A string template with {variable} placeholders."""

    def __init__(self, template: str, input_variables: Optional[List[str]] = None):
        self.template = template
        self.input_variables = input_variables or list(
            dict.fromkeys(re.findall(r"\{(\w+)\}", template))
        )

    def format(self, **kwargs) -> str:
        return self.template.format(**kwargs)

    @classmethod
    def from_template(cls, template: str) -> "PromptTemplate":
        return cls(template=template)

    def __or__(self, llm):
        """Support pipe syntax: prompt | llm  ->  LLMChain."""
        from cortexchain.chains.llm_chain import LLMChain
        return LLMChain(llm=llm, prompt=self)

    def __repr__(self) -> str:
        return f"PromptTemplate(input_variables={self.input_variables!r})"
