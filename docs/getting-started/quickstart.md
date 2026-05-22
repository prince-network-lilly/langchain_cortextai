# Quick Start

This guide walks you through the core patterns in CortexChain.

## 1. Basic LLM Call

```python
from cortexchain import CortexLLM

llm = CortexLLM(agent_name="my-agent")
response = llm("What is machine learning?")
print(response)
```

## 2. Prompt Templates

```python
from cortexchain import PromptTemplate, LLMChain, CortexLLM

llm = CortexLLM(agent_name="my-agent")
prompt = PromptTemplate(template="Explain {topic} in simple terms for a {audience}.")

chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(topic="neural networks", audience="5-year-old")
print(result)
```

## 3. Conversation with Memory

```python
from cortexchain import CortexLLM, ConversationChain

llm = CortexLLM(agent_name="my-agent")
chat = ConversationChain(llm=llm)

print(chat("Hi, my name is Alice")["text"])
print(chat("What's my name?")["text"])  # Remembers "Alice"
```

## 4. Sequential Chains

```python
from cortexchain import CortexLLM, LLMChain, SimpleSequentialChain, PromptTemplate

llm = CortexLLM(agent_name="my-agent")

summarize = LLMChain(
    llm=llm,
    prompt=PromptTemplate(template="Summarize: {input}"),
)
translate = LLMChain(
    llm=llm,
    prompt=PromptTemplate(template="Translate to Spanish: {input}"),
)

pipeline = SimpleSequentialChain(chains=[summarize, translate])
result = pipeline({"input": "Long English document..."})
print(result["text"])
```

## 5. Tools & Agents

```python
from cortexchain import CortexLLM, ReActAgent, AgentExecutor, tool

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression."""
    return str(eval(expression))

llm = CortexLLM(agent_name="my-agent")
agent = ReActAgent(llm=llm, tools=[calculator])
executor = AgentExecutor(agent=agent, tools=[calculator])

result = executor.run("What is 15 * 23 + 7?")
print(result)
```

## 6. Graph Workflows

```python
from cortexchain import StateGraph, END

graph = StateGraph()
graph.add_node("fetch", lambda s: {**s, "data": "fetched"})
graph.add_node("process", lambda s: {**s, "result": s["data"].upper()})
graph.add_edge("fetch", "process")
graph.add_edge("process", END)
graph.set_entry_point("fetch")

app = graph.compile()
result = app.invoke({"input": "go"})
print(result["result"])  # "FETCHED"
```

## 7. Async Support

```python
import asyncio
from cortexchain import AsyncCortexLLM, AsyncLLMChain, PromptTemplate

async def main():
    llm = AsyncCortexLLM(agent_name="my-agent")
    prompt = PromptTemplate(template="Analyze: {text}")
    chain = AsyncLLMChain(llm=llm, prompt=prompt)

    # Single call
    result = await chain.ainvoke({"text": "Some data"})
    print(result["text"])

    # Batch (parallel)
    results = await chain.abatch([
        {"text": "Data 1"},
        {"text": "Data 2"},
        {"text": "Data 3"},
    ])
    for r in results:
        print(r["text"])

asyncio.run(main())
```

## Next Steps

- [Configuration](configuration.md) — Environment variables and settings
- [Chains](../concepts/chains.md) — All chain types explained
- [Agents](../concepts/agents.md) — Agent patterns in depth
- [Graph](../concepts/graph.md) — State machine workflows
