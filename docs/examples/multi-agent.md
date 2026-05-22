# Example: Multi-Agent Systems

## Supervisor/Worker Pattern

```python
from cortexchain import CortexLLM, SupervisorAgent, WorkerAgent, tool

# Define specialized tools
@tool
def search_papers(query: str) -> str:
    """Search academic papers."""
    return f"Found 5 papers about: {query}"

@tool
def analyze_data(dataset: str) -> str:
    """Run statistical analysis on a dataset."""
    return f"Analysis complete for {dataset}: mean=0.75, std=0.12"

@tool
def write_report(content: str) -> str:
    """Format content as a report."""
    return f"## Report\n\n{content}"

# Create workers
llm = CortexLLM(agent_name="multi-agent")

researcher = WorkerAgent(
    name="researcher",
    llm=llm,
    tools=[search_papers],
    description="Searches for and summarizes relevant papers"
)

analyst = WorkerAgent(
    name="analyst",
    llm=llm,
    tools=[analyze_data],
    description="Performs data analysis and statistical tests"
)

writer = WorkerAgent(
    name="writer",
    llm=llm,
    tools=[write_report],
    description="Writes formatted reports from findings"
)

# Create supervisor
supervisor = SupervisorAgent(
    llm=llm,
    workers=[researcher, analyst, writer],
)

# Run complex task
result = supervisor.run(
    "Research the latest advances in protein folding, analyze our internal "
    "dataset results, and produce a summary report for the team."
)
print(result)
```

## Plan-and-Execute Pattern

```python
from cortexchain import CortexLLM, PlanAndExecuteAgent, tool

@tool
def query_database(sql: str) -> str:
    """Execute a database query."""
    return "Results: 150 rows, avg_value=42.3"

@tool
def create_visualization(data: str) -> str:
    """Create a chart from data."""
    return "Chart saved to output/chart.png"

@tool
def send_slack_message(message: str) -> str:
    """Send a message to Slack."""
    return "Message sent to #data-team"

llm = CortexLLM(agent_name="planner")
agent = PlanAndExecuteAgent(
    llm=llm,
    tools=[query_database, create_visualization, send_slack_message],
    max_replans=2,
)

result = agent.run(
    "Pull last month's experiment results from the database, "
    "create a visualization of the trends, and share it with the data team on Slack."
)
# Agent will:
# 1. Plan: [query DB, create viz, send to Slack]
# 2. Execute each step
# 3. Replan if something fails
```

## Multi-Agent with Graph

```python
from cortexchain import StateGraph, END, CortexLLM

llm = CortexLLM(agent_name="workflow")

def researcher_node(state):
    findings = llm(f"Research: {state['task']}")
    return {**state, "research": findings}

def reviewer_node(state):
    review = llm(f"Review this research for accuracy:\n{state['research']}")
    return {**state, "review": review}

def route_review(state):
    if "approved" in state["review"].lower():
        return "publish"
    return "revise"

def revise_node(state):
    revised = llm(f"Revise based on feedback:\n{state['review']}\n\nOriginal:\n{state['research']}")
    return {**state, "research": revised, "revised": True}

def publish_node(state):
    return {**state, "status": "published"}

graph = StateGraph()
graph.add_node("research", researcher_node)
graph.add_node("review", reviewer_node)
graph.add_node("revise", revise_node)
graph.add_node("publish", publish_node)

graph.add_edge("research", "review")
graph.add_conditional_edges("review", route_review, {"publish": "publish", "revise": "revise"})
graph.add_edge("revise", "review")  # Re-review after revision
graph.add_edge("publish", END)
graph.set_entry_point("research")

app = graph.compile()
result = app.invoke({"task": "Summarize Q4 clinical trial results"}, max_steps=8)
```
