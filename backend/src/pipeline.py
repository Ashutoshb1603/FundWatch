"""
End-to-end pipeline orchestrator.

Mirrors the Step Functions workflow in infra/statemachine.asl.json
(spec section 15) step for step, so the same logic can run either:
  - locally / in the FastAPI demo server (this module, called directly), or
  - as the state machine in AWS, where each step is its own Lambda in
    backend/lambda_handlers/ that imports and calls the same functions here.

Keeping the actual logic in one place means the "local demo" and the "real
AWS deployment" can never silently drift apart.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from .bedrock.client import explain_finding
from .comparison import compare_snapshots
from .brief import AnalystBrief, build_brief
from .extraction.extractor import extract_with_fallback
from .materiality import DEFAULT_CONFIG, MaterialityConfig
from .normalization import normalize
from .schema import Finding, FundSnapshot, ValidationResult
from .validation import validate_same_fund


@dataclass
class PipelineResult:
    scan_id: str
    status: str  # "completed" | "validation_failed" | "error"
    previous_snapshot: FundSnapshot | None = None
    current_snapshot: FundSnapshot | None = None
    validation: ValidationResult | None = None
    findings: list[Finding] = field(default_factory=list)
    brief: AnalystBrief | None = None
    steps_log: list[dict] = field(default_factory=list)
    error: str | None = None

    def to_dict(self) -> dict:
        return {
            "scan_id": self.scan_id,
            "status": self.status,
            "error": self.error,
            "fund": {
                "scheme_name": (self.current_snapshot.fund.scheme_name if self.current_snapshot else None),
                "amc": (self.current_snapshot.fund.amc if self.current_snapshot else None),
                "previous_period": (self.previous_snapshot.fund.period if self.previous_snapshot else None),
                "current_period": (self.current_snapshot.fund.period if self.current_snapshot else None),
            },
            "validation": (
                {
                    "same_fund": self.validation.same_fund,
                    "comparable_periods": self.validation.comparable_periods,
                    "periods_consecutive": self.validation.periods_consecutive,
                    "issues": self.validation.issues,
                }
                if self.validation
                else None
            ),
            "extraction": {
                "previous_confidence": (
                    self.previous_snapshot.extraction_confidence.value if self.previous_snapshot else None
                ),
                "current_confidence": (
                    self.current_snapshot.extraction_confidence.value if self.current_snapshot else None
                ),
                "previous_warnings": self.previous_snapshot.warnings if self.previous_snapshot else [],
                "current_warnings": self.current_snapshot.warnings if self.current_snapshot else [],
            },
            "findings": [f.to_dict() for f in self.findings],
            "material_change_count": len(self.findings),
            "brief": self.brief.to_dict() if self.brief else None,
            "steps_log": self.steps_log,
        }


def _log(result: PipelineResult, step: str, status: str, detail: str = ""):
    result.steps_log.append({"step": step, "status": status, "detail": detail})


def run_pipeline(
    previous_pdf_path: str,
    current_pdf_path: str,
    materiality_config: MaterialityConfig = DEFAULT_CONFIG,
    use_bedrock: bool = True,
    generate_explanations: bool = True,
    scheme_name_hint: str | None = None,
) -> PipelineResult:
    scan_id = str(uuid.uuid4())
    result = PipelineResult(scan_id=scan_id, status="error")

    try:
        _log(result, "extract_text_tables", "running")
        prev_extraction = extract_with_fallback(previous_pdf_path, document_id="previous")
        curr_extraction = extract_with_fallback(current_pdf_path, document_id="current")
        _log(result, "extract_text_tables", "done")

        _log(result, "validate_extraction", "running")
        for outcome in (prev_extraction, curr_extraction):
            if outcome.confidence.value == "manual_verification_required":
                _log(result, "validate_extraction", "warning", f"{outcome.document_id}: needs manual verification")
        _log(result, "validate_extraction", "done")

        _log(result, "normalize_factsheets", "running")
        previous = normalize(prev_extraction, scheme_name_hint=scheme_name_hint)
        current = normalize(curr_extraction, scheme_name_hint=scheme_name_hint)
        result.previous_snapshot = previous
        result.current_snapshot = current
        _log(result, "normalize_factsheets", "done")

        _log(result, "validate_fund_identity", "running")
        validation = validate_same_fund(previous, current)
        result.validation = validation
        _log(
            result,
            "validate_fund_identity",
            "done" if validation.can_proceed else "failed",
            "; ".join(validation.issues) if validation.issues else "",
        )
        if not validation.can_proceed:
            result.status = "validation_failed"
            return result

        _log(result, "compare_data", "running")
        findings = compare_snapshots(previous, current, materiality_config)
        result.findings = findings
        _log(result, "compare_data", "done", f"{len(findings)} findings")

        _log(result, "detect_material_changes_and_attach_evidence", "done", f"{len(findings)} material changes")

        if generate_explanations and use_bedrock:
            _log(result, "generate_explanations", "running")
            for f in findings:
                resp = explain_finding(f.to_dict())
                if resp.available and resp.text:
                    f.explanation = resp.text
            _log(result, "generate_explanations", "done")
        else:
            _log(result, "generate_explanations", "skipped")

        _log(result, "generate_analyst_brief", "running")
        result.brief = build_brief(previous, current, findings, use_bedrock=use_bedrock)
        _log(
            result,
            "generate_analyst_brief",
            "done",
            "with narrative" if result.brief.narrative_available else "deterministic only (Bedrock unavailable)",
        )

        result.status = "completed"
        return result

    except Exception as exc:  # noqa: BLE001
        result.status = "error"
        result.error = str(exc)
        _log(result, "pipeline", "error", str(exc))
        return result
