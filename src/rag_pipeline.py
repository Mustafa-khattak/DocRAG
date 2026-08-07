"""
Orchestrates retrieval + generation and returns one structured result,
so the UI can render the answer, its retrieved context, and page
references from a single object.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, List, Tuple

from .llm import HFClient
from .vector_store import VectorStore


@dataclass
class RAGResult:
    answer: str
    sources: List[dict] = field(default_factory=list)

    @property
    def page_labels(self) -> List[str]:
        """Deduplicated, ordered list like ['report.pdf · p.4', ...]."""
        seen: List[str] = []
        for s in self.sources:
            label = f"{s['source']} · p.{s['page']}"
            if label not in seen:
                seen.append(label)
        return seen


class RAGPipeline:
    """Ties the vector store (retrieval) to the LLM client (generation)."""

    def __init__(self, vector_store: VectorStore, llm_client: HFClient):
        self.vector_store = vector_store
        self.llm_client = llm_client

    def query(self, question: str, top_k: int = 4,
              temperature: float = 0.2) -> RAGResult:
        sources = self.vector_store.search(question, k=top_k)
        answer = self.llm_client.ask(question, sources, temperature=temperature)
        return RAGResult(answer=answer, sources=sources)

    def query_stream(self, question: str, top_k: int = 4,
                      temperature: float = 0.2) -> Tuple[Iterator[str], List[dict]]:
        """Returns (token_stream, retrieved_sources) for a live chat UI."""
        sources = self.vector_store.search(question, k=top_k)
        stream = self.llm_client.ask_stream(question, sources, temperature=temperature)
        return stream, sources
