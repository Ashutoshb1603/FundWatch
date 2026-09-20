# Lambda handlers

Each file here is a thin AWS Lambda entrypoint that calls straight into
`backend/src/`. They exist so the Step Functions workflow
(`infra/statemachine.asl.json`) can run the exact same deterministic logic
that the local FastAPI demo (`backend/src/api.py`) uses — nothing is
reimplemented, only wired to Lambda's event/response shape and to
S3 / DynamoDB for state.

Deploy them via `infra/template.yaml` (AWS SAM). Each handler:
  - reads its input from the Step Functions state input (usually S3 pointers
    + the previous step's JSON output),
  - does its one job,
  - writes any large artifacts (extracted text, normalized JSON) back to S3,
  - returns a small JSON payload for the next state.
