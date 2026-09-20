"""Step: Extract Text/Tables. Input: {bucket, key, document_id}."""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import boto3

from src.extraction.extractor import extract_with_fallback

s3 = boto3.client("s3")


def handler(event, context):
    bucket, key, document_id = event["bucket"], event["key"], event["document_id"]
    local_path = f"/tmp/{document_id}.pdf"
    s3.download_file(bucket, key, local_path)

    outcome = extract_with_fallback(local_path, document_id, s3_bucket=bucket, s3_key=key)

    result = {
        "document_id": document_id,
        "confidence": outcome.confidence.value,
        "notes": outcome.notes,
        "full_text": outcome.primary.full_text,
        "pages": [
            {"page_number": p.page_number, "text": p.text, "tables": p.tables}
            for p in outcome.primary.pages
        ],
    }
    scan_id = event.get("scan_id", "legacy")
    out_key = f"scans/{scan_id}/extracted/{document_id}.json"
    s3.put_object(Bucket=bucket, Key=out_key, Body=json.dumps(result).encode("utf-8"))
    return {"bucket": bucket, "extracted_key": out_key, "document_id": document_id, "confidence": outcome.confidence.value}
