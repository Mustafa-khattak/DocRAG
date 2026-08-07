"""
Thin wrapper around the Hugging Face Inference API for chat completion.

Replaces the local Ollama client: instead of running a model on-device,
this calls a hosted model via `huggingface_hub.InferenceClient`. The
Space's HF_TOKEN (set as a Repository Secret) authenticates the request,
so recruiters/viewers never need to install or run anything locally —
they just open the Space and start asking questions.
"""
from __future__ import annotations

from typing import Iterator, List, Optional, Tuple

from huggingface_hub import InferenceClient

DEFAULT_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

SYSTEM_PROMPT = (
    "You are a careful research assistant helping a user understand a "
    "document they uploaded. Answer the question using ONLY the context "
    "excerpts provided below. If the context does not contain enough "
    "information to answer, say so plainly instead of guessing or using "
    "outside knowledge. Be concise, direct, and specific. Page references "
    "are shown separately in the interface, so you don't need to cite "
    "them yourself inside the answer."
)


class HFClient:
    """Talks to a hosted model via the Hugging Face Inference API."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: Optional[str] = None):
        self.model = model
        self.api_key = api_key
        self._client = InferenceClient(api_key=api_key, provider="auto") if api_key else None

    def is_available(self) -> Tuple[bool, str]:
        """
        Checks that an API token is configured. This is a local, instant
        check (no network round trip) — actual model reachability is
        surfaced if/when a real request fails, so the sidebar stays fast.
        """
        if not self.api_key or not self.api_key.strip():
            return False, (
                "No Hugging Face API token found. Add HF_TOKEN as a Repository "
                "Secret in this Space's Settings (or in .streamlit/secrets.toml "
                "for local runs)."
            )
        return True, "ready"

    def _build_messages(self, question: str, context_chunks: List[dict]) -> List[dict]:
        if context_chunks:
            context_block = "\n\n".join(
                f"[Source: {c['source']}, page {c['page']}]\n{c['text']}"
                for c in context_chunks
            )
        else:
            context_block = "No relevant context was retrieved from the document."

        user_content = f"Context excerpts:\n{context_block}\n\nQuestion: {question}"
        return [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ]

    def ask(self, question: str, context_chunks: List[dict],
             temperature: float = 0.2) -> str:
        """Blocking, non-streamed answer."""
        messages = self._build_messages(question, context_chunks)
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=800,
        )
        return response.choices[0].message.content

    def ask_stream(self, question: str, context_chunks: List[dict],
                    temperature: float = 0.2) -> Iterator[str]:
        """Streamed answer: yields text deltas as the model generates them."""
        messages = self._build_messages(question, context_chunks)
        stream = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=800,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
