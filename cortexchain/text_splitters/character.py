from typing import List
from cortexchain.schema import Document


class CharacterTextSplitter:
    """Splits text by a single separator with chunk size and overlap control."""

    def __init__(
        self,
        separator: str = "\n\n",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.separator = separator
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        splits = text.split(self.separator)
        chunks = []
        current_chunk: List[str] = []
        current_length = 0

        for split in splits:
            split_len = len(split)
            if current_length + split_len > self.chunk_size and current_chunk:
                chunk_text = self.separator.join(current_chunk)
                chunks.append(chunk_text)
                # Keep overlap
                overlap_chunks: List[str] = []
                overlap_len = 0
                for piece in reversed(current_chunk):
                    if overlap_len + len(piece) > self.chunk_overlap:
                        break
                    overlap_chunks.insert(0, piece)
                    overlap_len += len(piece)
                current_chunk = overlap_chunks
                current_length = overlap_len

            current_chunk.append(split)
            current_length += split_len

        if current_chunk:
            chunks.append(self.separator.join(current_chunk))

        return chunks

    def split_documents(self, documents: List[Document]) -> List[Document]:
        result = []
        for doc in documents:
            texts = self.split_text(doc.page_content)
            for i, text in enumerate(texts):
                metadata = {**doc.metadata, "chunk": i}
                result.append(Document(page_content=text, metadata=metadata))
        return result
