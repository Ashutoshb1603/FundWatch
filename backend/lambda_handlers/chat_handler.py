"""API entrypoint: POST /scans/{scan_id}/chat (spec section 13, optional
grounded analyst chat — answers using only the stored scan's findings/brief)."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.bedrock.client import chat_answer
from ._dynamo import table


def handler(event, context):
    scan_id = event["pathParameters"]["scan_id"]
    body = json.loads(event.get("body") or "{}")
    question = body.get("question", "")

    item = table().get_item(Key={"scan_id": scan_id}).get("Item")
    if not item:
        return {"statusCode": 404, "body": json.dumps({"error": "Scan not found."})}

    context_payload = {"fund": item.get("fund"), "findings": item.get("findings"), "brief": item.get("brief")}
    resp = chat_answer(question, context_payload)
    body_out = (
        {"available": True, "answer": resp.text}
        if resp.available
        else {
            "available": False,
            "answer": "The analyst chat needs Amazon Bedrock, which isn't reachable right now.",
        }
    )
    return {"statusCode": 200, "headers": {"Content-Type": "application/json"}, "body": json.dumps(body_out)}
