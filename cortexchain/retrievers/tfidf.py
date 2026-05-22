import math
import re
from collections import Counter
from typing import Dict, List
from cortexchain.schema import Document


class TFIDFRetriever:
    """Simple TF-IDF based retriever (no external dependencies). Ranks documents by relevance."""

    def __init__(self, documents: List[Document] = None, k: int = 4):
        self.k = k
        self.documents: List[Document] = []
        self._doc_freqs: Dict[str, int] = {}
        self._doc_vectors: List[Dict[str, float]] = []
        if documents:
            self.add_documents(documents)

    def add_documents(self, documents: List[Document]) -> None:
        self.documents.extend(documents)
        self._build_index()

    def _tokenize(self, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    def _build_index(self) -> None:
        self._doc_freqs = {}
        self._doc_vectors = []
        n = len(self.documents)

        doc_term_counts = []
        for doc in self.documents:
            tokens = self._tokenize(doc.page_content)
            tf = Counter(tokens)
            doc_term_counts.append(tf)
            for term in set(tokens):
                self._doc_freqs[term] = self._doc_freqs.get(term, 0) + 1

        for tf in doc_term_counts:
            vector = {}
            total_terms = sum(tf.values())
            for term, count in tf.items():
                tf_score = count / total_terms
                idf = math.log((n + 1) / (self._doc_freqs.get(term, 0) + 1)) + 1
                vector[term] = tf_score * idf
            self._doc_vectors.append(vector)

    def _query_vector(self, query: str) -> Dict[str, float]:
        tokens = self._tokenize(query)
        tf = Counter(tokens)
        n = len(self.documents)
        vector = {}
        total_terms = sum(tf.values())
        for term, count in tf.items():
            tf_score = count / total_terms
            idf = math.log((n + 1) / (self._doc_freqs.get(term, 0) + 1)) + 1
            vector[term] = tf_score * idf
        return vector

    def _cosine_similarity(self, vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
        common_terms = set(vec_a.keys()) & set(vec_b.keys())
        if not common_terms:
            return 0.0
        dot = sum(vec_a[t] * vec_b[t] for t in common_terms)
        mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
        mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def retrieve(self, query: str, k: int = None) -> List[Document]:
        """Retrieve top-k most relevant documents for the query."""
        if not self.documents:
            return []
        k = k or self.k
        query_vec = self._query_vector(query)
        scores = []
        for i, doc_vec in enumerate(self._doc_vectors):
            score = self._cosine_similarity(query_vec, doc_vec)
            scores.append((score, i))
        scores.sort(reverse=True)
        results = []
        for score, idx in scores[:k]:
            doc = self.documents[idx]
            result = Document(
                page_content=doc.page_content,
                metadata={**doc.metadata, "relevance_score": round(score, 4)},
            )
            results.append(result)
        return results

    @classmethod
    def from_documents(cls, documents: List[Document], k: int = 4) -> "TFIDFRetriever":
        return cls(documents=documents, k=k)
