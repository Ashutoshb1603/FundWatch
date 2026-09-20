"""Step: Validate Fund Identity. Input: {bucket, previous_normalized_key, current_normalized_key}."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import boto3

from src.schema import FundMeta, FundSnapshot
from src.validation import validate_same_fund

s3 = boto3.client("s3")


def _snapshot_from_dict(d: dict) -> FundSnapshot:
    meta = FundMeta(**d["fund"])
    d = dict(d)
    d["fund"] = meta
    d.pop("extraction_confidence", None)
    d.pop("holdings", None)
    d.pop("sectors", None)
    return FundSnapshot(**d)


def handler(event, context):
    bucket = event["bucket"]
    prev = json.loads(s3.get_object(Bucket=bucket, Key=event["previous_normalized_key"])["Body"].read())
    curr = json.loads(s3.get_object(Bucket=bucket, Key=event["current_normalized_key"])["Body"].read())

    result = validate_same_fund(_snapshot_from_dict(prev), _snapshot_from_dict(curr))
    return {
        "can_proceed": result.can_proceed,
        "same_fund": result.same_fund,
        "comparable_periods": result.comparable_periods,
        "periods_consecutive": result.periods_consecutive,
        "issues": result.issues,
    }
