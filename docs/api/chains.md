# API Reference: Chains

## BaseChain (abstract)

```python
class BaseChain(ABC):
    def invoke(self, inputs: Dict) -> Dict  # abstract
    def __call__(self, inputs: Union[Dict, str]) -> Dict
```

## LLMChain

```python
class LLMChain(BaseChain):
    def __init__(self, llm: CortexLLM, prompt: PromptTemplate, output_key: str = "text")
    def invoke(self, inputs: Dict) -> Dict
    def run(self, **kwargs) -> str
```

## ConversationChain

```python
class ConversationChain(BaseChain):
    def __init__(self, llm: CortexLLM, memory=None, prompt=None)
    def invoke(self, inputs: Dict) -> Dict
```

## SimpleSequentialChain

```python
class SimpleSequentialChain(BaseChain):
    def __init__(self, chains: List[BaseChain])
    def invoke(self, inputs: Dict) -> Dict
```

## RouterChain

```python
class RouterChain(BaseChain):
    def __init__(self, llm: CortexLLM, destinations: Dict[str, BaseChain], default_chain=None)
    def invoke(self, inputs: Dict) -> Dict
```

## RetrievalQAChain

```python
class RetrievalQAChain(BaseChain):
    def __init__(self, llm: CortexLLM, retriever, prompt=None)
    def invoke(self, inputs: Dict) -> Dict
    def run(self, query: str) -> str
```

## StructuredOutputChain

```python
class StructuredOutputChain(BaseChain):
    def __init__(self, llm: CortexLLM, prompt: PromptTemplate, schema: dict, max_retries: int = 2)
    def invoke(self, inputs: Dict) -> Dict  # Returns {"parsed": dict, "raw": str}
```

## MapReduceChain

```python
class MapReduceChain(BaseChain):
    def __init__(self, llm: CortexLLM, map_prompt=None, reduce_prompt=None)
    def invoke(self, inputs: Dict) -> Dict
    def run(self, documents: List[Document]) -> str
```

## RefineChain

```python
class RefineChain(BaseChain):
    def __init__(self, llm: CortexLLM, initial_prompt=None, refine_prompt=None)
    def invoke(self, inputs: Dict) -> Dict
```

## AsyncLLMChain

```python
class AsyncLLMChain:
    def __init__(self, llm: AsyncCortexLLM, prompt: PromptTemplate, output_key: str = "text")
    async def ainvoke(self, inputs: Dict) -> Dict
    async def arun(self, **kwargs) -> str
    async def abatch(self, inputs_list: list, max_concurrency: int = 4) -> list
```

## AsyncSequentialChain

```python
class AsyncSequentialChain:
    def __init__(self, chains: list, input_key: str = "input", output_key: str = "output")
    async def ainvoke(self, inputs: Dict) -> Dict
```
