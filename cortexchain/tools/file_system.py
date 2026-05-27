"""File system tools for reading, writing, and listing files."""

import os
import json
from cortexchain.tools.base import BaseTool


class ReadFileTool(BaseTool):
    """Reads file contents. Input: file path."""

    name = "read_file"
    description = "Reads and returns the contents of a file. Input: file path."

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir

    def _resolve_path(self, path: str) -> str:
        if self.base_dir:
            return os.path.join(self.base_dir, path)
        return path

    def run(self, tool_input: str) -> str:
        path = self._resolve_path(tool_input.strip())
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            return f"Error: File not found: {path}"
        except Exception as e:
            return f"Error reading file: {e}"


class WriteFileTool(BaseTool):
    """Writes content to a file. Input: JSON with 'path' and 'content'."""

    name = "write_file"
    description = 'Writes content to a file. Input: JSON {"path": "...", "content": "..."}'

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir

    def _resolve_path(self, path: str) -> str:
        if self.base_dir:
            return os.path.join(self.base_dir, path)
        return path

    def run(self, tool_input: str) -> str:
        try:
            params = json.loads(tool_input)
            path = self._resolve_path(params["path"])
            content = params["content"]
        except (json.JSONDecodeError, KeyError):
            return 'Error: Input must be JSON with "path" and "content" keys.'

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Successfully wrote {len(content)} chars to {path}"
        except Exception as e:
            return f"Error writing file: {e}"


class ListDirectoryTool(BaseTool):
    """Lists files in a directory. Input: directory path."""

    name = "list_directory"
    description = "Lists files and folders in a directory. Input: directory path."

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir

    def _resolve_path(self, path: str) -> str:
        if self.base_dir:
            return os.path.join(self.base_dir, path)
        return path

    def run(self, tool_input: str) -> str:
        path = self._resolve_path(tool_input.strip() or ".")
        try:
            entries = os.listdir(path)
            result = []
            for entry in sorted(entries):
                full = os.path.join(path, entry)
                prefix = "[DIR]" if os.path.isdir(full) else "[FILE]"
                result.append(f"{prefix} {entry}")
            return "\n".join(result) if result else "(empty directory)"
        except FileNotFoundError:
            return f"Error: Directory not found: {path}"
        except Exception as e:
            return f"Error listing directory: {e}"
