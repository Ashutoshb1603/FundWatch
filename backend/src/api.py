"""
Local/dev API server (FastAPI).

This plays the role of "API Gateway + Lambda" for local development and for
the hackathon demo: same pipeline.py logic the real Lambdas call, exposed
over plain HTTP so the Next.js frontend has something to talk to without
needing an AWS account. Swap this for real API Gateway + Lambda routes by
deploying infra/template.yaml.
"""
from __future__ import annotations

import os
import shutil
import tempfile
import uuid

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .bedrock.client import chat_answer
from .pipeline import run_pipeline

app = FastAPI(title="FundWatch API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to the deployed frontend origin in production
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB, per spec section 17 (restrict file size)
ALLOWED_CONTENT_TYPES = {"application/pdf"}

# In-memory store for the demo. Replace with DynamoDB (spec section 14) for
# a real deployment — see backend/lambda_handlers for the Dynamo-backed
# equivalents.
_SCANS: dict[str, dict] = {}


def _safe_temp_path(upload: UploadFile) -> str:
    suffix = ".pdf"
    tmp_dir = tempfile.mkdtemp(prefix="fundwatch_")
    # never trust the client filename directly (path traversal / injection)
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    return os.path.join(tmp_dir, safe_name)


async def _save_upload(upload: UploadFile) -> str:
    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(400, f"Unsupported file type: {upload.content_type}. Only PDF is accepted.")
    path = _safe_temp_path(upload)
    size = 0
    with open(path, "wb") as f:
        while chunk := await upload.read(1024 * 1024):
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                f.close()
                os.remove(path)
                raise HTTPException(400, "File too large (25MB limit).")
            f.write(chunk)
    return path


@app.post("/api/analyze")
async def analyze(
    previous_factsheet: UploadFile = File(...),
    current_factsheet: UploadFile = File(...),
    scheme_name: str | None = Form(default=None),
):
    prev_path = await _save_upload(previous_factsheet)
    curr_path = await _save_upload(current_factsheet)
    try:
        result = run_pipeline(prev_path, curr_path, scheme_name_hint=scheme_name)
    finally:
        shutil.rmtree(os.path.dirname(prev_path), ignore_errors=True)
        shutil.rmtree(os.path.dirname(curr_path), ignore_errors=True)

    payload = result.to_dict()
    _SCANS[result.scan_id] = payload
    return payload


@app.get("/api/scans/{scan_id}")
async def get_scan(scan_id: str):
    scan = _SCANS.get(scan_id)
    if not scan:
        raise HTTPException(404, "Scan not found.")
    return scan


class ChatRequest(BaseModel):
    question: str


@app.post("/api/scans/{scan_id}/chat")
async def chat(scan_id: str, req: ChatRequest):
    scan = _SCANS.get(scan_id)
    if not scan:
        raise HTTPException(404, "Scan not found.")
    context = {
        "fund": scan["fund"],
        "findings": scan["findings"],
        "brief": scan["brief"],
    }
    resp = chat_answer(req.question, context)
    if not resp.available:
        return {
            "available": False,
            "answer": (
                "The analyst chat needs an LLM provider (Amazon Bedrock or Groq), which isn't reachable right now."
                "You can still browse the findings, evidence, and analyst brief above."
            ),
        }
    return {"available": True, "answer": resp.text}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
