"""
Primary extraction layer (spec section 6, "first layer").

Uses pdfplumber for text + table extraction. This is deliberately kept as
plain text/line extraction plus a set of regex-based field finders — real
factsheets from different AMCs are laid out very differently, so treat this
module as the "best effort" layer and lean on extraction_confidence + the
Textract fallback for anything it can't parse cleanly.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

try:
    import pdfplumber
except ImportError:  # pragma: no cover
    pdfplumber = None


@dataclass
class PageText:
    page_number: int  # 1-indexed
    text: str
    tables: list[list[list[str | None]]]


@dataclass
class ExtractedDocument:
    document_id: str
    pages: list[PageText]
    parser_used: str = "pdfplumber"
    parse_error: str | None = None

    @property
    def full_text(self) -> str:
        return "\n".join(p.text for p in self.pages)

    def find_page_for(self, needle: str) -> int | None:
        """Best-effort: first page whose text contains this substring (case-insensitive)."""
        needle_l = needle.lower()
        for p in self.pages:
            if needle_l in p.text.lower():
                return p.page_number
        return None


def extract_pdf(path: str, document_id: str) -> ExtractedDocument:
    """Extract text + tables per page. Never raises for a readable PDF; on
    failure it returns an ExtractedDocument with parse_error set so the
    caller can fall back to Textract (spec section 6)."""
    if pdfplumber is None:
        return ExtractedDocument(
            document_id=document_id, pages=[], parse_error="pdfplumber not installed"
        )
    pages: list[PageText] = []
    try:
        with pdfplumber.open(path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                try:
                    tables = [t for t in (page.extract_tables() or []) if t]
                except Exception:
                    tables = []
                pages.append(PageText(page_number=i, text=text, tables=tables))
    except Exception as exc:  # noqa: BLE001 - intentionally broad, this is the fallback trigger
        return ExtractedDocument(document_id=document_id, pages=[], parse_error=str(exc))

    if not any(p.text.strip() for p in pages):
        return ExtractedDocument(
            document_id=document_id,
            pages=pages,
            parse_error="No extractable text found (likely a scanned/image PDF).",
        )
    return ExtractedDocument(document_id=document_id, pages=pages)


# ---- Lightweight field finders -------------------------------------------------
# These are intentionally simple, regex-based heuristics. They are the kind of
# thing you'd tune per-AMC template in a real product; here they cover common
# phrasing patterns seen across Indian mutual fund factsheets.

_PATTERNS = {
    "aum_cr": re.compile(
        r"(?:AUM|Assets?\s+Under\s+Management)\D{0,20}?(?:Rs\.?|₹|INR)?\s*([\d,]+\.?\d*)\s*(?:Cr|Crore)",
        re.IGNORECASE,
    ),
    "expense_ratio": re.compile(
        r"(?:Total\s+Expense\s+Ratio|Expense\s+Ratio|TER)\D{0,20}?([\d]+\.?\d*)\s*%",
        re.IGNORECASE,
    ),
    "riskometer": re.compile(
        r"Riskometer\D{0,40}?(Low to Moderate|Moderate(?:ly High)?|Low|High|Very High)",
        re.IGNORECASE,
    ),
    "isin": re.compile(r"\bISIN\D{0,10}?([A-Z]{2}[A-Z0-9]{9}\d)\b"),
}


def find_field(full_text: str, field: str) -> str | None:
    pattern = _PATTERNS.get(field)
    if not pattern:
        return None
    m = pattern.search(full_text)
    return m.group(1).strip() if m else None
