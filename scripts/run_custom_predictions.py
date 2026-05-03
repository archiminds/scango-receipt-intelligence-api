#!/usr/bin/env python3
"""Replay synthetic samples through the IAM-protected API and capture responses.

The script signs each request with AWS SigV4 using the configured local AWS
profile, then writes API responses as prediction records for the evaluator.
"""

import json
import sys
from pathlib import Path
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import boto3
import requests
from requests_aws4auth import AWS4Auth

API_URL = "https://qvkec05ydc.execute-api.us-east-1.amazonaws.com/prod/v1/receipts/parse"
DATASET_PATH = Path("synthetic/custom_dataset.jsonl")
OUT_PATH = Path("synthetic/custom_predictions.jsonl")
REGION = "us-east-1"
PROFILE = "default"


def _sigv4_auth():
  """Return AWS4Auth signer using the configured profile/region."""
  # The deployed API uses API Gateway AWS_IAM authorization, so requests must be
  # signed for the execute-api service with valid AWS credentials.
  session = boto3.Session(profile_name=PROFILE, region_name=REGION)
  creds = session.get_credentials().get_frozen_credentials()
  return AWS4Auth(
      creds.access_key,
      creds.secret_key,
      REGION,
      "execute-api",
      session_token=creds.token,
  )


def main():
  auth = _sigv4_auth()

  with DATASET_PATH.open() as src, OUT_PATH.open("w") as dst:
    for line in src:
      sample = json.loads(line)
      # Prefer clean_text for deterministic API evaluation. Switch to
      # receipt_text when specifically testing OCR-noise robustness.
      payload = {
          "receipt_text": sample.get("clean_text") or sample.get("receipt_text"),
          "currency": sample["expected_output"].get("currency", "AUD"),
          "source": "synthetic_eval",
          "metadata": {
              "dataset_id": sample.get("metadata", {}).get("scenario", "synthetic"),
              "sample_id": sample.get("metadata", {}).get("id") or str(uuid4()),
          },
      }

      resp = requests.post(API_URL, json=payload, auth=auth, timeout=30)
      resp.raise_for_status()

      # The evaluator accepts records where the predicted API output lives under
      # expected_output, matching the synthetic dataset shape.
      dst.write(
          json.dumps(
              {
                  "request_id": payload["metadata"]["sample_id"],
                  "receipt_text": payload["receipt_text"],
                  "expected_output": resp.json(),
                  "metadata": payload["metadata"],
              }
          )
          + "\n"
      )

  print(f"Saved predictions to {OUT_PATH}")


if __name__ == "__main__":
  main()
