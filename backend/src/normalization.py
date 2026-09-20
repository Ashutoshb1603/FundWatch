"""
Normalization layer (spec section 8).

Converts raw extraction output (text/tables from pdfplumber, or lines from
Textract) into the common FundSnapshot schema. This is where per-AMC layout
differences get absorbed, so the comparison engine never has to know or
care what the original document looked like.

NOTE: real-world factsheets vary hugely in table layout across AMCs. The
table parsers below cover the common "Company | Sector | % of NAV" and
"Sector | % of NAV" shapes. For anything it can't confidently parse it
leaves the field as None and records a warning rather than guessing.
"""
from __future__ import annotations

import re
from datetime import datetime

from .extraction.extractor import ExtractionOutcome
from .extraction.pdf_parser import find_field
from .schema import (
    ConfidenceLevel,
    FundMeta,
    FundSnapshot,
    Holding,
    SectorAllocation,
    SourceRef,
)

_MONTHS = {
    m.lower(): i
    for i, m in enumerate(
        [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December",
        ],
        start=1,
    )
}


def _period_sort_key(period_text: str | None) -> str | None:
    if not period_text:
        return None
    m = re.search(r"([A-Za-z]+)\s+(\d{4})", period_text)
    if not m:
        return None
    month_name, year = m.group(1).lower(), m.group(2)
    month_num = _MONTHS.get(month_name)
    if not month_num:
        return None
    return f"{year}-{month_num:02d}"


def _find_period(text: str) -> str | None:
    month_alt = "|".join(_MONTHS)
    patterns = [
        rf"(?:as on|as of|factsheet[- ]?|monthly factsheet\D{{0,10}})\D{{0,10}}\b({month_alt})\s+(\d{{4}})\b",
        rf"\b({month_alt})\s+(\d{{4}})\b",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return f"{m.group(1).title()} {m.group(2)}"
    return None


def _find_scheme_name(text: str) -> str | None:
    m = re.search(r"([A-Z][A-Za-z&,'\- ]{4,60}Fund)\b", text)
    return m.group(1).strip() if m else None


def _find_amc(text: str) -> str | None:
    m = re.search(r"([A-Z][A-Za-z& ]{2,40}(?:Mutual Fund|Asset Management|AMC))", text)
    return m.group(1).strip() if m else None


def _find_plan_option(text: str) -> tuple[str | None, str | None]:
    plan = None
    option = None
    m = re.search(r"\b(Direct|Regular)\s*Plan\b", text, re.IGNORECASE)
    if m:
        plan = m.group(1).title()
    m = re.search(r"\b(Growth|IDCW|Dividend)\b", text, re.IGNORECASE)
    if m:
        option = m.group(1).title()
    return plan, option


def _find_fund_managers(text: str) -> list[str]:
    m = re.search(
        r"Fund Manager[s]?\b(.*?)(?=DATE OF ALLOTMENT|INCEPTION DATE|NAV\b|ASSETS UNDER MANAGEMENT|PORTFOLIO|SECTOR ALLOCATION|QUANTITATIVE DATA)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if not m:
        return []
    block = m.group(1)
    names: list[str] = []
    for raw_line in block.splitlines():
        line = " ".join(raw_line.split()).strip(" :-")
        if not line or re.search(r"^(Name|Since|Total Exp|Manager)$", line, re.IGNORECASE):
            continue
        line = re.sub(r"\([^)]*\)", "", line).strip()
        line = re.sub(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\b.*$", "", line, flags=re.IGNORECASE).strip()
        line = re.sub(r"^\d{1,2},?\s*\d{4}.*$", "", line).strip()
        line = re.sub(r"\bOver\s+\d+\s+years?.*$", "", line, flags=re.IGNORECASE).strip()
        chunks = [c.strip() for c in re.split(r",|\band\b", line) if c.strip()]
        for chunk in chunks:
            if 2 <= len(chunk.split()) <= 5 and re.fullmatch(r"[A-Za-z. '&-]+", chunk):
                if chunk.lower() not in {n.lower() for n in names}:
                    names.append(chunk)
    return names[:4]


def _parse_holdings_table(table: list[list[str | None]]) -> list[tuple[str, float | None, str | None]]:
    """Parse common Company/Instrument + Industry/Sector + % NAV tables."""
    if not table or len(table) < 2:
        return []
    header = [c.lower() if c else "" for c in table[0]]
    name_idx = next((i for i, h in enumerate(header) if "company" in h or "holding" in h or "instrument" in h), 0)
    industry_idx = next((i for i, h in enumerate(header) if "industry" in h or "sector" in h), None)
    weight_idx = next((i for i, h in enumerate(header) if "%" in h or "nav" in h or "weight" in h), None)
    if weight_idx is None:
        weight_idx = len(header) - 1

    out: list[tuple[str, float | None, str | None]] = []
    for row in table[1:]:
        if not row or name_idx >= len(row) or not row[name_idx]:
            continue
        name = str(row[name_idx]).strip()
        if not name or name.lower() in ("total", "grand total", "cash & other net current assets"):
            continue
        weight = None
        if weight_idx < len(row) and row[weight_idx]:
            wm = re.search(r"[\d.]+", str(row[weight_idx]))
            if wm:
                try:
                    weight = float(wm.group())
                except ValueError:
                    weight = None
        industry = None
        if industry_idx is not None and industry_idx < len(row) and row[industry_idx]:
            industry = str(row[industry_idx]).strip()
        out.append((name, weight, industry))
    return out


def _parse_sector_table(table: list[list[str | None]]) -> list[tuple[str, float | None]]:
    if not table or len(table) < 2:
        return []
    header = [c.lower() if c else "" for c in table[0]]
    name_idx = next((i for i, h in enumerate(header) if "sector" in h or "industry" in h), 0)
    weight_idx = next((i for i, h in enumerate(header) if "%" in h or "nav" in h or "weight" in h), None)
    if weight_idx is None:
        weight_idx = len(header) - 1

    out: list[tuple[str, float | None]] = []
    for row in table[1:]:
        if not row or name_idx >= len(row) or not row[name_idx]:
            continue
        name = str(row[name_idx]).strip()
        if not name or name.lower() in ("total", "grand total"):
            continue
        weight = None
        if weight_idx < len(row) and row[weight_idx]:
            wm = re.search(r"[\d.]+", str(row[weight_idx]))
            if wm:
                try:
                    weight = float(wm.group())
                except ValueError:
                    weight = None
        out.append((name, weight))
    return out


def _snippet(text: str, needle: str | None, radius: int = 120) -> str | None:
    if not needle:
        return None
    idx = text.lower().find(needle.lower())
    if idx < 0:
        return None
    start = max(0, idx - radius)
    end = min(len(text), idx + len(needle) + radius)
    return " ".join(text[start:end].split())


def _focus_document(doc, scheme_name_hint: str | None):
    """Focus a multi-scheme factsheet on the actual scheme section.

    A scheme name can appear later inside another scheme's portfolio
    (for example, one fund-of-fund may hold units of the target fund).
    Therefore, don't select a page merely because the scheme name appears.

    Prefer pages where the scheme name appears together with strong
    section-level signals such as:
      - CATEGORY OF SCHEME
      - INVESTMENT OBJECTIVE
      - FUND MANAGER
      - ASSETS UNDER MANAGEMENT
      - PORTFOLIO

    Keep original page numbers for evidence.
    """
    if not scheme_name_hint:
        return doc

    hint = " ".join(scheme_name_hint.lower().split())
    candidates = []

    for i, page in enumerate(doc.pages):
        text = " ".join(page.text.lower().split())

        if hint not in text:
            continue

        score = 0

        # Strong evidence that this is the scheme's own section.
        # These are much stronger than simply finding the scheme name.
        if "category of scheme" in text:
            score += 12

        if "investment objective" in text:
            score += 10

        if "fund manager" in text:
            score += 8

        if "assets under management" in text:
            score += 8

        if "portfolio" in text:
            score += 6

        if "nav" in text:
            score += 2

        # The scheme name appearing in the first part of the page is
        # more likely to be the page heading than appearing in a
        # later portfolio row.
        position = text.find(hint)
        if position >= 0 and position < 1200:
            score += 8

        # Penalize pages that look like another scheme's portfolio
        # merely mentioning our target fund as an investment.
        if "mutual fund units" in text and "category of scheme" not in text:
            score -= 10

        if "fund of fund" in text and "category of scheme" not in text:
            score -= 8

        candidates.append((score, i))

    if not candidates:
        return doc

    # Highest-confidence candidate; for ties choose the earliest page.
    _, start = max(candidates, key=lambda item: (item[0], -item[1]))

    # Keep a small window because scheme information commonly spans
    # multiple pages (summary → portfolio → industry allocation).
    window_start = max(0, start - 1)
    window_end = min(len(doc.pages), start + 4)

    focused = type(doc)(
        document_id=doc.document_id,
        pages=doc.pages[window_start:window_end],
        parser_used=doc.parser_used,
        parse_error=doc.parse_error,
    )

    return focused

def _find_aum(text: str) -> str | None:
    patterns = [
        r"As\s+on\s+[A-Za-z]+\s+\d{1,2},?\s+\d{4}.{0,120}?₹?\s*([\d,]+(?:\.\d+)?)\s*Cr",
        r"(?:AUM|Assets?\s+Under\s+Management)\D{0,40}?₹?\s*([\d,]+(?:\.\d+)?)\s*(?:Cr|Crore)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1)
    return None


def _find_expense_ratio(text: str) -> str | None:
    patterns = [
        r"(?:Total\s+Expense\s+Ratio|Expense\s+Ratio|TER).*?Direct\s*[:\-]\s*([\d]+(?:\.\d+)?)\s*%",
        r"(?:Total\s+Expense\s+Ratio|Expense\s+Ratio|TER)\D{0,60}?([\d]+(?:\.\d+)?)\s*%",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1)
    return None


def _find_riskometer(text: str) -> str | None:
    patterns = [
        r"(?:Riskometer|Risk-o-meter)\s*(?:as\s+on[^\n]*)?[\s:\-]+(Very\s+High|Moderately\s+High|Low\s+to\s+Moderate|Moderate|Low|High)",
        r"(?:Current\s+risk[^\n]*?Riskometer)[\s:\-]+(Very\s+High|Moderately\s+High|Low\s+to\s+Moderate|Moderate|Low|High)",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if m:
            return m.group(1)
    return None


def normalize(outcome: ExtractionOutcome, scheme_name_hint: str | None = None) -> FundSnapshot:
    doc = _focus_document(outcome.primary, scheme_name_hint)
    text = doc.full_text
    warnings: list[str] = list(outcome.notes)

    period_text = _find_period(text)
    fund = FundMeta(
        amc=_find_amc(text),
        scheme_name=scheme_name_hint or _find_scheme_name(text),
        isin=find_field(text, "isin"),
        period=period_text,
        period_sort_key=_period_sort_key(period_text),
    )
    fund.plan, fund.option = _find_plan_option(text)
    if not fund.scheme_name:
        warnings.append("Could not confidently detect scheme name.")
    if not fund.period:
        warnings.append("Could not confidently detect reporting period.")

    snapshot = FundSnapshot(
        document_id=outcome.document_id,
        fund=fund,
        extraction_confidence=outcome.confidence,
        warnings=warnings,
    )

    aum_raw = _find_aum(text) or find_field(text, "aum_cr")
    if aum_raw:
        try:
            snapshot.aum_cr = float(aum_raw.replace(",", ""))
            page = doc.find_page_for("AUM") or doc.find_page_for("Assets Under Management")
            snapshot.aum_source = SourceRef(
                document_id=outcome.document_id, page_number=page, confidence=outcome.confidence, raw_snippet=_snippet(text, "Assets Under Management")
            )
        except ValueError:
            pass

    er_raw = _find_expense_ratio(text) or find_field(text, "expense_ratio")
    if er_raw:
        try:
            snapshot.expense_ratio = float(er_raw)
            page = doc.find_page_for("Expense Ratio") or doc.find_page_for("TER")
            snapshot.expense_ratio_source = SourceRef(
                document_id=outcome.document_id, page_number=page, confidence=outcome.confidence, raw_snippet=_snippet(text, "Expense Ratio")
            )
        except ValueError:
            pass

    risk_raw = _find_riskometer(text) or find_field(text, "riskometer")
    if risk_raw:
        snapshot.riskometer = risk_raw.title()
        page = doc.find_page_for("Riskometer")
        snapshot.riskometer_source = SourceRef(
            document_id=outcome.document_id, page_number=page, confidence=outcome.confidence, raw_snippet=_snippet(text, "Riskometer")
        )

    managers = _find_fund_managers(text)
    if managers:
        snapshot.fund_managers = managers
        page = doc.find_page_for("Fund Manager")
        snapshot.fund_managers_source = SourceRef(
            document_id=outcome.document_id, page_number=page, confidence=outcome.confidence, raw_snippet=_snippet(text, "Fund Manager")
        )

    for page in doc.pages:
        for table in page.tables:
            header_text = " ".join(str(c) for c in (table[0] if table else []) if c).lower()
            if any(k in header_text for k in ("company", "holding", "instrument")):
                for name, weight, industry in _parse_holdings_table(table):
                    snapshot.holdings.append(
                        Holding(
                            company=name,
                            weight=weight,
                            sector=industry,
                            source=SourceRef(
                                document_id=outcome.document_id,
                                page_number=page.page_number,
                                extraction_method="table",
                                confidence=outcome.confidence,
                                raw_snippet=" | ".join(str(c) for c in next((r for r in table[1:] if r and name in " ".join(str(x or "") for x in r)), [])),
                            ),
                        )
                    )
            elif any(k in header_text for k in ("sector", "industry")):
                for name, weight in _parse_sector_table(table):
                    snapshot.sectors.append(
                        SectorAllocation(
                            sector=name,
                            weight=weight,
                            source=SourceRef(
                                document_id=outcome.document_id,
                                page_number=page.page_number,
                                extraction_method="table",
                                confidence=outcome.confidence,
                                raw_snippet=" | ".join(str(c) for c in next((r for r in table[1:] if r and name in " ".join(str(x or "") for x in r)), [])),
                            ),
                        )
                    )

    if not snapshot.sectors and snapshot.holdings:
        # Some AMCs publish industry/sector allocation as a chart rather than a
        # machine-readable table. Aggregate the extracted holding industries as
        # a transparent proxy instead of dropping the category.
        aggregate: dict[str, float] = {}
        for h in snapshot.holdings:
            if h.sector and h.weight is not None:
                aggregate[h.sector] = aggregate.get(h.sector, 0.0) + h.weight
        for sector_name, weight in sorted(aggregate.items()):
            snapshot.sectors.append(
                SectorAllocation(
                    sector=sector_name,
                    weight=round(weight, 4),
                    source=SourceRef(
                        document_id=outcome.document_id,
                        page_number=(snapshot.holdings[0].source.page_number if snapshot.holdings and snapshot.holdings[0].source else None),
                        extraction_method="table",
                        confidence=outcome.confidence,
                        raw_snippet=f"Aggregated from extracted holding industries: {sector_name}",
                    ),
                )
            )
        if snapshot.sectors:
            snapshot.warnings.append("Sector allocation was aggregated from holding-level industry labels because no sector table was detected.")

    if not snapshot.holdings:
        snapshot.warnings.append("No holdings table detected — portfolio comparison will be empty.")
    if not snapshot.sectors:
        snapshot.warnings.append("No sector-allocation table detected — sector comparison will be empty.")

    return snapshot
