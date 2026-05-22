# Graph (StateGraph)

CortexChain includes a LangGraph-style state machine engine for complex workflows with branching, loops, and checkpointing.

## Basic Graph

```python
from cortexchain import StateGraph, END

graph = StateGraph()

# Define nodes (functions that transform state)
graph.add_node("step1", lambda state: {**state, "step1_done": True})
graph.add_node("step2", lambda state: {**state, "step2_done": True})

# Define edges
graph.add_edge("step1", "step2")
graph.add_edge("step2", END)

# Set entry point
graph.set_entry_point("step1")

# Compile and run
app = graph.compile()
result = app.invoke({"input": "hello"})
```

## Conditional Edges

Route to different nodes based on state:

```python
from cortexchain import StateGraph, END

def router(state):
    if state.get("score", 0) > 0.8:
        return "approve"
    return "review"

graph = StateGraph()
graph.add_node("evaluate", lambda s: {**s, "score": 0.9})
graph.add_node("approve", lambda s: {**s, "decision": "approved"})
graph.add_node("review", lambda s: {**s, "decision": "needs review"})

graph.add_conditional_edges("evaluate", router, {
    "approve": "approve",
    "review": "review",
})
graph.add_edge("approve", END)
graph.add_edge("review", END)
graph.set_entry_point("evaluate")

app = graph.compile()
result = app.invoke({})
# result["decision"] == "approved"
```

## Streaming

Get step-by-step execution events:

```python
app = graph.compile()
for event in app.stream({"input": "data"}):
    print(f"Node: {event['node']}, State: {event['state']}")
```

## Checkpointing

Save and resume graph state:

```python
from cortexchain import StateGraph, END, MemoryCheckpointer, FileCheckpointer

# In-memory (for development)
checkpointer = MemoryCheckpointer()

# File-based (for production)
checkpointer = FileCheckpointer(directory="./checkpoints")

app = graph.compile(checkpointer=checkpointer)
app.invoke({"input": "data"}, config={"thread_id": "user-123"})

# Later: load saved state
saved = checkpointer.load("user-123")
```

## Human-in-the-Loop

Pause execution for human approval:

```python
from cortexchain import StateGraph, END, HumanApprovalNode, require_approval

# Method 1: HumanApprovalNode
graph.add_node("dangerous_action", HumanApprovalNode(
    action_fn=lambda s: {**s, "executed": True},
    prompt="Execute dangerous action? (y/n): ",
))

# Method 2: @require_approval decorator
@require_approval(prompt="Approve this step?")
def risky_step(state):
    return {**state, "done": True}
```

## Subgraphs & Parallel Execution

```python
from cortexchain import SubgraphNode, ParallelNode

# Nest a graph inside another
sub = StateGraph()
# ... define sub-graph ...
graph.add_node("sub_process", SubgraphNode(sub.compile()))

# Run nodes in parallel
graph.add_node("parallel", ParallelNode(
    nodes={"fetch_a": fetch_fn_a, "fetch_b": fetch_fn_b}
))
```

## Max Steps Guard

Prevent infinite loops:

```python
app = graph.compile()
result = app.invoke({}, max_steps=10)  # Stops after 10 node executions
```

## Visualization

```python
from cortexchain import visualize_graph, print_graph

# ASCII visualization
print_graph(graph)

# Mermaid diagram (for docs)
mermaid_str = visualize_graph(graph)
```
