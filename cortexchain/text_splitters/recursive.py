from typing import List
from cortexchain.schema import Document


class RecursiveCharacterTextSplitter:
    """Splits text recursively trying each separator in order until chunks fit."""

    def __init__(
        self,
        separators: List[str] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        return self._split_text(text, self.separators)

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        if not text:
            return []

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            splits = list(text)
        else:
            splits = text.split(separator)

        good_chunks: List[str] = []
        current_chunk: List[str] = []
        current_length = 0

        for split in splits:
            split_len = len(split) + (len(separator) if current_chunk else 0)

            if current_length + split_len > self.chunk_size and current_chunk:
                merged = separator.join(current_chunk)
                if len(merged) > self.chunk_size and remaining_separators:
                    # Recursively split with next separator
                    good_chunks.extend(self._split_text(merged, remaining_separators))
                else:
                    good_chunks.append(merged)

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
            merged = separator.join(current_chunk)
            if len(merged) > self.chunk_size and remaining_separators:
                good_chunks.extend(self._split_text(merged, remaining_separators))
            else:
                good_chunks.append(merged)

        return good_chunks

    def split_documents(self, documents: List[Document]) -> List[Document]:
        result = []
        for doc in documents:
            texts = self.split_text(doc.page_content)
            for i, text in enumerate(texts):
                metadata = {**doc.metadata, "chunk": i}
                result.append(Document(page_content=text, metadata=metadata))
        return result
