"""
Export the chat transcript to a plain .txt file or a formatted .pdf,
including retrieved source/page references for every assistant answer.
"""
from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import List, TypedDict

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer


class ChatTurn(TypedDict):
    role: str            # "user" or "assistant"
    content: str
    pages: List[str]      # e.g. ["report.pdf · p.4"]; empty for user turns


def export_to_txt(turns: List[ChatTurn], title: str = "DocRAG Chat Export") -> bytes:
    lines = [title, f"Exported {datetime.now():%Y-%m-%d %H:%M}", "=" * 60, ""]
    for turn in turns:
        speaker = "You" if turn["role"] == "user" else "Assistant"
        lines.append(f"{speaker}:")
        lines.append(turn["content"])
        if turn.get("pages"):
            lines.append(f"Sources: {', '.join(turn['pages'])}")
        lines.append("")
    return "\n".join(lines).encode("utf-8")


def export_to_pdf(turns: List[ChatTurn], title: str = "DocRAG Chat Export") -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=LETTER,
        topMargin=0.9 * inch, bottomMargin=0.9 * inch,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DrTitle", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=18, textColor=colors.HexColor("#1B1F2B"), spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        "DrMeta", parent=styles["Normal"], fontSize=9,
        textColor=colors.HexColor("#6B7280"), spaceAfter=16,
    )
    user_style = ParagraphStyle(
        "DrUser", parent=styles["Normal"], fontName="Helvetica-Bold",
        fontSize=11, textColor=colors.HexColor("#12141C"),
        spaceBefore=14, spaceAfter=4,
    )
    answer_style = ParagraphStyle(
        "DrAnswer", parent=styles["Normal"], fontName="Helvetica",
        fontSize=10.5, leading=15, textColor=colors.HexColor("#1B1F2B"),
        spaceAfter=4,
    )
    source_style = ParagraphStyle(
        "DrSource", parent=styles["Normal"], fontName="Helvetica-Oblique",
        fontSize=8.5, textColor=colors.HexColor("#9C7A32"), spaceAfter=10,
    )

    story = [
        Paragraph(_escape(title), title_style),
        Paragraph(f"Exported {datetime.now():%B %d, %Y at %H:%M}", meta_style),
        HRFlowable(width="100%", color=colors.HexColor("#E5E1D8"), thickness=1),
        Spacer(1, 8),
    ]

    for turn in turns:
        text = _escape(turn["content"])
        if turn["role"] == "user":
            story.append(Paragraph(f"Q: {text}", user_style))
        else:
            story.append(Paragraph(text, answer_style))
            if turn.get("pages"):
                refs = " &nbsp;&middot;&nbsp; ".join(_escape(p) for p in turn["pages"])
                story.append(Paragraph(f"Sources: {refs}", source_style))

    doc.build(story)
    return buffer.getvalue()


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
