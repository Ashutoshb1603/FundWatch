"""Step: Generate Analyst Brief. Combines findings + Bedrock narrative into
the final structured brief and stores the completed scan in DynamoDB."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import boto3

from src.bedrock.client import generate_brief
from ._dynamo import table

s3 = boto3.client("s3")


def handler(event, context):
    bucket = event["bucket"]
    findings = json.loads(s3.get_object(Bucket=bucket, Key=event["findings_key"])["Body"].read())
    current = json.loads(
        s3.get_object(Bucket=bucket, Key=event["current_normalized_key"])["Body"].read()
    )
    previous = json.loads(
        s3.get_object(Bucket=bucket, Key=event["previous_normalized_key"])["Body"].read()
    )
    current_fund = current.get("fund", {})
    previous_fund = previous.get("fund", {})
    fund = {
        "scheme_name": current_fund.get("scheme_name"),
        "amc": current_fund.get("amc"),
        "previous_period": previous_fund.get("period"),
        "current_period": current_fund.get("period"),
    }

    resp = generate_brief(
        scheme_name=fund.get("scheme_name"),
        previous_period=fund.get("previous_period"),
        current_period=fund.get("current_period"),
        findings=findings,
    )

    brief = {
        "scheme_name": fund.get("scheme_name"),
        "previous_period": fund.get("previous_period"),
        "current_period": fund.get("current_period"),
        "key_changes": findings,
        "narrative": resp.text if resp.available else None,
        "narrative_available": resp.available,
        "caveat": (
            "This brief distinguishes observed disclosure changes (deterministically "
            "calculated) from narrative interpretation. Not investment advice."
        ),
    }

    scan_id = event["scan_id"]
    table().put_item(
        Item={
            "scan_id": scan_id,
            "status": "completed",
            "current_step": "generate_analyst_brief",
            "fund": fund,
            "validation": event.get("validation"),
            "findings": findings,
            "brief": brief,
            "created_at": int(time.time()),
        }
    )
    return {"scan_id": scan_id, "status": "completed", "brief": brief}
