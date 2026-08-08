<div align="center">

# 📄 DocRAG

### AI-Powered PDF Question Answering System

Upload a PDF. Ask questions in plain English. Get answers grounded in your document — with the exact source passages and page numbers shown alongside every response.

**[Try it live →](https://docrag-mustafakhattak.streamlit.app/)**

</div>

---

## What it does

DocRAG is a Retrieval-Augmented Generation (RAG) chatbot for your own documents. It extracts and chunks text from PDFs you upload, embeds each chunk into a searchable vector index, retrieves the most relevant passages for any question you ask, and sends those passages — not the whole document — to a hosted LLM to generate a grounded answer.

**Nothing to install to try it.** Open the live demo, upload a PDF, start asking. Generation runs on the Hugging Face Inference API (a hosted model), so there's no local model download, no GPU required, no setup on your end.

## Features

| | Feature | Implementation |
|---|---|---|
| 📄 | Upload & analyze custom PDFs | `pypdf` text extraction, page-aware |
| 🔍 | Semantic search | `sentence-transformers` embeddings (`all-MiniLM-L6-v2`) |
| 🧠 | Retrieval-Augmented Generation | Retrieved chunks injected into the LLM prompt, not the full document |
| 🤖 | Hosted LLM inference | `huggingface_hub.InferenceClient` — no local model, no GPU needed |
| ⚡ | Fast vector retrieval | `FAISS` (`IndexFlatIP`, cosine similarity) |
| 💬 | Interactive chat interface | Streamlit, with streamed token-by-token responses |
| 📚 | Retrieved context visualization | Expandable "index card" view showing exactly what the model used |
| 📄 | Source page references | Every answer is traceable back to file + page number |
| 📝 | Chat export | Download the full transcript as `.txt` or formatted `.pdf` |
| 🎨 | Custom UI | Dark "reading room" theme — custom fonts, colors, and components |
| 💾 | Save/load index | Persist a processed document's index to disk, reload without reprocessing |

## Demo

<div align="center">
<i>Upload a PDF → Process → Ask questions → Get grounded answers with page citations</i>
</div>

```
Open the app  →  Upload PDF  →  Click "Process"  →  Ask a question  →  Read the answer + sources
```

## Project structure

```
docrag/
├── app.py                   # Streamlit UI — entry point
├── requirements.txt
├── .streamlit/
│   └── config.toml          # theme configuration
├── src/
│   ├── pdf_processor.py     # PDF text extraction + page-aware chunking
│   ├── vector_store.py      # FAISS index + sentence-transformers embeddings
│   ├── llm.py                # Hugging Face Inference API client
│   ├── rag_pipeline.py      # Retrieval + generation orchestration
│   ├── export_utils.py      # TXT / PDF chat export
│   └── styles.py            # Design tokens + HTML component helpers
└── data/                    # created at runtime (saved indexes)
```

## Tech stack

- **Frontend:** [Streamlit](https://streamlit.io)
- **Embeddings:** [sentence-transformers](https://www.sbert.net/) (`all-MiniLM-L6-v2`)
- **Vector search:** [FAISS](https://github.com/facebookresearch/faiss) (Meta AI)
- **LLM inference:** [Hugging Face Inference API](https://huggingface.co/docs/api-inference) (default model: `meta-llama/Llama-3.1-8B-Instruct`)
- **PDF parsing:** [pypdf](https://pypdf.readthedocs.io/)
- **PDF export:** [ReportLab](https://www.reportlab.com/)
- **Hosting:** [Streamlit Community Cloud](https://streamlit.io/cloud)

## Using the app

1. Open the sidebar and drop one or more PDFs into the uploader
2. Click **Process new file(s)** — extracts text, chunks it, embeds each chunk into the FAISS index
3. Ask a question in the chat box
4. Expand **📚 Retrieved context** under any answer to see exactly which passages (and page numbers) the model used
5. Use **⬇ .txt / ⬇ .pdf** in the sidebar to export the full conversation with source references
6. Click **💾 Save** to persist the index to `data/saved_index/`, then **📂 Load** it again in a future session without reprocessing

### Tuning retrieval quality

Open **⚙ Retrieval & model settings** in the sidebar:

| Setting | Effect |
|---|---|
| Chunks retrieved (top-k) | More = more context, but a noisier prompt. 3–6 is a good range. |
| Temperature | Lower = more literal/deterministic. Keep low (0–0.3) for factual Q&A. |
| Chunk size / overlap | Larger chunks preserve context but reduce retrieval precision. Applies to newly processed docs only. |
| Hugging Face model | Any chat-capable model id served by HF Inference Providers. |

## Deployment

This app is deployed on **[Streamlit Community Cloud](https://streamlit.io/cloud)** — free, and built specifically for Streamlit apps.

<details>
<summary><b>Deploy your own copy</b></summary>

1. Fork/clone this repo to your own GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io) → sign in with GitHub
3. **Create app** → **Deploy a public app from GitHub**
4. Set:
   - **Repository:** `mustafa-khattak/DocRAG`
   - **Branch:** `main`
   - **Main file path:** `app.py`
5. Click **Advanced settings** → paste into **Secrets**:
   ```toml
   HF_TOKEN = "hf_your_real_token_here"
   ```

</details>

## Roadmap

- [ ] OCR support for scanned PDFs
- [ ] Multi-document cross-referencing in a single session
- [ ] Configurable embedding model selection

## Contributing

Issues and pull requests are welcome. For significant changes, please open an issue first to discuss what you'd like to change.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

- [Hugging Face](https://huggingface.co) for hosted inference
- [Streamlit](https://streamlit.io) for the app framework and free hosting
- [Meta AI](https://ai.meta.com) for FAISS and the Llama model family

---

<div align="center">

Built by [Mustafa Khattak](https://github.com/Mustafa-khattak)

</div>
