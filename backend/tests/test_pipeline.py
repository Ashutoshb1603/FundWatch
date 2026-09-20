"""
Exercises the deterministic core (validation -> comparison -> materiality ->
brief skeleton) end-to-end with synthetic data, with Bedrock disabled (no
AWS credentials in this environment). This is the part of the spec that
must never depend on an LLM, so it's what we test hardest.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.comparison import compare_snapshots
from src.materiality import DEFAULT_CONFIG
from src.brief import build_brief
from src.schema import ChangeType, Priority
from src.validation import validate_same_fund
from tests.sample_data import make_current, make_previous


def test_validation_passes_for_matching_fund():
    prev, curr = make_previous(), make_current()
    result = validate_same_fund(prev, curr)
    assert result.same_fund is True
    assert result.comparable_periods is True
    assert result.periods_consecutive is True
    assert result.can_proceed is True


def test_comparison_detects_expected_changes():
    prev, curr = make_previous(), make_current()
    findings = compare_snapshots(prev, curr, DEFAULT_CONFIG)
    by_type = {}
    for f in findings:
        by_type.setdefault(f.change_type, []).append(f)

    # Reliance weight dropped >= 0.5pp
    reliance = [f for f in by_type.get(ChangeType.HOLDING_WEIGHT_CHANGE, []) if f.label == "Reliance Industries"]
    assert reliance and reliance[0].absolute_difference == -1.5

    # TCS exited entirely
    assert any(f.label == "Tata Consultancy Services" for f in by_type.get(ChangeType.HOLDING_EXITED, []))

    # L&T is a new top-10 entrant
    lnt_new = [f for f in by_type.get(ChangeType.HOLDING_NEW, []) if f.label == "Larsen & Toubro"]
    assert lnt_new
    assert any(f.label == "Larsen & Toubro" for f in by_type.get(ChangeType.TOP10_ENTRY, []))

    # Financial Services sector dropped 3.6pp (>= 1.0pp threshold)
    fin = [f for f in by_type.get(ChangeType.SECTOR_WEIGHT_CHANGE, []) if f.label == "Financial Services"]
    assert fin and round(fin[0].absolute_difference, 1) == -3.6

    # IT sector rose 3.4pp
    it = [f for f in by_type.get(ChangeType.SECTOR_WEIGHT_CHANGE, []) if f.label == "Information Technology"]
    assert it and round(it[0].absolute_difference, 1) == 3.4

    # expense ratio changed (0.72 -> 0.68)
    assert by_type.get(ChangeType.EXPENSE_RATIO_CHANGE)

    # fund manager changed (Vikram Seth added) -> HIGH priority
    mgr = by_type.get(ChangeType.FUND_MANAGER_CHANGE)
    assert mgr and mgr[0].priority == Priority.HIGH

    # riskometer unchanged -> should NOT appear
    assert ChangeType.RISKOMETER_CHANGE not in by_type

    # AUM change is only ~2.4%, below the 10% "major" threshold -> should NOT appear
    assert ChangeType.AUM_CHANGE not in by_type

    # every finding must carry priority + at least one evidence pointer where applicable
    for f in findings:
        assert f.priority in (Priority.HIGH, Priority.MEDIUM, Priority.LOW)


def test_findings_are_ranked_high_priority_first():
    prev, curr = make_previous(), make_current()
    findings = compare_snapshots(prev, curr, DEFAULT_CONFIG)
    priorities = [f.priority for f in findings]
    rank = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
    assert priorities == sorted(priorities, key=lambda p: rank[p])


def test_brief_builds_deterministic_skeleton_without_bedrock():
    prev, curr = make_previous(), make_current()
    findings = compare_snapshots(prev, curr, DEFAULT_CONFIG)
    brief = build_brief(prev, curr, findings, use_bedrock=False)
    assert brief.narrative_available is False
    assert brief.narrative is None
    assert brief.scheme_name == "Example Flexi Cap Fund"
    assert brief.previous_period == "July 2026"
    assert brief.current_period == "August 2026"
    assert len(brief.ranked_findings) == len(findings)
    assert "not constitute investment advice" in brief.caveat


def test_evidence_is_attached_to_findings_that_have_it():
    prev, curr = make_previous(), make_current()
    findings = compare_snapshots(prev, curr, DEFAULT_CONFIG)
    reliance = next(f for f in findings if f.label == "Reliance Industries" and f.change_type == ChangeType.HOLDING_WEIGHT_CHANGE)
    d = reliance.to_dict()
    assert d["previous_evidence"]["page_number"] == 5
    assert d["current_evidence"]["page_number"] == 5


if __name__ == "__main__":
    import traceback
    tests = [v for k, v in list(globals().items()) if k.startswith("test_")]
    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
            passed += 1
        except Exception:
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
