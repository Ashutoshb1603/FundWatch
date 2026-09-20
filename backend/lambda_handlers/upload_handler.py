"""API entrypoint: POST /analyze.
Accepts S3 object keys returned by the presigned-upload endpoint, validates
that both objects exist and are safe-sized PDFs, then starts Step Functions.
"""
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import boto3

from ._dynamo import table

sfn = boto3.client("stepfunctions")
s3 = boto3.client("s3")
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN", "")

MAX_BYTES = 25 * 1024 * 1024


def handler(event, context):
    body = json.loads(event.get("body") or "{}")
    previous_key = body.get("previous_key")
    current_key = body.get("current_key")
    fund_name_hint = body.get("fund_name") or body.get("scheme_name")

    if not previous_key or not current_key:
        return _response(400, {"error": "previous_key and current_key are required."})
    if not STATE_MACHINE_ARN:
        return _response(500, {"error": "STATE_MACHINE_ARN is not configured."})

    bucket = os.environ["FUNDWATCH_BUCKET"]
    objects = []
    try:
        for key in (previous_key, current_key):
            if not key.lower().endswith(".pdf"):
                return _response(400, {"error": "Only PDF uploads are accepted."})
            if not key.startswith("uploads/"):
                return _response(400, {"error": "Uploads must use an uploads/ S3 prefix."})
            head = s3.head_object(Bucket=bucket, Key=key)
            size = int(head.get("ContentLength", 0))
            if size <= 0 or size > MAX_BYTES:
                return _response(400, {"error": f"{key} is empty or exceeds the 25 MB limit."})
            objects.append({"bucket": bucket, "key": key, "size": size})
    except s3.exceptions.NoSuchKey:
        return _response(400, {"error": "One or both uploaded PDFs could not be found in S3."})
    except Exception as exc:
        return _response(400, {"error": f"Upload validation failed: {exc}"})

    scan_id = str(uuid.uuid4())
    table().put_item(
        Item={
            "scan_id": scan_id,
            "status": "processing",
            "current_step": "queued",
            "fund_name_hint": fund_name_hint,
        }
    )

    sfn.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=scan_id,
        input=json.dumps(
            {
                "scan_id": scan_id,
                "bucket": bucket,
                "previous": {"bucket": bucket, "key": previous_key, "document_id": "previous"},
                "current": {"bucket": bucket, "key": current_key, "document_id": "current"},
                "scheme_name_hint": fund_name_hint,
            }
        ),
    )
    return _response(202, {"scan_id": scan_id, "status": "processing"})


def _response(status: int, body: dict):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body)}
