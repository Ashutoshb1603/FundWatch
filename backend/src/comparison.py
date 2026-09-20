"""
Deterministic comparison engine (spec section 9).

No LLM involved anywhere in this file. Every number here is calculated in
plain Python from the two normalized FundSnapshots. This is the source of
truth; Bedrock is only ever allowed to explain what this module already found.
"""
from __future__ import annotations

from .materiality import DEFAULT_CONFIG, MaterialityConfig, priority_for
from .schema import ChangeType, Finding, FundSnapshot, Holding, SectorAllocation

TOP_N = 10


def _top_n_names(holdings: list[Holding], n: int = TOP_N) -> set[str]:
    ranked = sorted((h for h in holdings if h.weight is not None), key=lambda h: h.weight, reverse=True)
    return {h.company.strip().lower() for h in ranked[:n]}


def _index_by_name(items: list, name_attr: str) -> dict:
    return {getattr(i, name_attr).strip().lower(): i for i in items if getattr(i, name_attr)}


def compare_holdings(
    previous: FundSnapshot, current: FundSnapshot, config: MaterialityConfig = DEFAULT_CONFIG
) -> list[Finding]:
    findings: list[Finding] = []

    prev_by_name = _index_by_name(previous.holdings, "company")
    curr_by_name = _index_by_name(current.holdings, "company")
    prev_top10 = _top_n_names(previous.holdings)
    curr_top10 = _top_n_names(current.holdings)

    all_names = set(prev_by_name) | set(curr_by_name)

    for name in sorted(all_names):
        prev_h = prev_by_name.get(name)
        curr_h = curr_by_name.get(name)

        if prev_h is None and curr_h is not None:
            if curr_h.weight is None:
                continue 
            findings.append(
                Finding(
                    change_type=ChangeType.HOLDING_NEW,
                    label=curr_h.company,
                    previous_value=None,
                    current_value=curr_h.weight,
                    priority=priority_for(ChangeType.HOLDING_NEW, config),
                    rule_triggered="new_holding",
                    current_source=curr_h.source,
                )
            )
            if name in curr_top10 and config.top10_entry_exit_always_flagged:
                findings.append(
                    Finding(
                        change_type=ChangeType.TOP10_ENTRY,
                        label=curr_h.company,
                        previous_value=None,
                        current_value=curr_h.weight,
                        priority=priority_for(ChangeType.TOP10_ENTRY, config),
                        rule_triggered="entered_top_10",
                        current_source=curr_h.source,
                    )
                )
            continue

        if curr_h is None and prev_h is not None:
            if prev_h.weight is None:
                continue 
            findings.append(
                Finding(
                    change_type=ChangeType.HOLDING_EXITED,
                    label=prev_h.company,
                    previous_value=prev_h.weight,
                    current_value=None,
                    priority=priority_for(ChangeType.HOLDING_EXITED, config),
                    rule_triggered="holding_exited",
                    previous_source=prev_h.source,
                )
            )
            if name in prev_top10 and config.top10_entry_exit_always_flagged:
                findings.append(
                    Finding(
                        change_type=ChangeType.TOP10_EXIT,
                        label=prev_h.company,
                        previous_value=prev_h.weight,
                        current_value=None,
                        priority=priority_for(ChangeType.TOP10_EXIT, config),
                        rule_triggered="exited_top_10",
                        previous_source=prev_h.source,
                    )
                )
            continue

        # present in both periods
        if prev_h.weight is None or curr_h.weight is None:
            continue
        diff = round(curr_h.weight - prev_h.weight, 4)
        if abs(diff) >= config.holding_weight_pp_threshold:
            findings.append(
                Finding(
                    change_type=ChangeType.HOLDING_WEIGHT_CHANGE,
                    label=curr_h.company,
                    previous_value=prev_h.weight,
                    current_value=curr_h.weight,
                    absolute_difference=diff,
                    percentage_point_difference=diff,
                    priority=priority_for(ChangeType.HOLDING_WEIGHT_CHANGE, config),
                    rule_triggered=f"weight_change_>=_{config.holding_weight_pp_threshold}pp",
                    previous_source=prev_h.source,
                    current_source=curr_h.source,
                )
            )
        if name in prev_top10 and name not in curr_top10 and config.top10_entry_exit_always_flagged:
            findings.append(
                Finding(
                    change_type=ChangeType.TOP10_EXIT,
                    label=curr_h.company,
                    previous_value=prev_h.weight,
                    current_value=curr_h.weight,
                    priority=priority_for(ChangeType.TOP10_EXIT, config),
                    rule_triggered="dropped_out_of_top_10",
                    previous_source=prev_h.source,
                    current_source=curr_h.source,
                )
            )
        elif name in curr_top10 and name not in prev_top10 and config.top10_entry_exit_always_flagged:
            findings.append(
                Finding(
                    change_type=ChangeType.TOP10_ENTRY,
                    label=curr_h.company,
                    previous_value=prev_h.weight,
                    current_value=curr_h.weight,
                    priority=priority_for(ChangeType.TOP10_ENTRY, config),
                    rule_triggered="entered_top_10",
                    previous_source=prev_h.source,
                    current_source=curr_h.source,
                )
            )

    return findings


def compare_sectors(
    previous: FundSnapshot, current: FundSnapshot, config: MaterialityConfig = DEFAULT_CONFIG
) -> list[Finding]:
    findings: list[Finding] = []
    prev_by_name = _index_by_name(previous.sectors, "sector")
    curr_by_name = _index_by_name(current.sectors, "sector")
    all_names = set(prev_by_name) | set(curr_by_name)

    for name in sorted(all_names):
        prev_s = prev_by_name.get(name)
        curr_s = curr_by_name.get(name)
        prev_w = prev_s.weight if prev_s else None
        curr_w = curr_s.weight if curr_s else None
        if prev_w is None or curr_w is None:
            continue
        diff = round(curr_w - prev_w, 4)
        if abs(diff) >= config.sector_weight_pp_threshold:
            findings.append(
                Finding(
                    change_type=ChangeType.SECTOR_WEIGHT_CHANGE,
                    label=curr_s.sector,
                    previous_value=prev_w,
                    current_value=curr_w,
                    absolute_difference=diff,
                    percentage_point_difference=diff,
                    priority=priority_for(ChangeType.SECTOR_WEIGHT_CHANGE, config),
                    rule_triggered=f"sector_change_>=_{config.sector_weight_pp_threshold}pp",
                    previous_source=prev_s.source,
                    current_source=curr_s.source,
                )
            )
    return findings


def compare_fund_level(
    previous: FundSnapshot, current: FundSnapshot, config: MaterialityConfig = DEFAULT_CONFIG
) -> list[Finding]:
    findings: list[Finding] = []

    if previous.aum_cr is not None and current.aum_cr is not None and previous.aum_cr != 0:
        pct_change = round((current.aum_cr - previous.aum_cr) / previous.aum_cr * 100, 2)
        if abs(pct_change) >= config.aum_pct_threshold:
            findings.append(
                Finding(
                    change_type=ChangeType.AUM_CHANGE,
                    label="AUM",
                    previous_value=previous.aum_cr,
                    current_value=current.aum_cr,
                    absolute_difference=round(current.aum_cr - previous.aum_cr, 2),
                    percentage_point_difference=pct_change,
                    priority=priority_for(ChangeType.AUM_CHANGE, config),
                    rule_triggered=f"aum_change_>=_{config.aum_pct_threshold}pct",
                    previous_source=previous.aum_source,
                    current_source=current.aum_source,
                )
            )

    if (
        config.expense_ratio_any_change
        and previous.expense_ratio is not None
        and current.expense_ratio is not None
        and previous.expense_ratio != current.expense_ratio
    ):
        diff_bps = round((current.expense_ratio - previous.expense_ratio) * 100, 1)
        findings.append(
            Finding(
                change_type=ChangeType.EXPENSE_RATIO_CHANGE,
                label="Expense ratio",
                previous_value=previous.expense_ratio,
                current_value=current.expense_ratio,
                absolute_difference=round(current.expense_ratio - previous.expense_ratio, 4),
                percentage_point_difference=diff_bps,  # reported as bps for this metric
                priority=priority_for(ChangeType.EXPENSE_RATIO_CHANGE, config),
                rule_triggered="expense_ratio_changed",
                previous_source=previous.expense_ratio_source,
                current_source=current.expense_ratio_source,
            )
        )

    if (
        previous.riskometer
        and current.riskometer
        and previous.riskometer.strip().lower() != current.riskometer.strip().lower()
    ):
        findings.append(
            Finding(
                change_type=ChangeType.RISKOMETER_CHANGE,
                label="Riskometer",
                previous_value=previous.riskometer,
                current_value=current.riskometer,
                priority=priority_for(ChangeType.RISKOMETER_CHANGE, config),
                rule_triggered="riskometer_changed",
                previous_source=previous.riskometer_source,
                current_source=current.riskometer_source,
            )
        )

    prev_managers = {m.strip().lower() for m in previous.fund_managers}
    curr_managers = {m.strip().lower() for m in current.fund_managers}
    if previous.fund_managers and current.fund_managers and prev_managers != curr_managers:
        findings.append(
            Finding(
                change_type=ChangeType.FUND_MANAGER_CHANGE,
                label="Fund manager(s)",
                previous_value=", ".join(previous.fund_managers),
                current_value=", ".join(current.fund_managers),
                priority=priority_for(ChangeType.FUND_MANAGER_CHANGE, config),
                rule_triggered="fund_manager_changed",
                previous_source=previous.fund_managers_source,
                current_source=current.fund_managers_source,
            )
        )

    return findings


def compare_snapshots(
    previous: FundSnapshot, current: FundSnapshot, config: MaterialityConfig = DEFAULT_CONFIG
) -> list[Finding]:
    """Run every comparison category and return all material findings,
    ranked by priority (HIGH -> MEDIUM -> LOW), highest-magnitude first
    within a priority tier."""
    findings: list[Finding] = []
    findings.extend(compare_holdings(previous, current, config))
    findings.extend(compare_sectors(previous, current, config))
    findings.extend(compare_fund_level(previous, current, config))

    priority_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

    def sort_key(f: Finding):
        magnitude = abs(f.percentage_point_difference) if f.percentage_point_difference is not None else 0
        return (priority_rank[f.priority.value], -magnitude)

    findings.sort(key=sort_key)
    return findings
