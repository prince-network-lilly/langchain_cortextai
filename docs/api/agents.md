# API Reference: Agents

## ReActAgent

```python
class ReActAgent:
    def __init__(self, llm: CortexLLM, tools: List[BaseTool], prompt: str = None)
    def plan(self, inputs: Dict, intermediate_steps: List) -> Union[AgentAction, AgentFinish]
```

## AgentExecutor

```python
class AgentExecutor:
    def __init__(self, agent: ReActAgent, tools: List[BaseTool], max_iterations: int = 10, verbose: bool = False)
    def run(self, input: str) -> str
    def invoke(self, inputs: Dict) -> Dict
```

## SupervisorAgent

```python
class SupervisorAgent:
    def __init__(self, llm: CortexLLM, workers: List[WorkerAgent])
    def run(self, task: str) -> str
```

## WorkerAgent

```python
class WorkerAgent:
    def __init__(self, name: str, llm: CortexLLM, tools: List[BaseTool] = None, description: str = "")
    def run(self, task: str) -> str
```

## PlanAndExecuteAgent

```python
class PlanAndExecuteAgent:
    def __init__(self, llm: CortexLLM, tools: List[BaseTool] = None, max_replans: int = 2)
    def run(self, task: str) -> str
    def plan(self, task: str) -> List[str]
    def execute_step(self, step: str, context: Dict) -> str
```
