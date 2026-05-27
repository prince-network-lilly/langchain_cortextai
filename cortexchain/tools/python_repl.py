"""Execute Python code dynamically. Useful for data analysis, calculations, and quick experiments."""

import io
import contextlib
from cortexchain.tools.base import BaseTool


class PythonREPLTool(BaseTool):
    """Executes Python code and returns stdout. Use for calculations, data processing, etc."""

    name = "python_repl"
    description = (
        "Executes Python code and returns the output. "
        "Input should be valid Python code. "
        "Use print() to produce output."
    )

    def __init__(self, globals_dict: dict = None):
        self._globals = globals_dict or {}

    def run(self, tool_input: str) -> str:
        stdout = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout):
                exec(tool_input, self._globals)  # noqa: S102
            output = stdout.getvalue()
            return output if output else "(executed successfully, no output)"
        except Exception as e:
            return f"Error: {type(e).__name__}: {e}"
