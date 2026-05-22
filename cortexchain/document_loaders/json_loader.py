import json
from typing import Any, Callable, Dict, List, Optional
from cortexchain.schema import Document


class JSONLoader:
    """Loads a JSON file. Can extract specific fields using a jq-like path or custom function."""

    def __init__(
        self,
        file_path: str,
        content_key: Optional[str] = None,
        metadata_keys: Optional[List[str]] = None,
        jq_schema: Optional[str] = None,
        text_content: bool = True,
        encoding: str = "utf-8",
    ):
        self.file_path = file_path
        self.content_key = content_key
        self.metadata_keys = metadata_keys or []
        self.jq_schema = jq_schema
        self.text_content = text_content
        self.encoding = encoding

    def load(self) -> List[Document]:
        with open(self.file_path, "r", encoding=self.encoding) as f:
            data = json.load(f)

        if isinstance(data, list):
            return self._load_list(data)
        elif isinstance(data, dict):
            if self.jq_schema and self.jq_schema in data:
                items = data[self.jq_schema]
                if isinstance(items, list):
                    return self._load_list(items)
            return [self._dict_to_doc(data, 0)]
        else:
            return [Document(page_content=str(data), metadata={"source": self.file_path})]

    def _load_list(self, items: List[Any]) -> List[Document]:
        docs = []
        for i, item in enumerate(items):
            if isinstance(item, dict):
                docs.append(self._dict_to_doc(item, i))
            else:
                docs.append(
                    Document(
                        page_content=str(item),
                        metadata={"source": self.file_path, "index": i},
                    )
                )
        return docs

    def _dict_to_doc(self, item: Dict, index: int) -> Document:
        if self.content_key and self.content_key in item:
            content = str(item[self.content_key])
        else:
            content = json.dumps(item, ensure_ascii=False)

        metadata = {"source": self.file_path, "index": index}
        for key in self.metadata_keys:
            if key in item:
                metadata[key] = item[key]

        return Document(page_content=content, metadata=metadata)

    def load_and_split(self, splitter=None) -> List[Document]:
        docs = self.load()
        if splitter:
            return splitter.split_documents(docs)
        return docs
