# Example: RAG Pipeline

Build a Retrieval-Augmented Generation pipeline using CortexChain.

## Basic RAG

```python
from cortexchain import (
    CortexLLM, RetrievalQAChain, TFIDFRetriever,
    Document, TextLoader, RecursiveCharacterTextSplitter
)

# 1. Load documents
loader = TextLoader("knowledge_base.txt")
raw_docs = loader.load()

# 2. Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.split_documents(raw_docs)

# 3. Create retriever
retriever = TFIDFRetriever.from_documents(docs, k=3)

# 4. Build QA chain
llm = CortexLLM(agent_name="qa-agent")
qa = RetrievalQAChain(llm=llm, retriever=retriever)

# 5. Ask questions
answer = qa.run(query="What is the company policy on remote work?")
print(answer)
```

## RAG with CSV Data

```python
from cortexchain import CSVLoader, TFIDFRetriever, RetrievalQAChain, CortexLLM

# Load from CSV (each row becomes a document)
loader = CSVLoader("products.csv", content_column="description")
docs = loader.load()

retriever = TFIDFRetriever.from_documents(docs, k=5)
llm = CortexLLM(agent_name="product-qa")
qa = RetrievalQAChain(llm=llm, retriever=retriever)

answer = qa.run(query="Which products are suitable for diabetes?")
```

## RAG with Graph Workflow

```python
from cortexchain import (
    StateGraph, END, CortexLLM, TFIDFRetriever,
    Document, PromptTemplate
)

llm = CortexLLM(agent_name="rag-agent")
retriever = TFIDFRetriever.from_documents(docs, k=3)

def retrieve(state):
    query = state["query"]
    results = retriever.retrieve(query)
    return {**state, "context": "\n".join(r.page_content for r in results)}

def generate(state):
    prompt = f"Based on this context:\n{state['context']}\n\nAnswer: {state['query']}"
    answer = llm(prompt)
    return {**state, "answer": answer}

def grade(state):
    prompt = f"Is this answer relevant to the question?\nQ: {state['query']}\nA: {state['answer']}\nRespond YES or NO."
    grade = llm(prompt)
    return {**state, "grade": "pass" if "YES" in grade.upper() else "fail"}

def route_grade(state):
    return "output" if state["grade"] == "pass" else "retrieve"

# Build graph
graph = StateGraph()
graph.add_node("retrieve", retrieve)
graph.add_node("generate", generate)
graph.add_node("grade", grade)
graph.add_node("output", lambda s: s)

graph.add_edge("retrieve", "generate")
graph.add_edge("generate", "grade")
graph.add_conditional_edges("grade", route_grade, {"output": "output", "retrieve": "retrieve"})
graph.add_edge("output", END)
graph.set_entry_point("retrieve")

app = graph.compile()
result = app.invoke({"query": "What is the refund policy?"}, max_steps=6)
print(result["answer"])
```
