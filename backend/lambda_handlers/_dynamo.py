"""Shared DynamoDB helpers for the Lambda handlers (spec section 14)."""
import os

import boto3

TABLE_NAME = os.environ.get("FUNDWATCH_TABLE", "FundWatchScans")


def table():
    return boto3.resource("dynamodb").Table(TABLE_NAME)
