"""
Amazon Bedrock client wrapper (spec section 10).

Uses the Bedrock Converse API. Designed to fail soft: if Bedrock is
unavailable, mis-configured, or errors out, callers get back
`BedrockResponse(available=False, ...)` and the rest of the pipeline (which
is 100% deterministic already) continues to work — the UI just shows the
findings and evidence without a prose explanation (spec section 16).
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

try:
    import boto3
except ImportError:  # pragma: no cover
    boto3 = None

from .prompts import (
    ANALYST_BRIEF_TEMPLATE,
    CHAT_SYSTEM_PROMPT,
    EXPLAIN_FINDING_TEMPLATE,
    SYSTEM_PROMPT,
)

DEFAULT_MODEL_ID = os.environ.get("BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-6")


@dataclass
class BedrockResponse:
    available: bool
    text: str | None = None
    error: str | None = None


def _get_client():
    if boto3 is None:
        return None
    try:
        return boto3.client("bedrock-runtime", region_name=os.environ.get("AWS_REGION", "ap-south-1"))
    except Exception:
        return None


def _converse(system_prompt: str, user_prompt: str, model_id: str = DEFAULT_MODEL_ID) -> BedrockResponse:
    client = _get_client()
    if client is None:
        return BedrockResponse(available=False, error="Bedrock client unavailable in this environment.")
    try:
        resp = client.converse(
            modelId=model_id,
            system=[{"text": system_prompt}],
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            inferenceConfig={"maxTokens": 1024, "temperature": 0.2},
        )
        content = resp["output"]["message"]["content"]
        text = "".join(block.get("text", "") for block in content)
        return BedrockResponse(available=True, text=text)
    except Exception as exc:  # noqa: BLE001
        return BedrockResponse(available=False, error=str(exc))


def explain_finding(finding_dict: dict, model_id: str = DEFAULT_MODEL_ID) -> BedrockResponse:
    prompt = EXPLAIN_FINDING_TEMPLATE.format(finding_json=json.dumps(finding_dict, indent=2))
    return _converse(SYSTEM_PROMPT, prompt, model_id)


def generate_brief(
    scheme_name: str,
    previous_period: str,
    current_period: str,
    findings: list[dict],
    model_id: str = DEFAULT_MODEL_ID,
) -> BedrockResponse:
    prompt = ANALYST_BRIEF_TEMPLATE.format(
        scheme_name=scheme_name or "Unknown scheme",
        previous_period=previous_period or "previous period",
        current_period=current_period or "current period",
        findings_json=json.dumps(findings, indent=2),
    )
    return _converse(SYSTEM_PROMPT, prompt, model_id)


def chat_answer(question: str, context: dict, model_id: str = DEFAULT_MODEL_ID) -> BedrockResponse:
    prompt = (
        f"Stored FundWatch analysis (JSON):\n{json.dumps(context, indent=2)}\n\n"
        f"Analyst question: {question}"
    )
    return _converse(CHAT_SYSTEM_PROMPT, prompt, model_id)
