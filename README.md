# 📄 DocRAG — AI-Powered PDF Question Answering System

A hosted, recruiter-friendly chatbot that answers questions about your own
PDF documents. Upload a PDF in the browser, ask questions in plain
English, and get answers grounded in the document — with the exact
retrieved passages and page numbers shown alongside every answer.

**Nothing to install.** Generation runs on the Hugging Face Inference API
(a hosted model), so anyone with the Space link can use it immediately —
no Ollama, no localhost, no local model download.

## Features

| Feature | How it's implemented |
|---|---|
| 📄 Upload & analyze custom PDFs | `pypdf` text extraction, per-page aware |
| 🔍 Semantic search | `sentence-transformers` embeddings (`all-MiniLM-L6-v2`) |
| 🧠 Retrieval-Augmented Generation | Retrieved chunks injected into the LLM prompt |
| 🤖 Hugging Face LLM | Hosted inference via `huggingface_hub.InferenceClient` (default: Mistral-7B-Instruct) |
| ⚡ Fast retrieval | `FAISS` (`IndexFlatIP`, cosine similarity) |
| 💬 Interactive chat | `Streamlit` chat UI with streaming responses |
| 📚 Retrieved context visualization | Expandable "index card" view per answer |
| 📄 Source page references | Every chunk keeps its source file + page number |
| 📝 Chat export | Download the transcript as `.txt` or formatted `.pdf` |
| 🎨 Modern UI | Custom dark theme, custom fonts, styled components |
| ☁️ Deployable on Hugging Face Spaces | One secret (`HF_TOKEN`), zero local setup for viewers |

Everything runs **through the Streamlit browser interface** — upload
files and read answers there, not in a terminal.

## Project structure

```
docrag/
├── app.py                   # Streamlit UI — run this
├── requirements.txt
├── .streamlit/config.toml   # theme
├── src/
│   ├── pdf_processor.py     # PDF text extraction + page-aware chunking
│   ├── vector_store.py      # FAISS + sentence-transformers embeddings
│   ├── llm.py                # Hugging Face Inference API client
│   ├── rag_pipeline.py      # Retrieval + generation orchestration
│   ├── export_utils.py      # TXT / PDF chat export
│   └── styles.py            # Design tokens + HTML component helpers
└── data/                    # created at runtime (saved indexes)
```

## Recruiter / viewer workflow

Once deployed, using it is exactly four steps — nothing to install:

```
Open the Space  →  Upload a PDF  →  Wait ~10 seconds  →  Ask questions
```

## Deploying to Hugging Face Spaces

1. Create a new Space at [huggingface.co/new-space](https://huggingface.co/new-space)
   - **SDK:** Streamlit
2. Push/upload this project's files to the Space repo (via `git push` or
   the web uploader) — connecting an existing GitHub repo works too
3. Add your API token as a secret:
   **Space → Settings → Repository Secrets → New secret**
   - Name: `HF_TOKEN`
   - Value: a token from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) (read/Inference scope)
4. The Space builds automatically. Once it's live, share the link:
   ```
   https://huggingface.co/spaces/yourusername/DocRAG
   ```

The app reads the token automatically via `st.secrets["HF_TOKEN"]` —
no code changes needed after setting the secret.

> **Model choice:** the default, `meta-llama/Llama-3.1-8B-Instruct`, is
> reliably served for chat completion by HF's free Inference Providers.
> Not every model id works out of the box — a model must be hosted for
> the *chat completion* task by at least one connected provider, or
> you'll see an error like `"... is not a chat model"`. If that happens
> (or a model is rate-limited/"cold"), swap the model id in the
> sidebar's **Retrieval & model settings**, or in `DEFAULT_MODEL` in
> `src/llm.py`. Other models known to work well: `Qwen/Qwen2.5-7B-Instruct`,
> `openai/gpt-oss-120b:cerebras`. You can check whether a given model
> supports chat completion on its Hugging Face model page, under the
> "Inference Providers" section.

## Running locally (optional)

You don't need Ollama or any local model — just Python and an HF token.

```bash
# 1. Create and activate a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Provide your HF token locally
mkdir -p .streamlit
echo 'HF_TOKEN = "hf_your_token_here"' > .streamlit/secrets.toml

# 4. Launch the app
streamlit run app.py
```

Streamlit opens `http://localhost:8501` in your browser — that's where
you upload PDFs and chat.

> The embedding model (`all-MiniLM-L6-v2`, ~90 MB) downloads automatically
> from Hugging Face the first time you process a PDF, then is cached
> locally. Embedding itself runs on your machine either way — only the
> answer-generation step calls the hosted API.

## Using the app

1. Open the sidebar and drop one or more PDFs into the uploader.
2. Click **Process new file(s)** — this extracts text, splits it into
   overlapping chunks, and embeds each chunk into the FAISS index.
3. Ask a question in the chat box at the bottom of the page.
4. Expand **📚 Retrieved context** under any answer to see exactly which
   passages (and page numbers) the model used.
5. Use **⬇ .txt / ⬇ .pdf** in the sidebar to export the whole
   conversation, including source references.
6. Optionally hit **💾 Save** to persist the FAISS index to
   `data/saved_index/`, so you can **📂 Load** it again in a future
   session without re-processing the PDFs.

### Tuning retrieval quality

Open **⚙ Retrieval & model settings** in the sidebar:

- **Chunks retrieved per question (top-k)** — more chunks = more context,
  but a noisier prompt. 3–6 is a good starting range.
- **Temperature** — lower is more literal/deterministic; higher is more
  creative. For factual document Q&A, keep this low (0–0.3).
- **Chunk size / overlap** — larger chunks preserve more context per
  passage but reduce retrieval precision. These only affect documents
  processed *after* you change them.
- **Hugging Face model** — swap in any chat-capable model id served by
  HF Inference Providers.

## Troubleshooting

- **"... is not a chat model" / `model_not_supported`** — the model id
  you entered isn't currently hosted for chat completion by any HF
  Inference Provider (this can happen even for instruction-tuned models,
  since hosting depends on what providers choose to serve). Switch to a
  model confirmed to work, e.g. `meta-llama/Llama-3.1-8B-Instruct` or
  `Qwen/Qwen2.5-7B-Instruct`, in the sidebar's model field.
- **"⚠️ HF token missing"** — set `HF_TOKEN` as a Repository Secret (on
  Spaces) or in `.streamlit/secrets.toml` (locally).
- **Generation fails / times out** — the free Inference tier can be slow
  or rate-limited under load; wait and retry, or switch to a different
  model in the sidebar.
- **"No extractable text found in ..."** — the PDF is likely a scanned
  image rather than real text. This project doesn't include OCR; you'd
  need to run the file through an OCR tool first.
- **Answers ignore the document / seem generic** — try increasing top-k,
  or check the **Retrieved context** panel to see whether relevant
  passages were actually retrieved. If not, the chunk size may be
  splitting key information awkwardly — try a larger chunk size.

## Notes on data flow

Document upload, text extraction, chunking, and embedding all happen
locally in the Space's container — your PDF's raw text is never sent
anywhere except to the LLM at generation time, and only the small
set of *retrieved chunks* relevant to each question (not the whole
document) is included in that request, sent to the Hugging Face
Inference API to generate the answer.
