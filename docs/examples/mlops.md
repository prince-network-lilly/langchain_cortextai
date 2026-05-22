# Example: MLOps Workflows

## Data Validation Pipeline

```python
from cortexchain import (
    StateGraph, END, CortexLLM,
    DataValidationTool, ExperimentTrackerTool, PipelineMonitorTool
)

llm = CortexLLM(agent_name="mlops-agent")
validator = DataValidationTool()
tracker = ExperimentTrackerTool()
monitor = PipelineMonitorTool()

def validate_data(state):
    result = validator.run(f"validate|{state['schema']}|{state['data_path']}")
    passed = "PASSED" in result.upper()
    return {**state, "validation_result": result, "data_valid": passed}

def log_experiment(state):
    tracker.run(f"log|{state['experiment_name']}|accuracy={state['metrics']['accuracy']}")
    return {**state, "logged": True}

def check_pipeline(state):
    status = monitor.run(f"status|{state['pipeline_name']}")
    return {**state, "pipeline_status": status}

def route_validation(state):
    return "train" if state["data_valid"] else "alert"

def train_model(state):
    response = llm(f"Generate training config for: {state['model_type']}")
    return {**state, "training_config": response, "status": "training"}

def send_alert(state):
    return {**state, "status": "data_validation_failed", "alert_sent": True}

# Build pipeline graph
graph = StateGraph()
graph.add_node("validate", validate_data)
graph.add_node("train", train_model)
graph.add_node("alert", send_alert)
graph.add_node("log", log_experiment)

graph.add_conditional_edges("validate", route_validation, {"train": "train", "alert": "alert"})
graph.add_edge("train", "log")
graph.add_edge("log", END)
graph.add_edge("alert", END)
graph.set_entry_point("validate")

app = graph.compile()
result = app.invoke({
    "schema": '{"columns": ["feature1", "feature2", "target"]}',
    "data_path": "data/train.csv",
    "experiment_name": "exp_042",
    "pipeline_name": "training_pipeline",
    "model_type": "gradient_boosting",
    "metrics": {"accuracy": 0.94},
})
```

## Experiment Comparison with Agent

```python
from cortexchain import CortexLLM, ReActAgent, AgentExecutor, ExperimentTrackerTool

llm = CortexLLM(agent_name="mlops-agent")
tracker = ExperimentTrackerTool()

agent = ReActAgent(llm=llm, tools=[tracker])
executor = AgentExecutor(agent=agent, tools=[tracker], max_iterations=5)

result = executor.run(
    "Compare my last 3 experiments and tell me which had the best F1 score. "
    "Also show me the hyperparameters used in the best one."
)
print(result)
```

## API Health Monitoring

```python
from cortexchain import APIHealthCheckTool, CortexLLM, LLMChain, PromptTemplate

health_checker = APIHealthCheckTool(endpoints=[
    "https://api.cortex.lilly.com/health",
    "https://mlflow.internal.lilly.com/health",
    "https://data-api.lilly.com/v1/status",
])

# Check all endpoints
status = health_checker.run("check_all")
print(status)

# Use LLM to analyze and recommend
llm = CortexLLM(agent_name="ops-agent")
prompt = PromptTemplate(
    template="Analyze these API health results and recommend actions:\n{health_status}"
)
chain = LLMChain(llm=llm, prompt=prompt)
recommendation = chain.run(health_status=status)
print(recommendation)
```

## Batch Processing with Rate Limiting

```python
from cortexchain import CortexLLM, BatchProcessor, RateLimiter, LLMChain, PromptTemplate

llm = CortexLLM(agent_name="batch-agent")
prompt = PromptTemplate(template="Classify this feedback as positive/negative/neutral: {input}")
chain = LLMChain(llm=llm, prompt=prompt)

# Process 100 items with rate limiting
processor = BatchProcessor(
    chain_or_fn=chain.invoke,
    max_workers=4,
    on_error="continue",
)

feedbacks = ["Great product!", "Terrible experience", "It's okay", ...]
results = processor.run(feedbacks)

print(results.summary())
print(f"Success rate: {results.success_rate:.1%}")
print(f"Failures: {len(results.failures)}")
```

## MLOps Toolkit — All-in-One

```python
from cortexchain import MLOpsToolkit, CortexLLM, AgentExecutor, ReActAgent

# Get all MLOps tools at once
toolkit = MLOpsToolkit()
tools = toolkit.get_tools()
# Returns: [DataValidationTool, ExperimentTrackerTool, PipelineMonitorTool, APIHealthCheckTool]

# Create an MLOps agent with all tools
llm = CortexLLM(agent_name="mlops")
agent = ReActAgent(llm=llm, tools=tools)
executor = AgentExecutor(agent=agent, tools=tools)

result = executor.run(
    "Check if the training pipeline is healthy, validate the latest dataset, "
    "and compare the last 2 experiment results."
)
```
