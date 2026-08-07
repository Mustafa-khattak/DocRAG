"""
Design system for DocRAG's UI: a "reading room" theme — deep ink
background, brass/gold accents, a characterful serif for headings, and
retrieved context rendered as library catalog-style index cards.

Kept separate from app.py so the visual language lives in one place.
"""

# ---- Token system ------------------------------------------------------
INK = "#12141C"            # app background
SURFACE = "#1A1E29"        # panels / sidebar / cards
SURFACE_RAISED = "#232838"  # hover state, raised elements
PARCHMENT = "#EAE3D3"      # primary text (warm off-white)
MUTED = "#8B92A6"          # secondary text
BRASS = "#C9A15D"          # primary accent (lamps, gilded spines)
BRASS_DIM = "#9C7A32"
MOSS = "#6E8F7C"           # secondary accent (cloth book covers)
RULE = "#2A2F3D"           # hairline dividers
DANGER = "#C97A6D"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'Inter', sans-serif;
}}

.stApp {{
    background: {INK};
    color: {PARCHMENT};
}}

/* ---- Headings use the display serif ---- */
h1, h2, h3, .dr-display {{
    font-family: 'Fraunces', serif !important;
    color: {PARCHMENT} !important;
    letter-spacing: 0.2px;
}}

/* ---- Sidebar: the "card catalog drawer" ---- */
[data-testid="stSidebar"] {{
    background: {SURFACE};
    border-right: 1px solid {RULE};
}}
[data-testid="stSidebar"] * {{
    color: {PARCHMENT};
}}

/* ---- Header brand block ---- */
.dr-brand {{
    display: flex;
    align-items: baseline;
    gap: 10px;
    padding: 4px 0 18px 0;
    border-bottom: 1px solid {RULE};
    margin-bottom: 18px;
}}
.dr-brand-mark {{
    font-family: 'Fraunces', serif;
    font-size: 26px;
    font-weight: 700;
    color: {BRASS};
}}
.dr-brand-sub {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: {MUTED};
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

/* ---- Status pill (AI assistant readiness) ---- */
.dr-status {{
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11.5px;
    padding: 5px 10px;
    border-radius: 20px;
    border: 1px solid {RULE};
    background: {SURFACE_RAISED};
    color: {MUTED};
}}
.dr-dot {{
    width: 7px; height: 7px; border-radius: 50%;
    display: inline-block;
}}
.dr-dot.ok {{ background: {MOSS}; box-shadow: 0 0 6px {MOSS}; }}
.dr-dot.bad {{ background: {DANGER}; box-shadow: 0 0 6px {DANGER}; }}

/* ---- Document chip list ---- */
.dr-doc {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 10px;
    background: {SURFACE_RAISED};
    border: 1px solid {RULE};
    border-radius: 8px;
    margin-bottom: 6px;
    font-size: 13px;
}}
.dr-doc-name {{ color: {PARCHMENT}; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 160px; }}
.dr-doc-meta {{ font-family: 'JetBrains Mono', monospace; color: {BRASS}; font-size: 11px; }}

/* ---- Buttons ---- */
.stButton > button, .stDownloadButton > button {{
    background: transparent;
    color: {BRASS};
    border: 1px solid {BRASS_DIM};
    border-radius: 8px;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    transition: all 0.15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    background: {BRASS};
    color: {INK};
    border-color: {BRASS};
}}
.stButton > button[kind="primary"] {{
    background: {BRASS};
    color: {INK};
}}

/* ---- Chat messages ---- */
[data-testid="stChatMessage"] {{
    background: {SURFACE};
    border: 1px solid {RULE};
    border-radius: 12px;
    padding: 4px 6px;
}}

/* ---- Retrieved-context index cards (signature element) ---- */
.dr-card {{
    position: relative;
    background: {SURFACE_RAISED};
    border: 1px dashed {RULE};
    border-radius: 6px;
    padding: 12px 14px 12px 14px;
    margin-bottom: 10px;
}}
.dr-card-tab {{
    position: absolute;
    top: -9px; right: 12px;
    background: {BRASS};
    color: {INK};
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    letter-spacing: 0.3px;
}}
.dr-card-source {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10.5px;
    color: {MOSS};
    margin-bottom: 6px;
    letter-spacing: 0.2px;
}}
.dr-card-text {{
    font-size: 13px;
    line-height: 1.55;
    color: {PARCHMENT};
    opacity: 0.92;
}}
.dr-card-score {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: {MUTED};
    margin-top: 8px;
}}

/* ---- Empty state ---- */
.dr-empty {{
    text-align: center;
    padding: 80px 20px;
    color: {MUTED};
}}
.dr-empty-mark {{
    font-family: 'Fraunces', serif;
    font-size: 42px;
    color: {BRASS};
    margin-bottom: 10px;
}}

/* ---- Misc ---- */
[data-testid="stExpander"] {{
    background: {SURFACE};
    border: 1px solid {RULE};
    border-radius: 10px;
}}
hr {{ border-color: {RULE}; }}
</style>
"""


def _esc(text: str) -> str:
    """Escape text pulled from PDFs/filenames before dropping it into raw HTML."""
    return (
        str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def status_pill(ok: bool, label: str) -> str:
    cls = "ok" if ok else "bad"
    return f'<span class="dr-status"><span class="dr-dot {cls}"></span>{label}</span>'


def doc_chip(name: str, pages: int, chunks: int) -> str:
    safe_name = _esc(name)
    return (
        f'<div class="dr-doc">'
        f'<span class="dr-doc-name" title="{safe_name}">📄 {safe_name}</span>'
        f'<span class="dr-doc-meta">{pages}p · {chunks}ch</span>'
        f'</div>'
    )


def context_card(source: str, page: int, text: str, score: float) -> str:
    snippet = text if len(text) <= 320 else text[:320].rsplit(" ", 1)[0] + "…"
    return (
        f'<div class="dr-card">'
        f'<span class="dr-card-tab">p.{page}</span>'
        f'<div class="dr-card-source">{_esc(source)}</div>'
        f'<div class="dr-card-text">{_esc(snippet)}</div>'
        f'<div class="dr-card-score">similarity {score:.2f}</div>'
        f'</div>'
    )


def brand_header() -> str:
    return (
        '<div class="dr-brand">'
        '<span class="dr-brand-mark">📄 DocRAG</span>'
        '<span class="dr-brand-sub">AI PDF assistant</span>'
        '</div>'
    )
