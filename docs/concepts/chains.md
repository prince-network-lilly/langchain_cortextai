# Chains

Chains are composable pipelines that connect prompts, LLMs, and logic together.

## LLMChain

The most basic chain — combines a prompt template with an LLM:

```python
from cortexchain import CortexLLM, LLMChain, PromptTemplate

llm = CortexLLM(agent_name="my-agent")
prompt = PromptTemplate(template="Classify this text as positive or negative: {text}")
chain = LLMChain(llm=llm, prompt=prompt)

result = chain.run(text="I love this product!")
# or
result = chain.invoke({"text": "I love this product!"})
```

## ConversationChain

Automatically manages conversation memory:

```python
from cortexchain import CortexLLM, ConversationChain

chat = ConversationChain(llm=CortexLLM(agent_name="chat-agent"))
chat("Hello, I'm Alice")
chat("What's my name?")  # Remembers context
```

## SimpleSequentialChain

Pipes output from one chain to the next:

```python
from cortexchain import SimpleSequentialChain, LLMChain, PromptTemplate, CortexLLM

llm = CortexLLM(agent_name="my-agent")

chain1 = LLMChain(llm=llm, prompt=PromptTemplate(template="Summarize: {input}"))
chain2 = LLMChain(llm=llm, prompt=PromptTemplate(template="Translate to French: {input}"))

pipeline = SimpleSequentialChain(chains=[chain1, chain2])
result = pipeline({"input": "Long document..."})
```

## RouterChain

Routes input to different chains based on LLM classification:

```python
from cortexchain import RouterChain, LLMChain, PromptTemplate, CortexLLM

llm = CortexLLM(agent_name="my-agent")

destinations = {
    "technical": LLMChain(llm=llm, prompt=PromptTemplate(template="Technical answer: {input}")),
    "simple": LLMChain(llm=llm, prompt=PromptTemplate(template="Simple answer: {input}")),
}

router = RouterChain(llm=llm, destinations=destinations)
result = router({"input": "Explain quantum computing"})
```

## RetrievalQAChain (RAG)

Retrieval-Augmented Generation:

```python
from cortexchain import RetrievalQAChain, TFIDFRetriever, CortexLLM, Document

docs = [Document(page_content="..."), ...]
retriever = TFIDFRetriever.from_documents(docs, k=3)
llm = CortexLLM(agent_name="my-agent")

qa = RetrievalQAChain(llm=llm, retriever=retriever)
answer = qa.run(query="What is X?")
```

## StructuredOutputChain

Forces the LLM to output valid JSON matching a schema:

```python
from cortexchain import StructuredOutputChain, CortexLLM, PromptTemplate

chain = StructuredOutputChain(
    llm=CortexLLM(agent_name="my-agent"),
    prompt=PromptTemplate(template="Extract entities from: {text}"),
    schema={"name": str, "age": int, "city": str},
)
result = chain.invoke({"text": "Alice is 30 and lives in NYC"})
# result["parsed"] == {"name": "Alice", "age": 30, "city": "NYC"}
```

## MapReduceChain

Process large documents by splitting, mapping, then reducing:

```python
from cortexchain import MapReduceChain, CortexLLM

chain = MapReduceChain(llm=CortexLLM(agent_name="my-agent"))
summary = chain.run(documents=[...])
```

## Input Validation

Add validation to any chain:

```python
from cortexchain import InputValidator, LLMChain

validator = InputValidator()
validator.require("query").type_check({"query": str}).max_length("query", 5000)

chain = LLMChain(llm=llm, prompt=prompt)
validator.wrap(chain)  # Now chain.invoke() validates first
```
