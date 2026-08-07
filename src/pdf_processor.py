"""
PDF processing utilities.

Extracts text page-by-page and splits it into overlapping chunks while
preserving page-number metadata, so every retrieved passage can be
traced back to its exact source page later in the pipeline.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Tuple

from pypdf import PdfReader


@dataclass
class Chunk:
    """A single retrievable unit of text with full provenance."""
    text: str
    page: int            # 1-indexed page number
    source: str           # original filename
    chunk_id: str = field(default="")


def extract_pages(file_path: str) -> List[Tuple[int, str]]:
    """Return a list of (page_number, page_text) tuples, 1-indexed."""
    reader = PdfReader(file_path)
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = _clean_text(text)
        if text:
            pages.append((i, text))
    return pages


def _clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_pages(
    pages: List[Tuple[int, str]],
    source: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> List[Chunk]:
    """
    Split each page's text into overlapping character-based chunks.

    Chunking per-page (rather than across the whole document) keeps the
    page reference for every chunk unambiguous, which is what powers the
    "source page reference" feature in the UI.
    """
    chunks: List[Chunk] = []
    counter = 0

    for page_num, text in pages:
        if len(text) <= chunk_size:
            counter += 1
            chunks.append(Chunk(
                text=text, page=page_num, source=source,
                chunk_id=f"{source}-p{page_num}-{counter}",
            ))
            continue

        start = 0
        text_len = len(text)
        while start < text_len:
            end = start + chunk_size
            piece = text[start:end]

            # Prefer breaking on a word boundary rather than mid-word.
            if end < text_len:
                last_space = piece.rfind(" ")
                if last_space > chunk_size * 0.5:
                    piece = piece[:last_space]
                    end = start + last_space

            piece = piece.strip()
            if piece:
                counter += 1
                chunks.append(Chunk(
                    text=piece, page=page_num, source=source,
                    chunk_id=f"{source}-p{page_num}-{counter}",
                ))

            if end >= text_len:
                break
            start = max(end - chunk_overlap, start + 1)

    return chunks


def process_pdf(
    file_path: str,
    source_name: str,
    chunk_size: int = 800,
    chunk_overlap: int = 150,
) -> List[Chunk]:
    """End-to-end: PDF file path -> list of page-aware text chunks."""
    pages = extract_pages(file_path)
    if not pages:
        raise ValueError(
            f"No extractable text found in '{source_name}'. "
            "The PDF may be scanned/image-only and would need OCR first."
        )
    return chunk_pages(pages, source_name, chunk_size, chunk_overlap)
