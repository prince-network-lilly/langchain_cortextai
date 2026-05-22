# Tools & Agents

Agents use LLMs to decide which tools to call and in what order.

## Defining Tools

### Using the @tool Decorator

```python
from cortexchain import tool

@tool
def search_database(query: str) -> str:
    """Search the internal database for records."""
    # Your implementation
    return f"Found 3 records matching: {query}"

@tool(name="calculator", description="Evaluate math expressions")
def calc(expression: str) -> str:
    return str(eval(expression))
```

### Using BaseTool

```python
from cortexchain import BaseTool

class WeatherTool(BaseTool):
    name = "weather"
    description = "Get current weather for a city"

    def run(self, tool_input: str) -> str:
        return f"Weather in {tool_input}: 72°F, sunny"
```

## Built-in Tools

| Tool | Description |
|------|-------------|
| `PythonREPLTool` | Execute Python code |
| `HTTPRequestTool` | Make HTTP requests (with domain whitelist) |
| `ReadFileTool` | Read file contents |
| `WriteFileTool` | Write to files |
| `ListDirectoryTool` | List directory contents |
| `SQLDatabaseTool` | Query databases (read-only mode) |
| `ShellTool` | Run shell commands (with whitelist) |
| `DataValidationTool` | Validate data schemas |
| `ExperimentTrackerTool` | Track ML experiments |
| `PipelineMonitorTool` | Monitor data pipelines |
| `APIHealthCheckTool` | Check API endpoint health |

## ReAct Agent

The ReAct pattern: Thought → Action → Observation loop.

```python
from cortexchain import CortexLLM, ReActAgent, AgentExecutor, tool

@tool
def lookup(query: str) -> str:
    """Look up information."""
    return "Result for: " + query

llm = CortexLLM(agent_name="agent")
agent = ReActAgent(llm=llm, tools=[lookup])
executor = AgentExecutor(agent=agent, tools=[lookup], max_iterations=5)

result = executor.run("Find information about X")
```

## Supervisor Agent (Multi-Agent)

Orchestrate multiple specialized workers:

```python
from cortexchain import CortexLLM, SupervisorAgent, WorkerAgent

llm = CortexLLM(agent_name="supervisor")

researcher = WorkerAgent(name="researcher", llm=llm, tools=[search_tool])
writer = WorkerAgent(name="writer", llm=llm, tools=[])

supervisor = SupervisorAgent(
    llm=llm,
    workers=[researcher, writer],
)

result = supervisor.run("Research and write a report about AI in pharma")
```

## Plan-and-Execute Agent

Decomposes complex tasks into steps:

```python
from cortexchain import CortexLLM, PlanAndExecuteAgent

llm = CortexLLM(agent_name="planner")
agent = PlanAndExecuteAgent(llm=llm, tools=[...])

result = agent.run("Analyze our Q4 data and generate a summary report")
# Agent will: 1) Plan steps, 2) Execute each, 3) Replan if needed
```

## Toolkits

Pre-built collections of related tools:

```python
from cortexchain import MLOpsToolkit, DataToolkit, DevToolkit, APIToolkit

# MLOps: data validation + experiment tracking + pipeline monitoring
mlops_tools = MLOpsToolkit().get_tools()

# Data: file read/write + SQL + HTTP
data_tools = DataToolkit().get_tools()

# Dev: Python REPL + shell + file system
dev_tools = DevToolkit().get_tools()

# API: HTTP requests + health checks
api_tools = APIToolkit().get_tools()
```
