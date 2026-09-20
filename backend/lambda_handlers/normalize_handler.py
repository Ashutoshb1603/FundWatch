"""Step: Normalize Factsheet A / B. Input: {bucket, extracted_key, document_id}."""
import dataclasses
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import boto3

from src.extraction.extractor import ExtractionOutcome
from src.extraction.pdf_parser import ExtractedDocument, PageText
from src.normalization import normalize
from src.schema import ConfidenceLevel

s3 = boto3.client("s3")


def handler(event, context):
    bucket, extracted_key, document_id = event["bucket"], event["extracted_key"], event["document_id"]
    raw = json.loads(s3.get_object(Bucket=bucket, Key=extracted_key)["Body"].read())

    pages = [PageText(page_number=p["page_number"], text=p["text"], tables=p["tables"]) for p in raw["pages"]]
    doc = ExtractedDocument(document_id=document_id, pages=pages)
    outcome = ExtractionOutcome(
        document_id=document_id,
        primary=doc,
        used_fallback=False,
        fallback=None,
        confidence=ConfidenceLevel(raw["confidence"]),
        notes=raw["notes"],
    )
    snapshot = normalize(outcome, scheme_name_hint=event.get("scheme_name_hint"))

    scan_id = event.get("scan_id", "legacy")
    out_key = f"scans/{scan_id}/normalized/{document_id}.json"
    s3.put_object(Bucket=bucket, Key=out_key, Body=json.dumps(dataclasses.asdict(snapshot), default=str).encode("utf-8"))
    return {"bucket": bucket, "normalized_key": out_key, "document_id": document_id}
