"""Internal Step Functions task: persist scan progress/status."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ._dynamo import table


def handler(event, context):
    scan_id = event["scan_id"]
    status = event.get("status", "processing")
    step = event.get("step")
    detail = event.get("detail")
    attrs = ["#s = :s", "updated_at = :t"]
    names = {"#s": "status"}
    values = {":s": status, ":t": int(time.time())}
    if step is not None:
        attrs.append("current_step = :step")
        values[":step"] = step
    if detail is not None:
        attrs.append("status_detail = :detail")
        values[":detail"] = detail

    extra = event.get("extra")
    if isinstance(extra, dict):
        for key, value in extra.items():
            safe_key = f"#{key}"
            safe_value = f":{key}"
            names[safe_key] = key
            values[safe_value] = value
            attrs.append(f"{safe_key} = {safe_value}")

    table().update_item(
        Key={"scan_id": scan_id},
        UpdateExpression="SET " + ", ".join(attrs),
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )
    return event
