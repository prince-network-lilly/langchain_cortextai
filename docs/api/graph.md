# API Reference: Graph

## StateGraph

```python
class StateGraph:
    def add_node(self, name: str, fn: Callable[[Dict], Dict]) -> None
    def add_edge(self, source: str, target: str) -> None
    def add_conditional_edges(self, source: str, router: Callable, mapping: Dict[str, str]) -> None
    def set_entry_point(self, name: str) -> None
    def compile(self, checkpointer=None) -> CompiledGraph
```

## CompiledGraph

```python
class CompiledGraph:
    def invoke(self, inputs: Dict, config: Dict = None, max_steps: int = 50) -> Dict
    def stream(self, inputs: Dict) -> Iterator[Dict]  # Yields {"node": str, "state": Dict}
```

## END

```python
END = "__end__"  # Sentinel for terminal edges
```

## Checkpointers

### MemoryCheckpointer

```python
class MemoryCheckpointer:
    def save(self, thread_id: str, state: Dict, node: str) -> None
    def load(self, thread_id: str) -> Optional[Dict]
    def list_threads(self) -> List[str]
    def delete(self, thread_id: str) -> None
```

### FileCheckpointer

```python
class FileCheckpointer:
    def __init__(self, directory: str = "./checkpoints")
    def save(self, thread_id: str, state: Dict, node: str) -> None
    def load(self, thread_id: str) -> Optional[Dict]
```

## Human-in-the-Loop

### HumanApprovalNode

```python
class HumanApprovalNode:
    def __init__(self, action_fn: Callable, prompt: str = "Approve? (y/n): ")
    def __call__(self, state: Dict) -> Dict
```

### InterruptibleGraph

```python
class InterruptibleGraph:
    def __init__(self, graph: CompiledGraph, interrupt_before: List[str] = None)
    def invoke(self, inputs: Dict, approve_fn: Callable = None) -> Dict
```

### @require_approval

```python
@require_approval(prompt="Approve this step?")
def my_node(state: Dict) -> Dict: ...
```

## Subgraphs

### SubgraphNode

```python
class SubgraphNode:
    def __init__(self, compiled_graph: CompiledGraph, input_mapping: Dict = None, output_mapping: Dict = None)
    def __call__(self, state: Dict) -> Dict
```

### ParallelNode / ParallelThreadedNode

```python
class ParallelNode:
    def __init__(self, nodes: Dict[str, Callable])
    def __call__(self, state: Dict) -> Dict  # Runs nodes sequentially, merges results

class ParallelThreadedNode:
    def __init__(self, nodes: Dict[str, Callable], max_workers: int = 4)
    def __call__(self, state: Dict) -> Dict  # Runs nodes in threads
```

## Visualization

```python
def visualize_graph(graph: StateGraph) -> str  # Returns Mermaid diagram
def print_graph(graph: StateGraph) -> None     # Prints ASCII representation
```
