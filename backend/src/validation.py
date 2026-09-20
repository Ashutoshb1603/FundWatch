"""
Document/fund identity validation (spec section 7).

Runs BEFORE comparison. If the two factsheets don't look like the same
scheme, or the periods don't make sense to compare, we stop rather than
silently comparing apples to oranges.
"""
from __future__ import annotations

from difflib import SequenceMatcher

from .schema import FundSnapshot, ValidationResult

NAME_SIMILARITY_THRESHOLD = 0.85


def _normalize_name(name: str | None) -> str:
    if not name:
        return ""
    return " ".join(name.lower().replace("-", " ").split())


def _similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def validate_same_fund(previous: FundSnapshot, current: FundSnapshot) -> ValidationResult:
    issues: list[str] = []

    prev_isin = previous.fund.isin
    curr_isin = current.fund.isin
    same_fund = True

    if prev_isin and curr_isin:
        same_fund = prev_isin.strip().upper() == curr_isin.strip().upper()
        if not same_fund:
            issues.append(
                f"ISIN mismatch: previous document is {prev_isin}, current is {curr_isin}."
            )
    else:
        # Fall back to fuzzy name + AMC matching when ISIN isn't available in either doc.
        name_sim = _similar(
            _normalize_name(previous.fund.scheme_name), _normalize_name(current.fund.scheme_name)
        )
        amc_sim = _similar(_normalize_name(previous.fund.amc), _normalize_name(current.fund.amc))
        same_fund = name_sim >= NAME_SIMILARITY_THRESHOLD and (
            amc_sim >= NAME_SIMILARITY_THRESHOLD or not previous.fund.amc or not current.fund.amc
        )
        if not same_fund:
            issues.append(
                "Scheme name / AMC do not appear to match closely enough to be confident "
                "these are the same fund. No ISIN was available in one or both documents "
                "to confirm directly."
            )

    if previous.fund.plan and current.fund.plan and previous.fund.plan.lower() != current.fund.plan.lower():
        issues.append(
            f"Plan differs: previous is '{previous.fund.plan}', current is '{current.fund.plan}'. "
            "Comparing across plans (e.g. Direct vs Regular) can distort expense-ratio and AUM findings."
        )
    if (
        previous.fund.option
        and current.fund.option
        and previous.fund.option.lower() != current.fund.option.lower()
    ):
        issues.append(
            f"Option differs: previous is '{previous.fund.option}', current is '{current.fund.option}'."
        )

    comparable_periods = True
    periods_consecutive: bool | None = None
    prev_key = previous.fund.period_sort_key
    curr_key = current.fund.period_sort_key

    if not prev_key or not curr_key:
        issues.append(
            "Could not confidently determine the reporting period for one or both documents; "
            "consecutiveness could not be verified."
        )
    elif prev_key == curr_key:
        comparable_periods = False
        issues.append("Both documents appear to report the same period.")
    elif prev_key > curr_key:
        comparable_periods = False
        issues.append(
            f"Document order looks reversed: '{previous.fund.period}' is after '{current.fund.period}'."
        )
    else:
        periods_consecutive = _is_consecutive_month(prev_key, curr_key)
        if not periods_consecutive:
            issues.append(
                f"Periods are not consecutive months ({previous.fund.period} -> {current.fund.period}). "
                "The comparison will still run, but changes may reflect several months of drift."
            )

    return ValidationResult(
        same_fund=same_fund,
        comparable_periods=comparable_periods,
        periods_consecutive=periods_consecutive,
        issues=issues,
    )


def _is_consecutive_month(prev_key: str, curr_key: str) -> bool:
    try:
        py, pm = (int(x) for x in prev_key.split("-"))
        cy, cm = (int(x) for x in curr_key.split("-"))
    except ValueError:
        return False
    months_diff = (cy - py) * 12 + (cm - pm)
    return months_diff == 1
