"""API entrypoint: GET /scans/{scan_id}."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ._dynamo import table


def handler(event, context):
    scan_id = event["pathParameters"]["scan_id"]
    item = table().get_item(Key={"scan_id": scan_id}).get("Item")
    if not item:
        return {"statusCode": 404, "body": json.dumps({"error": "Scan not found."})}
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps(item, default=str)}
