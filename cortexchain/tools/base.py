from abc import ABC, abstractmethod
from typing import Callable, Optional


class BaseTool(ABC):
    """Abstract base class for all tools."""

    name: str = ""
    description: str = ""

    @abstractmethod
    def run(self, tool_input: str) -> str:
        pass

    def __call__(self, tool_input: str) -> str:
        return self.run(tool_input)

    def __repr__(self) -> str:
        return f"Tool(name={self.name!r})"


class FunctionTool(BaseTool):
    """Wraps a plain Python function as a tool."""

    def __init__(self, func: Callable, name: str, description: str):
        self.func = func
        self.name = name
        self.description = description

    def run(self, tool_input: str) -> str:
        try:
            result = self.func(tool_input)
            return str(result)
        except Exception as e:
            return f"Tool error ({self.name}): {e}"


def tool(_func: Optional[Callable] = None, *, name: str = None, description: str = None):
    """Decorator that converts a function into a FunctionTool.

    Usage:
        @tool
        def my_tool(input: str) -> str: ...

        @tool(name="my_tool", description="Does something useful")
        def my_tool(input: str) -> str: ...
    """
    def decorator(func: Callable) -> FunctionTool:
        _name = name or func.__name__
        _desc = description or (func.__doc__ or f"Useful tool: {_name}").strip()
        return FunctionTool(func=func, name=_name, description=_desc)

    if _func is not None:
        # Called as @tool (no parentheses)
        return decorator(_func)
    return decorator
