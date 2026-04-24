# cortexchain

A **LangChain-style Python framework** that wraps the [Lilly Cortex AI API](https://api.cortex.lilly.com), giving you chains, memory, prompt templates, tools, and a ReAct agent — all built on top of `LIGHTClient`.

## Installation

One command — `light_client` is pulled in automatically from GitHub:

```bash
pip install git+https://github.com/YOUR_USERNAME/cortexchain.git
```

To pin a specific version/tag:

```bash
pip install git+https://github.com/YOUR_USERNAME/cortexchain.git@v0.1.0
```

---

## Quick start

```python
from cortexchain import CortexLLM

llm = CortexLLM(agent_name="your-agent-name", default_knowledge=True)
print(llm("What is the capital of France?"))
```

---

## Features

### 1. `LLMChain` — prompt template + LLM

```python
from cortexchain import CortexLLM, PromptTemplate, LLMChain

llm = CortexLLM(agent_name="your-agent")
prompt = PromptTemplate.from_template("Summarize this in one sentence: {text}")
chain = LLMChain(llm=llm, prompt=prompt)

print(chain.run(text="LangChain is a framework for LLM applications."))
```

Pipe syntax also works:

```python
chain = PromptTemplate.from_template("Translate to French: {text}") | llm
print(chain.run(text="Good morning"))
```

---

### 2. `ConversationChain` — chat with memory

```python
from cortexchain import CortexLLM, ConversationChain

llm = CortexLLM(agent_name="your-agent")
chat = ConversationChain(llm=llm, verbose=True)

chat.chat("Hi, my name is Alice.")
chat.chat("What is my name?")   # remembers "Alice"
```

Use `ConversationWindowMemory` to keep only the last *k* exchanges:

```python
from cortexchain import ConversationWindowMemory

memory = ConversationWindowMemory(k=5)
chat = ConversationChain(llm=llm, memory=memory)
```

---

### 3. `SimpleSequentialChain` — pipeline of chains

```python
from cortexchain import LLMChain, PromptTemplate, SimpleSequentialChain

step1 = LLMChain(llm=llm, prompt=PromptTemplate.from_template("Write a synopsis for: {input}"))
step2 = LLMChain(llm=llm, prompt=PromptTemplate.from_template("Give a movie title for:\n{text}"))

pipeline = SimpleSequentialChain(chains=[step1, step2], verbose=True)
print(pipeline.run("a robot who learns to paint"))
```

---

### 4. Tools + ReAct Agent

```python
from cortexchain import CortexLLM, tool, ReActAgent, AgentExecutor

llm = CortexLLM(agent_name="your-agent")

@tool
def calculator(expression: str) -> str:
    """Evaluates a mathematical expression."""
    return str(eval(expression))

@tool
def get_time(query: str) -> str:
    """Returns the current date and time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

agent = ReActAgent(llm=llm, tools=[calculator, get_time])
executor = AgentExecutor(agent=agent, tools=[calculator, get_time], verbose=True)

print(executor.run("What is 42 * 17? Also what time is it?"))
```

Custom tool class:

```python
from cortexchain import BaseTool

class MyTool(BaseTool):
    name = "my_tool"
    description = "Does something custom."

    def run(self, tool_input: str) -> str:
        return f"processed: {tool_input}"
```

---

## API reference

| Class / function | Module | Description |
|---|---|---|
| `CortexLLM` | `cortexchain.llm` | Wraps the Cortex `/model/ask` endpoint |
| `PromptTemplate` | `cortexchain.prompts` | String template with `{variable}` substitution |
| `LLMChain` | `cortexchain.chains` | Prompt + LLM chain |
| `ConversationChain` | `cortexchain.chains` | LLMChain with automatic memory |
| `SimpleSequentialChain` | `cortexchain.chains` | Pipes multiple chains in sequence |
| `ConversationBufferMemory` | `cortexchain.memory` | Full conversation history |
| `ConversationWindowMemory` | `cortexchain.memory` | Sliding-window conversation history |
| `BaseTool` | `cortexchain.tools` | Abstract base for custom tools |
| `FunctionTool` | `cortexchain.tools` | Wraps a Python function as a tool |
| `tool` | `cortexchain.tools` | Decorator: convert a function into a tool |
| `ReActAgent` | `cortexchain.agents` | Thought/Action/Observation reasoning agent |
| `AgentExecutor` | `cortexchain.agents` | Runs the agent loop and calls tools |

---

## Development

```bash
git clone https://github.com/YOUR_USERNAME/cortexchain.git
cd cortexchain
pip install -e ".[dev]"
pytest
```

## Requirements

- Python ≥ 3.9
- `light_client` — resolved automatically from [EliLillyCo/LRL_light_k8s_infra_app_client_python](https://github.com/EliLillyCo/LRL_light_k8s_infra_app_client_python) (requires Lilly GitHub access)