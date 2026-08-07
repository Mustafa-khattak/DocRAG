"""
Local vector store built on FAISS + sentence-transformers.

No external API calls are made: the embedding model runs on-device
(downloaded once from Hugging Face on first use, then cached locally),
and the FAISS index lives entirely in memory / on local disk.
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from .pdf_processor import Chunk

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, fully local, 384-dim


class VectorStore:
    """Wraps embedding generation + a FAISS similarity index."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self._model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        self.index: Optional[faiss.Index] = None
        self.chunks: List[Chunk] = []

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the embedding model so app startup stays fast."""
        if self._model is None:
            self._model = SentenceTransformer(self._model_name)
        return self._model

    def _embed(self, texts: List[str]) -> np.ndarray:
        vectors = self.model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,  # so inner product == cosine similarity
        )
        return vectors.astype("float32")

    def build(self, chunks: List[Chunk]) -> None:
        """Build (or rebuild) the index from scratch."""
        if not chunks:
            raise ValueError("Cannot build an index from zero chunks.")
        vectors = self._embed([c.text for c in chunks])
        dim = vectors.shape[1]
        index = faiss.IndexFlatIP(dim)  # inner product on normalized vecs = cosine sim
        index.add(vectors)
        self.index = index
        self.chunks = list(chunks)

    def add(self, chunks: List[Chunk]) -> None:
        """Add more chunks to an existing index (e.g. a second uploaded PDF)."""
        if not chunks:
            return
        if self.index is None:
            self.build(chunks)
            return
        vectors = self._embed([c.text for c in chunks])
        self.index.add(vectors)
        self.chunks.extend(chunks)

    def search(self, query: str, k: int = 4) -> List[dict]:
        """Return the top-k most similar chunks to the query."""
        if self.index is None or not self.chunks:
            return []
        k = min(k, len(self.chunks))
        q_vec = self._embed([query])
        scores, indices = self.index.search(q_vec, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            chunk = self.chunks[idx]
            results.append({
                "text": chunk.text,
                "page": chunk.page,
                "source": chunk.source,
                "score": float(score),
            })
        return results

    @property
    def is_ready(self) -> bool:
        return self.index is not None and len(self.chunks) > 0

    @property
    def num_chunks(self) -> int:
        return len(self.chunks)

    def save(self, dir_path: str) -> None:
        """Persist the index + chunk metadata to disk for later reuse."""
        if self.index is None:
            raise ValueError("Nothing to save yet — build the index first.")
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self.index, str(path / "index.faiss"))
        with open(path / "chunks.pkl", "wb") as f:
            pickle.dump(self.chunks, f)

    def load(self, dir_path: str) -> None:
        """Restore a previously saved index + chunk metadata."""
        path = Path(dir_path)
        index_file = path / "index.faiss"
        chunks_file = path / "chunks.pkl"
        if not index_file.exists() or not chunks_file.exists():
            raise FileNotFoundError("No saved index found at that location.")
        self.index = faiss.read_index(str(index_file))
        with open(chunks_file, "rb") as f:
            self.chunks = pickle.load(f)
