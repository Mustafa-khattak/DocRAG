"""
DocRAG — an AI-powered PDF Q&A assistant.

Streamlit UI on top of FAISS (semantic retrieval, local) and the Hugging
Face Inference API (hosted generation). Recruiters/viewers just open the
deployed Space, upload a PDF, and ask questions — no installs, no
localhost, no local model download.

Run with:
    streamlit run app.py
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st

from src.export_utils import export_to_pdf, export_to_txt
from src.llm import DEFAULT_MODEL, HFClient
from src.pdf_processor import process_pdf
from src.rag_pipeline import RAGPipeline
from src.styles import CSS, brand_header, context_card, doc_chip, status_pill
from src.vector_store import VectorStore

INDEX_DIR = Path("data/saved_index")

st.set_page_config(
    page_title="DocRAG — AI PDF Assistant",
    page_icon="📄",
    layout="wide",
)
st.markdown(CSS, unsafe_allow_html=True)


def get_hf_token() -> str:
    """
    Reads the HF API token from Streamlit secrets (the normal path once
    deployed to a Space with HF_TOKEN set as a Repository Secret), falling
    back to an environment variable for local development.
    """
    try:
        token = st.secrets["HF_TOKEN"]
        if token:
            return token
    except Exception:
        pass
    return os.environ.get("HF_TOKEN", "")


# ----------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------
def _default_settings() -> dict:
    return {
        "chunk_size": 800,
        "chunk_overlap": 150,
        "top_k": 4,
        "temperature": 0.2,
        "model": DEFAULT_MODEL,
    }


def init_state() -> None:
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = VectorStore()
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = {}   # name -> {"pages": n, "chunks": n}
    if "messages" not in st.session_state:
        st.session_state.messages = []           # [{"role","content","sources","pages"}]
    if "settings" not in st.session_state:
        st.session_state.settings = _default_settings()


def summarize_vector_store(vs: VectorStore) -> dict:
    """Rebuild the per-document summary shown in the sidebar (used after Load)."""
    summary: dict = {}
    for c in vs.chunks:
        entry = summary.setdefault(c.source, {"pages": set(), "chunks": 0})
        entry["pages"].add(c.page)
        entry["chunks"] += 1
    return {name: {"pages": len(v["pages"]), "chunks": v["chunks"]} for name, v in summary.items()}


def get_llm_client() -> HFClient:
    model = st.session_state.settings["model"]
    token = get_hf_token()
    if (
        "llm_client" not in st.session_state
        or st.session_state.llm_client.model != model
        or st.session_state.llm_client.api_key != token
    ):
        st.session_state.llm_client = HFClient(model=model, api_key=token)
    return st.session_state.llm_client


init_state()

# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
with st.sidebar:
    st.markdown(brand_header(), unsafe_allow_html=True)

    llm_client = get_llm_client()
    ai_ok, ai_msg = llm_client.is_available()
    st.markdown(
        status_pill(ai_ok, "🤖 AI Assistant Ready" if ai_ok else "⚠️ HF token missing"),
        unsafe_allow_html=True,
    )
    if not ai_ok:
        st.caption(ai_msg)

    st.markdown("&nbsp;", unsafe_allow_html=True)
    st.markdown("**Upload documents**")
    uploaded_files = st.file_uploader(
        "Drop PDF files here",
        type=["pdf"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
        if new_files and st.button(f"⚙ Process {len(new_files)} new file(s)", use_container_width=True):
            progress = st.progress(0.0, text="Starting…")
            cfg = st.session_state.settings
            for i, f in enumerate(new_files):
                progress.progress(i / len(new_files), text=f"Reading {f.name}…")
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                    tmp.write(f.getvalue())
                    tmp_path = tmp.name
                try:
                    chunks = process_pdf(
                        tmp_path, f.name,
                        chunk_size=cfg["chunk_size"],
                        chunk_overlap=cfg["chunk_overlap"],
                    )
                    progress.progress((i + 0.5) / len(new_files), text=f"Embedding {f.name}…")
                    st.session_state.vector_store.add(chunks)
                    pages = len({c.page for c in chunks})
                    st.session_state.processed_files[f.name] = {"pages": pages, "chunks": len(chunks)}
                except ValueError as exc:
                    st.error(str(exc))
                finally:
                    Path(tmp_path).unlink(missing_ok=True)
            progress.progress(1.0, text="Done")
            progress.empty()
            st.rerun()

    if st.session_state.processed_files:
        st.markdown("**Indexed documents**")
        for name, meta in st.session_state.processed_files.items():
            st.markdown(doc_chip(name, meta["pages"], meta["chunks"]), unsafe_allow_html=True)

    with st.expander("⚙ Retrieval & model settings"):
        cfg = st.session_state.settings
        cfg["model"] = st.text_input("Hugging Face model", value=cfg["model"],
                                      help="Any chat-capable model id served by HF Inference Providers.")
        cfg["top_k"] = st.slider("Chunks retrieved per question", 1, 10, cfg["top_k"])
        cfg["temperature"] = st.slider("Temperature", 0.0, 1.0, cfg["temperature"], 0.05)
        cfg["chunk_size"] = st.slider("Chunk size (characters)", 300, 2000, cfg["chunk_size"], 50)
        cfg["chunk_overlap"] = st.slider("Chunk overlap (characters)", 0, 400, cfg["chunk_overlap"], 10)
        st.caption("Chunk size/overlap apply to newly processed documents only.")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 Clear chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col2:
        if st.button("♻ Reset all", use_container_width=True):
            for key in ["vector_store", "processed_files", "messages", "llm_client", "settings"]:
                st.session_state.pop(key, None)
            init_state()
            st.rerun()

    if st.session_state.vector_store.is_ready:
        st.markdown("---")
        st.markdown("**Save / load index**")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("💾 Save", use_container_width=True):
                st.session_state.vector_store.save(str(INDEX_DIR))
                st.success("Saved to disk.")
        with c2:
            if st.button("📂 Load", use_container_width=True, disabled=not INDEX_DIR.exists()):
                st.session_state.vector_store.load(str(INDEX_DIR))
                st.session_state.processed_files = summarize_vector_store(st.session_state.vector_store)
                st.success("Loaded from disk.")
                st.rerun()

    if st.session_state.messages:
        st.markdown("---")
        st.markdown("**Export chat**")
        export_turns = [
            {"role": m["role"], "content": m["content"], "pages": m.get("pages", [])}
            for m in st.session_state.messages
        ]
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                "⬇ .txt", data=export_to_txt(export_turns),
                file_name="docrag_chat.txt", mime="text/plain",
                use_container_width=True,
            )
        with c2:
            st.download_button(
                "⬇ .pdf", data=export_to_pdf(export_turns),
                file_name="docrag_chat.pdf", mime="application/pdf",
                use_container_width=True,
            )


# ----------------------------------------------------------------------
# Main chat area
# ----------------------------------------------------------------------
st.markdown("## Ask your documents anything")
st.caption("Every answer is grounded in the PDFs you've uploaded, with retrieved passages and page numbers shown alongside every answer.")

if not st.session_state.vector_store.is_ready:
    st.markdown(
        '<div class="dr-empty">'
        '<div class="dr-empty-mark">📄</div>'
        "Upload a PDF from the sidebar and click <b>Process</b> to begin."
        "</div>",
        unsafe_allow_html=True,
    )
else:
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg["role"] == "assistant" and msg.get("sources"):
                with st.expander(f"📚 Retrieved context ({len(msg['sources'])})"):
                    for s in msg["sources"]:
                        st.markdown(
                            context_card(s["source"], s["page"], s["text"], s["score"]),
                            unsafe_allow_html=True,
                        )

    question = st.chat_input("Ask a question about your documents…")
    if question:
        st.session_state.messages.append({"role": "user", "content": question, "pages": []})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            ai_ok, ai_msg = llm_client.is_available()
            sources = []
            if not ai_ok:
                st.error(ai_msg)
                answer_text = ai_msg
            else:
                pipeline = RAGPipeline(st.session_state.vector_store, llm_client)
                try:
                    stream, sources = pipeline.query_stream(
                        question,
                        top_k=st.session_state.settings["top_k"],
                        temperature=st.session_state.settings["temperature"],
                    )
                    # Stream tokens into the chat UI and accumulate full answer text
                    answer_text = ""
                    placeholder = st.empty()
                    for delta in stream:
                        answer_text += delta
                        placeholder.markdown(answer_text)
                except Exception as exc:
                    answer_text = f"Generation failed: {exc}"
                    st.error(answer_text)

            if sources:
                with st.expander(f"📚 Retrieved context ({len(sources)})"):
                    for s in sources:
                        st.markdown(
                            context_card(s["source"], s["page"], s["text"], s["score"]),
                            unsafe_allow_html=True,
                        )

        page_labels, seen = [], set()
        for s in sources:
            label = f"{s['source']} · p.{s['page']}"
            if label not in seen:
                seen.add(label)
                page_labels.append(label)

        st.session_state.messages.append({
            "role": "assistant",
            "content": answer_text,
            "sources": sources,
            "pages": page_labels,
        })
