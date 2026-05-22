import csv
from typing import List, Optional
from cortexchain.schema import Document


class CSVLoader:
    """Loads a CSV file — each row becomes a Document."""

    def __init__(
        self,
        file_path: str,
        content_columns: Optional[List[str]] = None,
        metadata_columns: Optional[List[str]] = None,
        encoding: str = "utf-8",
    ):
        self.file_path = file_path
        self.content_columns = content_columns
        self.metadata_columns = metadata_columns
        self.encoding = encoding

    def load(self) -> List[Document]:
        docs = []
        with open(self.file_path, "r", encoding=self.encoding, newline="") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if self.content_columns:
                    content = " | ".join(
                        f"{col}: {row.get(col, '')}" for col in self.content_columns
                    )
                else:
                    content = " | ".join(f"{k}: {v}" for k, v in row.items())

                metadata = {"source": self.file_path, "row": i}
                if self.metadata_columns:
                    for col in self.metadata_columns:
                        metadata[col] = row.get(col, "")

                docs.append(Document(page_content=content, metadata=metadata))
        return docs

    def load_and_split(self, splitter=None) -> List[Document]:
        docs = self.load()
        if splitter:
            return splitter.split_documents(docs)
        return docs
