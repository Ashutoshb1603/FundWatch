"""
Materiality rules (spec section 4).

These are explicitly PRODUCT rules, not universal financial truths, so they
live in one place as plain data and are easy to retune per-deployment via
env vars or a config file — never hardcoded inside the comparison engine.
"""
from __future__ import annotations

from dataclasses import dataclass

from .schema import ChangeType, Priority


@dataclass
class MaterialityConfig:
    holding_weight_pp_threshold: float = 0.50
    sector_weight_pp_threshold: float = 1.00
    aum_pct_threshold: float = 10.0  # % change in AUM considered "major"
    expense_ratio_any_change: bool = True
    top10_entry_exit_always_flagged: bool = True
    riskometer_change_always_high: bool = True
    fund_manager_change_always_high: bool = True


DEFAULT_CONFIG = MaterialityConfig()


def priority_for(change_type: ChangeType, config: MaterialityConfig = DEFAULT_CONFIG) -> Priority:
    if change_type in (ChangeType.RISKOMETER_CHANGE, ChangeType.FUND_MANAGER_CHANGE):
        return Priority.HIGH
    if change_type in (ChangeType.TOP10_ENTRY, ChangeType.TOP10_EXIT):
        return Priority.HIGH
    if change_type == ChangeType.SECTOR_WEIGHT_CHANGE:
        return Priority.MEDIUM
    if change_type == ChangeType.HOLDING_WEIGHT_CHANGE:
        return Priority.MEDIUM
    if change_type in (ChangeType.HOLDING_NEW, ChangeType.HOLDING_EXITED):
        return Priority.MEDIUM
    if change_type == ChangeType.EXPENSE_RATIO_CHANGE:
        return Priority.LOW
    if change_type == ChangeType.AUM_CHANGE:
        return Priority.MEDIUM
    return Priority.LOW
