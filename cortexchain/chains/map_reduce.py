"""MapReduceChain — process documents in parallel (map) then combine results (reduce)."""
from typing import Callable, Dict, List, Optional

from cortexchain.chains.base import BaseChain
from cortexchain.chains.llm_chain import LLMChain
from cortexchain.llm.cortex import CortexLLM
from cortexchain.prompts.templates import PromptTemplate
from cortexchain.schema import Document

_DEFAULT_MAP_TEMPLATE = """\
Analyze the following text and provide a concise summary:

{text}

Summary:"""

_DEFAULT_REDUCE_TEMPLATE = """\
You have been given multiple summaries from different parts of a document.
Combine them into a single, coherent final answer.

Summaries:
{summaries}

Combined result:"""


class MapReduceChain(BaseChain):
    """Processes a list of documents: map applies LLM to each, reduce combines results."""

    def __init__(
        self,
        llm: CortexLLM,
        map_prompt: Optional[PromptTemplate] = None,
        reduce_prompt: Optional[PromptTemplate] = None,
        map_fn: Optional[Callable[[str], str]] = None,
        reduce_fn: Optional[Callable[[List[str]], str]] = None,
        verbose: bool = False,
    ):
        self.llm = llm
        self.map_prompt = map_prompt or PromptTemplate.from_template(_DEFAULT_MAP_TEMPLATE)
        self.reduce_prompt = reduce_prompt or PromptTemplate.from_template(_DEFAULT_REDUCE_TEMPLATE)
        self.map_fn = map_fn
        self.reduce_fn = reduce_fn
        self.verbose = verbose

    def _map_single(self, text: str) -> str:
        if self.map_fn:
            return self.map_fn(text)
        prompt = self.map_prompt.format(text=text)
        return self.llm(prompt)

    def _reduce(self, mapped_results: List[str]) -> str:
        if self.reduce_fn:
            return self.reduce_fn(mapped_results)
        combined = "\n\n---\n\n".join(
            f"[Part {i+1}]: {r}" for i, r in enumerate(mapped_results)
        )
        prompt = self.reduce_prompt.format(summaries=combined)
        return self.llm(prompt)

    def invoke(self, inputs: Dict) -> Dict:
        documents = inputs.get("documents", inputs.get("texts", []))
        if isinstance(documents, str):
            documents = [documents]

        # Convert Document objects to text
        texts = []
        for doc in documents:
            if isinstance(doc, Document):
                texts.append(doc.page_content)
            else:
                texts.append(str(doc))

        if self.verbose:
            print(f"[MapReduce] Mapping {len(texts)} documents...")

        # Map phase
        mapped = []
        for i, text in enumerate(texts):
            result = self._map_single(text)
            mapped.append(result)
            if self.verbose:
                print(f"  [Map {i+1}/{len(texts)}] {result[:80]}...")

        # Reduce phase
        if self.verbose:
            print(f"[MapReduce] Reducing {len(mapped)} results...")

        final = self._reduce(mapped)

        return {"output": final, "mapped_results": mapped}

    def run(self, documents: List) -> str:
        return self.invoke({"documents": documents})["output"]

    @property
    def _default_input_key(self) -> str:
        return "documents"


class RefineChain(BaseChain):
    """Processes documents iteratively — refines the answer with each new document chunk."""

    def __init__(
        self,
        llm: CortexLLM,
        initial_prompt: Optional[PromptTemplate] = None,
        refine_prompt: Optional[PromptTemplate] = None,
        verbose: bool = False,
    ):
        self.llm = llm
        self.initial_prompt = initial_prompt or PromptTemplate.from_template(
            "Summarize the following text:\n\n{text}\n\nSummary:"
        )
        self.refine_prompt = refine_prompt or PromptTemplate.from_template(
            "You have an existing summary:\n{existing}\n\n"
            "Refine it with this new information:\n{text}\n\n"
            "Refined summary:"
        )
        self.verbose = verbose

    def invoke(self, inputs: Dict) -> Dict:
        documents = inputs.get("documents", inputs.get("texts", []))
        texts = []
        for doc in documents:
            if isinstance(doc, Document):
                texts.append(doc.page_content)
            else:
                texts.append(str(doc))

        if not texts:
            return {"output": "", "iterations": 0}

        # Process first document
        current = self.llm(self.initial_prompt.format(text=texts[0]))
        if self.verbose:
            print(f"[Refine] Initial: {current[:100]}...")

        # Refine with remaining documents
        for i, text in enumerate(texts[1:], start=2):
            prompt = self.refine_prompt.format(existing=current, text=text)
            current = self.llm(prompt)
            if self.verbose:
                print(f"[Refine {i}/{len(texts)}] {current[:100]}...")

        return {"output": current, "iterations": len(texts)}

    def run(self, documents: List) -> str:
        return self.invoke({"documents": documents})["output"]

    @property
    def _default_input_key(self) -> str:
        return "documents"
