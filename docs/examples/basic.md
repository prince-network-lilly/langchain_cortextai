# Example: Basic Usage

## Simple Question-Answer

```python
from cortexchain import CortexLLM

llm = CortexLLM(agent_name="general-assistant")
answer = llm("What are the key principles of MLOps?")
print(answer)
```

## Template-Based Generation

```python
from cortexchain import CortexLLM, LLMChain, PromptTemplate

llm = CortexLLM(agent_name="general-assistant")

# Email generator
email_prompt = PromptTemplate(
    template="Write a professional email about {topic} to {recipient}. Tone: {tone}."
)
email_chain = LLMChain(llm=llm, prompt=email_prompt)

result = email_chain.run(
    topic="project deadline extension",
    recipient="the project manager",
    tone="polite but firm"
)
print(result)
```

## Using the Prompt Hub

```python
from cortexchain import CortexLLM, LLMChain, PromptHub

llm = CortexLLM(agent_name="general-assistant")

# List available templates
print(PromptHub.list_templates())

# Use a pre-built template
summarize_prompt = PromptHub.get("summarize")
chain = LLMChain(llm=llm, prompt=summarize_prompt)
summary = chain.run(text="Very long document content here...")
```

## Output Parsing

```python
from cortexchain import CortexLLM, LLMChain, PromptTemplate, JSONOutputParser

llm = CortexLLM(agent_name="json-agent")
parser = JSONOutputParser()

prompt = PromptTemplate(
    template="Extract the person's name and age from: {text}\nRespond in JSON format."
)
chain = LLMChain(llm=llm, prompt=prompt)

raw = chain.run(text="Alice is 30 years old and lives in NYC")
parsed = parser.parse(raw)
print(parsed)  # {"name": "Alice", "age": 30, ...}
```

## Caching for Cost Reduction

```python
from cortexchain import CortexLLM, LLMCache

llm = CortexLLM(agent_name="my-agent")
cache = LLMCache(ttl_seconds=3600)

def cached_call(prompt: str) -> str:
    result = cache.get(prompt)
    if result is None:
        result = llm(prompt)
        cache.set(prompt, result)
    return result

# First call hits API, second is instant
answer1 = cached_call("What is Python?")
answer2 = cached_call("What is Python?")  # From cache
```
