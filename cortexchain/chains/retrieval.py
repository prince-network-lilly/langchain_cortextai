from typing import Dict, List, Optional
from cortexchain.chains.base import BaseChain
from cortexchain.llm.cortex import CortexLLM
from cortexchain.prompts.templates import PromptTemplate
from cortexchain.retrievers.tfidf import TFIDFRetriever
from cortexchain.schema import Document

_RAG_TEMPLATE = """\
Use the following context to answer the question. If you cannot find the answer in the context, say so.

Context:
{context}

Question: {question}

Answer:"""


class RetrievalQAChain(BaseChain):
    """Retrieval-Augmented Generation: retrieves relevant documents, then answers using LLM."""

    def __init__(
        self,
        llm: CortexLLM,
        retriever: TFIDFRetriever,
        prompt: Optional[PromptTemplate] = None,
        k: int = 4,
        return_source_documents: bool = False,
    ):
        self.llm = llm
        self.retriever = retriever
        self.prompt = prompt or PromptTemplate.from_template(_RAG_TEMPLATE)
        self.k = k
        self.return_source_documents = return_source_documents

    def _format_docs(self, docs: List[Document]) -> str:
        return "\n\n---\n\n".join(doc.page_content for doc in docs)

    def invoke(self, inputs: Dict) -> Dict:
        question = inputs.get("question", inputs.get("input", inputs.get("query", "")))
        docs = self.retriever.retrieve(question, k=self.k)
        context = self._format_docs(docs)
        formatted_prompt = self.prompt.format(context=context, question=question)
        result = self.llm.invoke(formatted_prompt)

        output = {"answer": result.message, "_result": result}
        if self.return_source_documents:
            output["source_documents"] = docs
        return output

    def run(self, question: str) -> str:
        return self.invoke({"question": question})["answer"]

    @classmethod
    def from_llm_and_retriever(
        cls, llm: CortexLLM, retriever: TFIDFRetriever, **kwargs
    ) -> "RetrievalQAChain":
        return cls(llm=llm, retriever=retriever, **kwargs)

    @property
    def _default_input_key(self) -> str:
        return "question"
