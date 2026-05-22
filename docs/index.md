# CortexChain

**LangChain-style framework for the Lilly Cortex AI API.**

CortexChain provides a production-ready framework for building AI-powered applications
using Eli Lilly's internal Cortex AI platform. It follows LangChain/LangGraph patterns
so teams familiar with those ecosystems can be productive immediately.

## Key Features

- **LLM Wrapper** — Simple interface to the Cortex `/model/ask` API
- **Chains** — Composable pipelines (LLM, Sequential, Router, RAG, MapReduce)
- **Tools & Agents** — ReAct, Supervisor/Worker, Plan-and-Execute patterns
- **Graph Engine** — LangGraph-style state machines with conditional edges
- **MLOps Tools** — Data validation, experiment tracking, pipeline monitoring
- **Production Ready** — Rate limiting, caching, retries, async, validation

## Quick Example

```python
from cortexchain import CortexLLM, LLMChain, PromptTemplate

llm = CortexLLM(agent_name="my-cortex-agent")
prompt = PromptTemplate(template="Summarize this: {text}")
chain = LLMChain(llm=llm, prompt=prompt)

result = chain.run(text="Long document content here...")
print(result)
```

## Installation

```bash
pip install git+https://github.com/prince-network-lilly/langchain_cortextai.git
```

## Next Steps

- [Installation Guide](getting-started/installation.md)
- [Quick Start Tutorial](getting-started/quickstart.md)
- [API Reference](api/schema.md)
