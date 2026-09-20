"""POST /uploads/presign.
Returns short-lived presigned PUT URLs for the two PDF factsheets.
The browser uploads directly to S3 so API Gateway never carries the PDF bytes.
"""
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import boto3

s3 = boto3.client("s3")

ALLOWED_EXTENSIONS = {".pdf"}
MAX_BYTES = 25 * 1024 * 1024
URL_EXPIRES_SECONDS = 900


def handler(event, context):
    body = json.loads(event.get("body") or "{}")
    files = body.get("files") or {}
    previous_name = files.get("previous")
    current_name = files.get("current")
    if not previous_name or not current_name:
        return _response(400, {"error": "files.previous and files.current are required."})

    for name in (previous_name, current_name):
        lower = str(name).lower()
        if not any(lower.endswith(ext) for ext in ALLOWED_EXTENSIONS):
            return _response(400, {"error": f"Unsupported file type for {name}. Only PDF is accepted."})

    bucket = os.environ["FUNDWATCH_BUCKET"]
    upload_id = str(uuid.uuid4())
    keys = {
        "previous": f"uploads/{upload_id}/previous.pdf",
        "current": f"uploads/{upload_id}/current.pdf",
    }
    urls = {
        role: s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket,
                "Key": key,
                "ContentType": "application/pdf",
                "ServerSideEncryption": "AES256",
            },
            ExpiresIn=URL_EXPIRES_SECONDS,
            HttpMethod="PUT",
        )
        for role, key in keys.items()
    }

    return _response(
        200,
        {
            "upload_id": upload_id,
            "bucket": bucket,
            "keys": keys,
            "urls": urls,
            "max_bytes": MAX_BYTES,
            "expires_in": URL_EXPIRES_SECONDS,
        },
    )


def _response(status: int, body: dict):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }
