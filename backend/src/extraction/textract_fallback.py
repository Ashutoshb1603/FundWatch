"""
Fallback extraction layer (spec section 6, "fallback layer").

Wraps Amazon Textract's AnalyzeDocument (TABLES + FORMS) for scanned or
low-confidence factsheets. This module is written to run inside AWS Lambda
with a real boto3 client; in local/dev environments without AWS credentials
it degrades gracefully and reports itself as unavailable rather than
crashing the pipeline (spec section 16: "if Textract fails, show an
extraction error and allow retry").
"""
from __future__ import annotations

from dataclasses import dataclass, field

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None


@dataclass
class TextractResult:
    available: bool
    document_id: str
    lines_by_page: dict[int, list[str]] = field(default_factory=dict)
    tables_by_page: dict[int, list[list[list[str]]]] = field(default_factory=dict)
    error: str | None = None


def textract_available() -> bool:
    return boto3 is not None


def analyze_with_textract(s3_bucket: str, s3_key: str, document_id: str) -> TextractResult:
    """Calls Textract's asynchronous document analysis API against an object
    already uploaded to S3 (StartDocumentAnalysis + GetDocumentAnalysis).
    Synchronous AnalyzeDocument is avoided here because factsheets are
    typically multi-page, which requires the async API."""
    if boto3 is None:
        return TextractResult(
            available=False,
            document_id=document_id,
            error="boto3 not installed in this environment.",
        )

    try:
        client = boto3.client("textract")
        start = client.start_document_analysis(
            DocumentLocation={"S3Object": {"Bucket": s3_bucket, "Name": s3_key}},
            FeatureTypes=["TABLES", "FORMS"],
        )
        job_id = start["JobId"]
        result = _poll_and_collect(client, job_id)
        return _parse_blocks(result, document_id)
    except Exception as exc:  # noqa: BLE001
        return TextractResult(available=True, document_id=document_id, error=str(exc))


def _poll_and_collect(client, job_id: str, max_polls: int = 60, delay_s: float = 2.0) -> list[dict]:
    import time

    blocks: list[dict] = []
    next_token = None
    while True:
        for _ in range(max_polls):
            kwargs = {"JobId": job_id}
            if next_token:
                kwargs["NextToken"] = next_token
            resp = client.get_document_analysis(**kwargs)
            status = resp["JobStatus"]
            if status == "SUCCEEDED":
                blocks.extend(resp.get("Blocks", []))
                next_token = resp.get("NextToken")
                if not next_token:
                    return blocks
                break
            if status == "FAILED":
                raise RuntimeError(f"Textract job failed: {resp.get('StatusMessage')}")
            time.sleep(delay_s)
        else:
            raise TimeoutError("Textract job did not complete in time.")


def _parse_blocks(blocks: list[dict], document_id: str) -> TextractResult:
    lines_by_page: dict[int, list[str]] = {}
    for b in blocks:
        if b.get("BlockType") == "LINE":
            page = b.get("Page", 1)
            lines_by_page.setdefault(page, []).append(b.get("Text", ""))
    # Table reconstruction from CELL blocks omitted here for brevity; a full
    # implementation would walk WORD/CELL/TABLE relationships. lines_by_page
    # is sufficient to re-run the same regex field finders used by the
    # primary parser as a fallback.
    return TextractResult(available=True, document_id=document_id, lines_by_page=lines_by_page)
