"""Shell command execution tool."""

import subprocess
from cortexchain.tools.base import BaseTool


class ShellTool(BaseTool):
    """Executes shell commands and returns stdout/stderr."""

    name = "shell"
    description = "Executes a shell command and returns the output. " "Input: the command to run. Use with caution."

    def __init__(self, timeout: int = 60, allowed_commands: list = None):
        self.timeout = timeout
        self.allowed_commands = allowed_commands

    def run(self, tool_input: str) -> str:
        command = tool_input.strip()
        if not command:
            return "Error: No command provided."

        if self.allowed_commands:
            first_word = command.split()[0]
            if first_word not in self.allowed_commands:
                return f"Error: Command '{first_word}' not in allowed list: " f"{self.allowed_commands}"

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]: {result.stderr}"
            if result.returncode != 0:
                output += f"\n[exit code: {result.returncode}]"
            return output if output.strip() else "(no output)"
        except subprocess.TimeoutExpired:
            return f"Error: Command timed out after {self.timeout}s"
        except Exception as e:
            return f"Error executing command: {e}"
