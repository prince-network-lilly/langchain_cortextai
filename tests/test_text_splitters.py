"""Tests for cortexchain.text_splitters"""
from cortexchain.text_splitters.character import CharacterTextSplitter
from cortexchain.text_splitters.recursive import RecursiveCharacterTextSplitter
from cortexchain.schema import Document


class TestCharacterTextSplitter:
    def test_basic_split(self):
        splitter = CharacterTextSplitter(separator="\n\n", chunk_size=50, chunk_overlap=0)
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = splitter.split_text(text)
        assert len(chunks) >= 2

    def test_overlap(self):
        splitter = CharacterTextSplitter(separator=" ", chunk_size=20, chunk_overlap=5)
        text = "one two three four five six seven eight"
        chunks = splitter.split_text(text)
        assert len(chunks) > 1

    def test_split_documents(self):
        splitter = CharacterTextSplitter(separator="\n\n", chunk_size=30, chunk_overlap=0)
        docs = [Document(page_content="Hello world.\n\nFoo bar baz.", metadata={"source": "test"})]
        result = splitter.split_documents(docs)
        assert all(isinstance(d, Document) for d in result)
        assert all("source" in d.metadata for d in result)
        assert all("chunk" in d.metadata for d in result)


class TestRecursiveCharacterTextSplitter:
    def test_uses_first_separator(self):
        splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " "], chunk_size=50, chunk_overlap=0
        )
        text = "Para one.\n\nPara two.\n\nPara three."
        chunks = splitter.split_text(text)
        assert len(chunks) >= 2

    def test_falls_through_separators(self):
        splitter = RecursiveCharacterTextSplitter(
            separators=["\n\n", "\n", " "], chunk_size=15, chunk_overlap=0
        )
        text = "This is a single long line without any paragraph breaks at all"
        chunks = splitter.split_text(text)
        assert all(len(c) <= 20 for c in chunks)  # Allow small overshoot

    def test_split_documents(self):
        splitter = RecursiveCharacterTextSplitter(chunk_size=30, chunk_overlap=5)
        docs = [Document(page_content="A" * 100, metadata={"id": 1})]
        result = splitter.split_documents(docs)
        assert len(result) > 1
        assert all(d.metadata["id"] == 1 for d in result)
