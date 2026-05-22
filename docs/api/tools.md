# API Reference: Tools

## BaseTool (abstract)

```python
class BaseTool(ABC):
    name: str
    description: str
    def run(self, tool_input: str) -> str  # abstract
    def __call__(self, tool_input: str) -> str
```

## FunctionTool

```python
class FunctionTool(BaseTool):
    def __init__(self, func: Callable, name: str, description: str)
    def run(self, tool_input: str) -> str
```

## @tool Decorator

```python
@tool
def my_tool(input: str) -> str: ...

@tool(name="custom_name", description="Custom description")
def my_tool(input: str) -> str: ...
```

## Built-in Tools

### PythonREPLTool
```python
class PythonREPLTool(BaseTool):
    name = "python_repl"
    def run(self, code: str) -> str
```

### HTTPRequestTool
```python
class HTTPRequestTool(BaseTool):
    def __init__(self, allowed_domains: List[str] = None)
    def run(self, tool_input: str) -> str  # Input: "METHOD url [body]"
```

### ReadFileTool / WriteFileTool / ListDirectoryTool
```python
class ReadFileTool(BaseTool):
    def run(self, file_path: str) -> str

class WriteFileTool(BaseTool):
    def run(self, tool_input: str) -> str  # Input: "path|content"

class ListDirectoryTool(BaseTool):
    def run(self, directory: str) -> str
```

### SQLDatabaseTool
```python
class SQLDatabaseTool(BaseTool):
    def __init__(self, connection_string: str, read_only: bool = True)
    def run(self, query: str) -> str
```

### ShellTool
```python
class ShellTool(BaseTool):
    def __init__(self, allowed_commands: List[str] = None)
    def run(self, command: str) -> str
```

## MLOps Tools

### DataValidationTool
```python
class DataValidationTool(BaseTool):
    name = "data_validation"
    def run(self, tool_input: str) -> str  # Input: "validate|schema|data"
```

### ExperimentTrackerTool
```python
class ExperimentTrackerTool(BaseTool):
    name = "experiment_tracker"
    def run(self, tool_input: str) -> str  # Actions: log, compare, best
```

### PipelineMonitorTool
```python
class PipelineMonitorTool(BaseTool):
    name = "pipeline_monitor"
    def run(self, tool_input: str) -> str  # Actions: status, health, alerts
```

### APIHealthCheckTool
```python
class APIHealthCheckTool(BaseTool):
    def __init__(self, endpoints: List[str] = None)
    def run(self, tool_input: str) -> str
```

## Toolkits

```python
class MLOpsToolkit:
    def get_tools(self) -> List[BaseTool]

class DataToolkit:
    def get_tools(self) -> List[BaseTool]

class DevToolkit:
    def get_tools(self) -> List[BaseTool]

class APIToolkit:
    def get_tools(self) -> List[BaseTool]
```
