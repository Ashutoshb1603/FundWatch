"""
FundWatch normalized internal schema.

Every supported factsheet (regardless of AMC or original layout) is converted
into these dataclasses before comparison. Keeping both periods in this same
shape is what lets the comparison engine stay deterministic and simple.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MANUAL_VERIFICATION_REQUIRED = "manual_verification_required"


@dataclass
class SourceRef:
    """Pointer back to the exact place a value came from in the source PDF."""
    document_id: str
    page_number: Optional[int] = None
    extraction_method: str = "text"  # "text" | "table" | "textract"
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    raw_snippet: Optional[str] = None  # short excerpt used to locate the value


@dataclass
class Holding:
    company: str
    weight: Optional[float]  # % of NAV
    source: Optional[SourceRef] = None
    isin: Optional[str] = None
    sector: Optional[str] = None


@dataclass
class SectorAllocation:
    sector: str
    weight: Optional[float]  # % of NAV
    source: Optional[SourceRef] = None


@dataclass
class FundMeta:
    amc: Optional[str] = None
    scheme_name: Optional[str] = None
    plan: Optional[str] = None
    option: Optional[str] = None
    isin: Optional[str] = None
    period: Optional[str] = None  # e.g. "August 2026"
    period_sort_key: Optional[str] = None  # "2026-08" for ordering/consecutiveness checks


@dataclass
class FundSnapshot:
    """One normalized factsheet, ready for comparison against another period."""
    document_id: str
    fund: FundMeta = field(default_factory=FundMeta)
    aum_cr: Optional[float] = None  # AUM in crores
    aum_source: Optional[SourceRef] = None
    expense_ratio: Optional[float] = None  # percent
    expense_ratio_source: Optional[SourceRef] = None
    riskometer: Optional[str] = None
    riskometer_source: Optional[SourceRef] = None
    fund_managers: list[str] = field(default_factory=list)
    fund_managers_source: Optional[SourceRef] = None
    holdings: list[Holding] = field(default_factory=list)
    sectors: list[SectorAllocation] = field(default_factory=list)
    extraction_confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    warnings: list[str] = field(default_factory=list)


class Priority(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ChangeType(str, Enum):
    HOLDING_NEW = "holding_new"
    HOLDING_EXITED = "holding_exited"
    HOLDING_WEIGHT_CHANGE = "holding_weight_change"
    SECTOR_WEIGHT_CHANGE = "sector_weight_change"
    AUM_CHANGE = "aum_change"
    EXPENSE_RATIO_CHANGE = "expense_ratio_change"
    RISKOMETER_CHANGE = "riskometer_change"
    FUND_MANAGER_CHANGE = "fund_manager_change"
    TOP10_ENTRY = "top10_entry"
    TOP10_EXIT = "top10_exit"


@dataclass
class Finding:
    """A single, machine-readable detected change. This is what both the UI
    and Bedrock consume — Bedrock never sees raw documents, only these."""
    change_type: ChangeType
    label: str  # human-readable subject, e.g. "Financial Services" or "Reliance Industries"
    previous_value: Optional[float | str]
    current_value: Optional[float | str]
    absolute_difference: Optional[float] = None
    percentage_point_difference: Optional[float] = None
    priority: Priority = Priority.LOW
    rule_triggered: Optional[str] = None
    previous_source: Optional[SourceRef] = None
    current_source: Optional[SourceRef] = None
    explanation: Optional[str] = None  # filled in later by Bedrock, or left None

    def to_dict(self) -> dict:
        d = {
            "change_type": self.change_type.value,
            "label": self.label,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "absolute_difference": self.absolute_difference,
            "percentage_point_difference": self.percentage_point_difference,
            "priority": self.priority.value,
            "rule_triggered": self.rule_triggered,
            "explanation": self.explanation,
        }
        if self.previous_source:
            d["previous_evidence"] = {
                "document_id": self.previous_source.document_id,
                "page_number": self.previous_source.page_number,
                "confidence": self.previous_source.confidence.value,
                "extraction_method": self.previous_source.extraction_method,
                "raw_snippet": self.previous_source.raw_snippet,
            }
        if self.current_source:
            d["current_evidence"] = {
                "document_id": self.current_source.document_id,
                "page_number": self.current_source.page_number,
                "confidence": self.current_source.confidence.value,
                "extraction_method": self.current_source.extraction_method,
                "raw_snippet": self.current_source.raw_snippet,
            }
        return d


@dataclass
class ValidationResult:
    same_fund: bool
    comparable_periods: bool
    periods_consecutive: Optional[bool]
    issues: list[str] = field(default_factory=list)

    @property
    def can_proceed(self) -> bool:
        return self.same_fund and self.comparable_periods
