# FundWatch

**Evidence-first mutual fund disclosure intelligence.** Upload two monthly
factsheets for the same scheme; FundWatch extracts the numbers, compares
them deterministically, flags material changes against configurable
thresholds, links every finding back to a source page, and (optionally)
uses Amazon Bedrock to explain what it found in plain language.

FundWatch answers **what changed, where, and by how much** — it never
recommends buying, selling, or holding anything.

---

## How it's built

**Deterministic code does the math. Bedrock only explains it.**

```
Upload → Extract → Validate → Normalize → Compare → Detect Material
Changes → Attach Evidence → Explain with Bedrock → Generate Analyst Brief
```

Every number, diff, and materiality flag is calculated in plain Python in
`backend/src/comparison.py` and `backend/src/materiality.py` — no LLM
involved. Amazon Bedrock only ever receives the already-computed findings
and writes prose around them (`backend/src/bedrock/`). If Bedrock is down,
the app still works: every screen (findings, evidence, the ranked brief)
renders from the deterministic layer alone, just without narrative text.

```
backend/
  src/
    schema.py            normalized data model + Finding/Evidence shapes
    extraction/           pdfplumber (primary) + Textract (fallback)
    normalization.py     raw extraction -> normalized FundSnapshot
    validation.py         same-fund / comparable-period checks
    comparison.py         *** deterministic diff engine, no LLM ***
    materiality.py        configurable thresholds -> priority
    bedrock/               prompts + Converse API client (graceful fallback)
    brief.py               analyst brief (deterministic skeleton + optional narrative)
    pipeline.py             orchestrates all of the above, step by step
    api.py                  FastAPI server — local/dev stand-in for API Gateway
  lambda_handlers/         thin AWS Lambda wrappers around src/, one per
                            Step Functions state, for the real deployment
  tests/                    unit tests for the deterministic core (no AWS needed)

infra/
  template.yaml            AWS SAM template: S3, API Gateway, Lambda,
                            Step Functions, DynamoDB, IAM
  statemachine.asl.json    Step Functions workflow definition

frontend/                  Next.js + Tailwind UI
  app/page.tsx              upload -> processing -> dashboard flow
  components/               UploadPanel, ProcessingView, Dashboard,
                             ChangeCard, EvidenceDrawer, AnalystBriefPanel,
                             AnalystChat
```

## Run it locally (no AWS account needed)

The backend runs the full deterministic pipeline on your machine; Bedrock
calls simply report themselves as unavailable if you have no AWS
credentials configured, and the app degrades exactly as the product spec
requires.

**LLM provider without AWS:** copy `backend/.env.example` to `backend/.env`
and set `GROQ_API_KEY` (free tier). When no AWS credentials are found the
backend uses Groq (`GROQ_MODEL`, default `openai/gpt-oss-120b`) with the same
grounded prompts; `LLM_PROVIDER=bedrock|groq` forces one. Free-tier rate
limits are handled by sending compacted findings (top 15 to the brief, top 30
to chat), explaining only the top 6 findings, and retrying on HTTP 429.

**Backend**
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.api:app --reload --port 8000
```

**Frontend**
```bash
cd frontend
npm install
cp .env.local.example .env.local   # points at http://localhost:8000
npm run dev
```

Open http://localhost:3000, upload two PDF factsheets for the same scheme,
and click **Analyze Changes**.

**Run the deterministic-core tests** (no PDFs or AWS needed — uses
synthetic `FundSnapshot` fixtures in `backend/tests/sample_data.py`):
```bash
cd backend
python3 tests/test_pipeline.py
```

## Deploying the real AWS architecture

`infra/template.yaml` is an AWS SAM template implementing the lean
serverless stack from the product spec: S3 for documents/evidence/reports,
API Gateway + Lambda for the API, Step Functions
(`infra/statemachine.asl.json`) to orchestrate extraction through brief
generation, Textract as the scanned-PDF fallback, Bedrock for the
natural-language layer, and DynamoDB for scan state. No Redis, Kafka,
vector DB, ECS, or multi-agent framework — none of that is needed here.

```bash
cd infra
sam build
sam deploy --guided
```

Point the frontend's `NEXT_PUBLIC_API_BASE_URL` at the deployed API
Gateway URL from the `sam deploy` output. The template defaults to the
active Amazon Bedrock global inference profile for Claude Sonnet 4.6;
change `BEDROCK_MODEL_ID` only if your account/region uses another enabled
model. For multi-scheme AMC factsheets, enter the exact scheme name in the
UI so FundWatch can focus extraction on the relevant pages.

## What's implemented vs. what's scaffolded

**Fully implemented and tested:**
- Normalized schema, deterministic comparison engine, configurable
  materiality rules, fund/period validation, evidence attachment, analyst
  brief skeleton — all covered by `backend/tests/test_pipeline.py`.
- FastAPI local server wiring the same pipeline end to end.
- Next.js UI for all core screens (upload, processing, dashboard with
  portfolio/sector/fund-level/risk tabs, change cards, evidence drawer,
  analyst brief, analyst chat). The TS/TSX source is syntax-checked here;
  run `npm ci && npm run build` on a networked developer machine before
  deployment to perform the full Next.js production build.

**Not live-AWS tested in this environment yet:**
- Textract fallback and Bedrock Converse calls are written against the
  real boto3 APIs but weren't run against a live AWS account in this
  environment (no credentials here). Both fail soft by design — see
  `backend/src/extraction/textract_fallback.py` and
  `backend/src/bedrock/client.py`.
- The regex-based field/table extraction in
  `backend/src/normalization.py` and `backend/src/extraction/pdf_parser.py`
  covers common Indian mutual-fund factsheet phrasing but will need
  per-AMC tuning against real factsheet PDFs — this is expected and is
  exactly why the pipeline reports extraction confidence and surfaces
  "Not disclosed / not detected" rather than guessing.
- Lambda handlers in `backend/lambda_handlers/` mirror the pipeline for
  AWS deployment; they weren't invoked in AWS itself in this environment.
