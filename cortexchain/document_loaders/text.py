from typing import List
from cortexchain.schema import Document


class TextLoader:
    """Loads a plain text file as a single Document."""

    def __init__(self, file_path: str, encoding: str = "utf-8"):
        self.file_path = file_path
        self.encoding = encoding

    def load(self) -> List[Document]:
        with open(self.file_path, "r", encoding=self.encoding) as f:
            content = f.read()
        return [
            Document(
                page_content=content,
                metadata={"source": self.file_path},
            )
        ]

    def load_and_split(self, splitter=None) -> List[Document]:
        docs = self.load()
        if splitter:
            return splitter.split_documents(docs)
        return docs
