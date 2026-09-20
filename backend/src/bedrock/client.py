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
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from pathlib import Path


def _load_dotenv() -> None:
    """Load backend/.env into os.environ (no python-dotenv dependency).
    Real environment variables win over the file."""
    path = Path(__file__).resolve().parents[2] / ".env"
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v:
            os.environ.setdefault(k, v)


_load_dotenv()

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


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


def _bedrock_has_credentials() -> bool:
    # Avoid boto3's full credential chain: it probes the EC2 metadata endpoint,
    # which stalls for seconds on machines that aren't on AWS.
    if os.environ.get("AWS_ACCESS_KEY_ID") or os.environ.get("AWS_PROFILE"):
        return True
    home = Path.home() / ".aws"
    return (home / "credentials").is_file() or (home / "config").is_file()


def _use_groq() -> bool:
    """LLM_PROVIDER=groq|bedrock forces a provider; otherwise Groq is used only
    when GROQ_API_KEY is set and no AWS credentials are available."""
    provider = os.environ.get("LLM_PROVIDER", "auto").lower()
    if provider == "groq":
        return True
    if provider == "bedrock":
        return False
    return bool(os.environ.get("GROQ_API_KEY")) and not _bedrock_has_credentials()


def _groq_converse(system_prompt: str, user_prompt: str) -> BedrockResponse:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        return BedrockResponse(available=False, error="GROQ_API_KEY is not set.")
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 1024,
    }
    if "gpt-oss" in GROQ_MODEL:
        payload["reasoning_effort"] = "low"  # fewer hidden tokens against the TPM cap
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        GROQ_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "fundwatch/1.0",
        },
    )
    last_error = "unknown error"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read())
            return BedrockResponse(available=True, text=data["choices"][0]["message"]["content"])
        except urllib.error.HTTPError as exc:
            last_error = f"HTTP {exc.code}"
            if exc.code != 429 or attempt == 3:
                break
            # Free-tier TPM limit: honour "try again in Ns" then retry.
            try:
                msg = json.loads(exc.read())["error"]["message"]
                m = re.search(r"try again in ([\d.]+)s", msg)
                wait = float(m.group(1)) if m else 10.0
            except Exception:  # noqa: BLE001
                wait = 10.0
            time.sleep(min(wait + 1, 30))
        except Exception as exc:  # noqa: BLE001
            last_error = str(exc)
            break
    return BedrockResponse(available=False, error=last_error)


def _converse(system_prompt: str, user_prompt: str, model_id: str = DEFAULT_MODEL_ID) -> BedrockResponse:
    if _use_groq():
        return _groq_converse(system_prompt, user_prompt)
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


_KEEP = ("change_type", "label", "previous_value", "current_value", "absolute_difference",
         "percentage_point_difference", "priority", "rule_triggered")


def compact_findings(findings: list[dict], limit: int = 25) -> dict:
    """Shrink findings for LLM context (free-tier providers reject big payloads).
    Keeps the top `limit` findings (already priority-ranked) with only the
    deterministic fields plus evidence page numbers; reports the omitted count."""
    rows = []
    for f in findings[:limit]:
        row = {k: f.get(k) for k in _KEEP}
        for side in ("previous", "current"):
            ev = f.get(f"{side}_evidence") or {}
            if ev.get("page_number") is not None:
                row[f"{side}_evidence_page"] = ev["page_number"]
        rows.append(row)
    return {
        "total_findings": len(findings),
        "included_findings": len(rows),
        "omitted_lower_priority_findings": max(0, len(findings) - len(rows)),
        "findings": rows,
    }


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
        findings_json=json.dumps(compact_findings(findings, limit=15), indent=1),
    )
    return _converse(SYSTEM_PROMPT, prompt, model_id)


def chat_answer(question: str, context: dict, model_id: str = DEFAULT_MODEL_ID) -> BedrockResponse:
    context = dict(context)
    if isinstance(context.get("findings"), list):
        context["findings"] = compact_findings(context["findings"], limit=30)
    if isinstance(context.get("brief"), dict):  # avoid duplicating findings via the brief
        context["brief"] = {k: v for k, v in context["brief"].items() if k != "key_changes"}
    prompt = (
        f"Stored FundWatch analysis (JSON):\n{json.dumps(context, indent=1)}\n\n"
        f"Analyst question: {question}"
    )
    return _converse(CHAT_SYSTEM_PROMPT, prompt, model_id)
