# LLM

The `CortexLLM` class is the foundation of CortexChain. It wraps the Cortex `/model/ask` API.

## Basic Usage

```python
from cortexchain import CortexLLM

llm = CortexLLM(agent_name="my-agent")

# Simple call (returns string)
text = llm("What is Python?")

# Full call (returns LLMResult with metadata)
result = llm.invoke("What is Python?")
print(result.message)
print(result.llm_model)
print(result.source_metadata)
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `agent_name` | str | required | The Cortex agent to call |
| `base_url` | str | `https://api.cortex.lilly.com` | API base URL |
| `default_knowledge` | bool | `False` | Enable default knowledge base |

## Chat History

Pass previous conversation context for multi-turn interactions:

```python
result = llm.invoke(
    "What was my first question?",
    chat_history="Human: What is Python?\nAI: Python is a programming language."
)
```

## Async Support

```python
from cortexchain import AsyncCortexLLM

llm = AsyncCortexLLM(agent_name="my-agent", max_workers=4)

# Single call
result = await llm.ainvoke("Hello")

# Batch (parallel)
results = await llm.abatch(["prompt1", "prompt2", "prompt3"])
```

## With Rate Limiting

```python
from cortexchain import CortexLLM, RateLimitedLLM

base_llm = CortexLLM(agent_name="my-agent")
llm = RateLimitedLLM(llm=base_llm, max_calls=10, period=60)
```

## With Caching

```python
from cortexchain import CortexLLM, LLMCache

llm = CortexLLM(agent_name="my-agent")
cache = LLMCache(ttl_seconds=3600)

# Manual cache usage
cached = cache.get("my prompt")
if cached is None:
    result = llm("my prompt")
    cache.set("my prompt", result)
```
