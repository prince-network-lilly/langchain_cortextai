"""Tests for cortexchain.retrievers.tfidf"""

from cortexchain.retrievers.tfidf import TFIDFRetriever
from cortexchain.schema import Document


def test_basic_retrieval():
    docs = [
        Document(page_content="Python is a programming language", metadata={"id": 1}),
        Document(page_content="The sky is blue and beautiful", metadata={"id": 2}),
        Document(page_content="Machine learning uses Python extensively", metadata={"id": 3}),
    ]
    retriever = TFIDFRetriever.from_documents(docs, k=2)
    results = retriever.retrieve("Python programming")
    assert len(results) == 2
    # Python docs should rank higher
    assert any("Python" in r.page_content for r in results)


def test_empty_retriever():
    retriever = TFIDFRetriever(k=3)
    results = retriever.retrieve("anything")
    assert results == []


def test_add_documents():
    retriever = TFIDFRetriever(k=2)
    retriever.add_documents(
        [
            Document(page_content="Hello world"),
            Document(page_content="Goodbye world"),
        ]
    )
    results = retriever.retrieve("Hello")
    assert len(results) == 2
    assert results[0].page_content == "Hello world"


def test_relevance_score_in_metadata():
    docs = [Document(page_content="cats are cute"), Document(page_content="dogs are loyal")]
    retriever = TFIDFRetriever.from_documents(docs, k=2)
    results = retriever.retrieve("cute cats")
    assert "relevance_score" in results[0].metadata
    assert results[0].metadata["relevance_score"] >= results[1].metadata["relevance_score"]
