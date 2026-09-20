"""
Primary extraction layer (spec section 6, "first layer").

Uses PyMuPDF (fitz) for text extraction. We moved off pdfplumber here:
on real multi-column factsheet layouts (e.g. combined multi-scheme AMC
books), pdfplumber's extract_text() and extract_tables() were merging
adjacent columns character-by-character and shredding one logical table
into dozens of fragments. PyMuPDF's block-based extraction preserves
column/row structure correctly on the same documents, so holdings are
now parsed from page.get_text("blocks") (see parse_holdings_block below)
rather than from a table-detection API.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None


@dataclass
class PageText:
    page_number: int  # 1-indexed
    text: str
    tables: list[list[list[str | None]]]  # kept for backward compatibility; no longer populated
    blocks: list[str] = field(default_factory=list)  # page's text blocks, in reading order


@dataclass
class ExtractedDocument:
    document_id: str
    pages: list[PageText]
    parser_used: str = "pymupdf"
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
    """Extract text + column-aware blocks per page. Never raises for a
    readable PDF; on failure it returns an ExtractedDocument with
    parse_error set so the caller can fall back to Textract (spec section 6)."""
    if fitz is None:
        

        return ExtractedDocument(
            document_id=document_id, pages=[], parse_error="pymupdf not installed"
        )
    pages: list[PageText] = []
    try:
        doc = fitz.open(path)
        for i, page in enumerate(doc, start=1):
            text = page.get_text()
            raw_blocks = page.get_text("blocks")
            # reading order: row band first (rounds out small y jitter), then left-to-right
            raw_blocks.sort(key=lambda b: (round(b[1] / 5), b[0]))
            block_texts = [b[4] for b in raw_blocks if b[4] and b[4].strip()]
            pages.append(PageText(page_number=i, text=text, tables=[], blocks=block_texts))
        doc.close()
    except Exception as exc:  # noqa: BLE001 - intentionally broad, this is the fallback trigger
        return ExtractedDocument(document_id=document_id, pages=[], parse_error=str(exc))

    if not any(p.text.strip() for p in pages):
        return ExtractedDocument(
            document_id=document_id,
            pages=pages,
            parse_error="No extractable text found (likely a scanned/image PDF).",
        )
    return ExtractedDocument(document_id=document_id, pages=pages)


# ---- Holdings block parser -----------------------------------------------
# Factsheet portfolio tables often have no ruling lines between individual
# holding rows (only column separators), which makes table-detection APIs
# unreliable. Parsing the column's raw text block as a repeating
# "name -> optional multi-line sector -> % NAV" pattern is far more robust.

SECTION_MARKERS = {
    "equity & equity related", "debt & debt related", "money market instruments",
    "units issued by reit", "units issued by invit", "sub total", "total",
    "grand total", "government securities (central/state)", "company/",
    "instrument", "(% age)", "cash,cash equivalents and net current assets",
}


def looks_like_percent(line: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}\.\d{1,2}", line.strip()))


# A company name that wraps onto a second line almost always breaks right
# after one of these tokens (e.g. "SBI Life Insurance Company" / "Ltd."). A
# line that IS one of these tokens, on its own, is a name continuation —
# not the start of the sector text.
_NAME_CONTINUATION_SUFFIXES = re.compile(r"^(Ltd\.?|Limited|LIMTIED|PLC|REIT|InvIT)$", re.IGNORECASE)


def parse_holdings_block(text: str) -> list[tuple[str, str | None, float]]:
    """Parse one column's block text into (name, sector, weight) triples.
    Only emits a holding when a trailing % NAV number was actually found —
    never guesses a name-only or number-only row."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    holdings: list[tuple[str, str | None, float]] = []
    buf: list[str] = []
    for line in lines:
        clean = line.lstrip("•").strip()
        low = clean.lower()
        if low in SECTION_MARKERS or low.startswith("hedged position"):
            buf = []
            continue
        if looks_like_percent(clean):
            if buf:
                if len(buf) >= 2 and _NAME_CONTINUATION_SUFFIXES.match(buf[1]):
                    name = f"{buf[0]} {buf[1]}"
                    sector = " ".join(buf[2:]) or None
                else:
                    name = buf[0]
                    sector = " ".join(buf[1:]) or None
                holdings.append((name, sector, float(clean)))
            buf = []
        else:
            buf.append(clean)
    return holdings


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