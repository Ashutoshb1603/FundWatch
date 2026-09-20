"""
Analyst brief generation (spec section 11).

Deterministic skeleton is always built first (fund, periods, ranked
findings, evidence) so the brief exists and is fully correct even if
Bedrock is down. If Bedrock is available, its narrative text is attached
on top — it never replaces the structured, evidence-linked data.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .bedrock.client import generate_brief
from .schema import Finding, FundSnapshot


@dataclass
class AnalystBrief:
    scheme_name: str | None
    previous_period: str | None
    current_period: str | None
    ranked_findings: list[dict]
    narrative: str | None
    narrative_available: bool
    caveat: str = (
        "This brief distinguishes observed disclosure changes (deterministically "
        "calculated from the two factsheets) from narrative interpretation. It does "
        "not constitute investment advice and makes no claim about future performance."
    )

    def to_dict(self) -> dict:
        return {
            "scheme_name": self.scheme_name,
            "previous_period": self.previous_period,
            "current_period": self.current_period,
            "key_changes": self.ranked_findings,
            "narrative": self.narrative,
            "narrative_available": self.narrative_available,
            "caveat": self.caveat,
        }


def build_brief(
    previous: FundSnapshot, current: FundSnapshot, findings: list[Finding], use_bedrock: bool = True
) -> AnalystBrief:
    ranked = [f.to_dict() for f in findings]
    scheme_name = current.fund.scheme_name or previous.fund.scheme_name

    narrative = None
    narrative_available = False
    if use_bedrock and ranked:
        resp = generate_brief(
            scheme_name=scheme_name,
            previous_period=previous.fund.period,
            current_period=current.fund.period,
            findings=ranked,
        )
        if resp.available and resp.text:
            narrative = resp.text
            narrative_available = True

    return AnalystBrief(
        scheme_name=scheme_name,
        previous_period=previous.fund.period,
        current_period=current.fund.period,
        ranked_findings=ranked,
        narrative=narrative,
        narrative_available=narrative_available,
    )
