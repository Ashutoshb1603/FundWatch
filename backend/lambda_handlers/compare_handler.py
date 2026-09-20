"""Step: Compare Data + Detect Material Changes + Attach Evidence.
Fully deterministic — no Bedrock call in this step."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import boto3

from src.comparison import compare_snapshots
from src.materiality import DEFAULT_CONFIG
from src.schema import FundMeta, FundSnapshot, Holding, SectorAllocation, SourceRef

s3 = boto3.client("s3")


def _snapshot_from_dict(d: dict) -> FundSnapshot:
    meta = FundMeta(**d["fund"])
    holdings = [
        Holding(h["company"], h["weight"], SourceRef(**h["source"]) if h.get("source") else None)
        for h in d.get("holdings", [])
    ]
    sectors = [
        SectorAllocation(s["sector"], s["weight"], SourceRef(**s["source"]) if s.get("source") else None)
        for s in d.get("sectors", [])
    ]
    snap = FundSnapshot(document_id=d["document_id"], fund=meta, holdings=holdings, sectors=sectors)
    for f in ("aum_cr", "expense_ratio", "riskometer", "fund_managers"):
        setattr(snap, f, d.get(f))
    return snap


def handler(event, context):
    bucket = event["bucket"]
    prev = json.loads(s3.get_object(Bucket=bucket, Key=event["previous_normalized_key"])["Body"].read())
    curr = json.loads(s3.get_object(Bucket=bucket, Key=event["current_normalized_key"])["Body"].read())

    config = DEFAULT_CONFIG
    if event.get("materiality_overrides"):
        config = DEFAULT_CONFIG.__class__(**{**DEFAULT_CONFIG.__dict__, **event["materiality_overrides"]})

    findings = compare_snapshots(_snapshot_from_dict(prev), _snapshot_from_dict(curr), config)
    findings_dicts = [f.to_dict() for f in findings]

    scan_id = event["scan_id"]
    out_key = f"scans/{scan_id}/findings.json"
    s3.put_object(Bucket=bucket, Key=out_key, Body=json.dumps(findings_dicts).encode("utf-8"))
    return {"bucket": bucket, "findings_key": out_key, "material_change_count": len(findings_dicts), "scan_id": scan_id}
