"""
Extraction orchestrator: primary parser -> confidence check -> Textract fallback.

Implements the "never silently accept obviously malformed extraction" rule
from spec section 6 by scoring what came out of the primary parser before
deciding whether Textract is needed.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..schema import ConfidenceLevel
from .pdf_parser import ExtractedDocument, extract_pdf
from .textract_fallback import TextractResult, analyze_with_textract, textract_available

REQUIRED_SIGNALS = ["scheme", "holding", "sector", "%"]  # crude "did we get real content" check


@dataclass
class ExtractionOutcome:
    document_id: str
    primary: ExtractedDocument
    used_fallback: bool
    fallback: TextractResult | None
    confidence: ConfidenceLevel
    notes: list[str]



def score_confidence(doc: ExtractedDocument) -> ConfidenceLevel:
    if doc.parse_error:
        return ConfidenceLevel.LOW

    text = doc.full_text.lower().strip()
    if not text:
        return ConfidenceLevel.LOW

    # Check for evidence of actual portfolio data, not just generic words.
    has_scheme_context = "scheme" in text
    has_holding_context = any(
        term in text
        for term in ["equity holding", "portfolio", "top 10 holdings"]
    )
    has_sector_context = any(
        term in text
        for term in ["sector allocation", "industry allocation", "sector-wise"]
    )
    has_percentage = "%" in text

    # Count actual extracted table rows, rather than all text blocks.
    table_count = sum(
        len(page.tables)
        for page in doc.pages
    )

    signals = sum([
        has_scheme_context,
        has_holding_context,
        has_sector_context,
        has_percentage,
    ])

    if signals >= 3 and table_count > 0:
        return ConfidenceLevel.HIGH

    if signals >= 2:
        return ConfidenceLevel.MEDIUM

    return ConfidenceLevel.LOW


def extract_with_fallback(
    path: str,
    document_id: str,
    s3_bucket: str | None = None,
    s3_key: str | None = None,
) -> ExtractionOutcome:
    primary = extract_pdf(path, document_id)
    confidence = score_confidence(primary)
    notes: list[str] = []
    used_fallback = False
    fallback: TextractResult | None = None

    needs_fallback = confidence in (ConfidenceLevel.LOW,) or primary.parse_error is not None
    if needs_fallback:
        notes.append(
            "Primary parser produced low-confidence or no output; attempting Textract fallback."
        )
        if not textract_available():
            notes.append("Textract is not available in this environment; flagging for manual verification.")
            confidence = ConfidenceLevel.MANUAL_VERIFICATION_REQUIRED
        elif not (s3_bucket and s3_key):
            notes.append("No S3 location provided for Textract; flagging for manual verification.")
            confidence = ConfidenceLevel.MANUAL_VERIFICATION_REQUIRED
        else:
            used_fallback = True
            fallback = analyze_with_textract(s3_bucket, s3_key, document_id)
            if fallback.error:
                notes.append(f"Textract fallback failed: {fallback.error}")
                confidence = ConfidenceLevel.MANUAL_VERIFICATION_REQUIRED
            else:
                confidence = ConfidenceLevel.MEDIUM
                notes.append("Textract fallback succeeded; treat extracted values as medium confidence.")

    return ExtractionOutcome(
        document_id=document_id,
        primary=primary,
        used_fallback=used_fallback,
        fallback=fallback,
        confidence=confidence,
        notes=notes,
    )
