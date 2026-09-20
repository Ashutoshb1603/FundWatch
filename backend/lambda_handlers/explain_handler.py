"""Step: Send Structured Findings to Bedrock / Generate Explanations.
Runs per-finding; on Bedrock failure it leaves `explanation: null` and
continues rather than failing the whole workflow (spec section 16)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import boto3

from src.bedrock.client import explain_finding

s3 = boto3.client("s3")


def handler(event, context):
    bucket = event["bucket"]
    findings = json.loads(s3.get_object(Bucket=bucket, Key=event["findings_key"])["Body"].read())

    for f in findings:
        resp = explain_finding(f)
        f["explanation"] = resp.text if resp.available else None
        f["explanation_available"] = resp.available

    scan_id = event["scan_id"]
    out_key = f"scans/{scan_id}/findings_explained.json"
    s3.put_object(Bucket=bucket, Key=out_key, Body=json.dumps(findings).encode("utf-8"))
    return {"bucket": bucket, "findings_key": out_key, "scan_id": scan_id}
