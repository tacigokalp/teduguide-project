"""Shared helpers for reading the TEDU wayfinding PDFs with PyMuPDF
(used by inspect_pdf.py, pdf_to_svg.py and extract_rooms.py).

Page layout (every page, A3 landscape 1683.78 x 1190.55 pt, origin top-left, y grows DOWN):
    title bar            y < ~130
    floor plan           y ~ 140 ... legend frame (the QR block sits bottom-left of it)
    "Scan QR Code" + QR  bottom-left, just above the legend frame
    legend frame         wide box starting ~35 pt above the "YER-YÖN LEJANTI | WAYFINDING LEGEND" heading

The walls of the plan are an embedded raster image, not vector lines. Only the numbered
marker circles and all text are real vector data.

Needs: pip install pymupdf
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import pymupdf

HEADER_BOTTOM = 130.0
QR_RIGHT_PT = 490.0  # the "Scan QR Code ..." block sits bottom-left, left of this x
MARKER_RE = re.compile(r"^\d{1,2}(\.\d)?$")  # "13" or "13.1"


@dataclass
class PageLayout:
    title: str
    level: int | None
    qr_top: float  # first y of the QR block
    legend_top: float  # first y of the legend text
    legend_box_top: float  # top border of the legend frame
    words: list[dict]


def open_pdf(path: str) -> pymupdf.Document:
    return pymupdf.open(path)


def page_words(page: pymupdf.Page) -> list[dict]:
    """Every word with its box and centre. y grows down (PyMuPDF's default)."""
    words = []
    for x0, y0, x1, y1, text, *_ in page.get_text("words"):
        words.append({
            "text": text, "x0": x0, "x1": x1, "top": y0, "bottom": y1,
            "x": (x0 + x1) / 2, "y": (y0 + y1) / 2,
        })
    words.sort(key=lambda w: (round(w["top"]), w["x0"]))
    return words


def parse_level(title: str) -> int | None:
    t = title.upper()
    if "ZEM" in t:
        return 0
    if "ÇATI" in t or "CATI" in t or "ROOF" in t:
        return 5  # decision K6
    m = re.search(r"(-?\d)\s*\.\s*KAT", t)
    return int(m.group(1)) if m else None


def layout(page: pymupdf.Page) -> PageLayout:
    words = page_words(page)
    title = " ".join(w["text"] for w in words if w["top"] < HEADER_BOTTOM)
    legend_top = next((w["top"] - 5 for w in words if w["text"].upper().startswith("LEJANT")), page.rect.height)
    qr_top = legend_top
    for i, w in enumerate(words):
        if w["text"] == "Scan" and i + 1 < len(words) and words[i + 1]["text"] == "QR":
            qr_top = w["top"] - 40  # the QR image starts a little above its caption
            break
    frames = [
        d["rect"].y0 for d in page.get_drawings()
        if d["rect"].width > 1000 and qr_top - 60 < d["rect"].y0 < legend_top
    ]
    legend_box_top = min(frames) if frames else legend_top - 40
    return PageLayout(title=title, level=parse_level(title), qr_top=qr_top, legend_top=legend_top,
                      legend_box_top=legend_box_top, words=words)
