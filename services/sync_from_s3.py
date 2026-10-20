"""Download the private app datasets and model artifacts from S3.

On EC2, boto3 uses the attached instance role. No access keys or local profile
are needed. Only the app's raw/ and models/ prefixes are downloaded.
"""

from __future__ import annotations

import os
from pathlib import Path

import boto3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BUCKET = os.getenv("FININTEL_S3_BUCKET", "finintel-ai-parit-2026-unique")
REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
PREFIX_TARGETS = {
    "raw/": PROJECT_ROOT / "datasets" / "raw",
    "models/": PROJECT_ROOT / "backend" / "ml" / "models",
}


def main() -> None:
    client = boto3.client("s3", region_name=REGION)
    downloaded = 0
    for prefix, target_root in PREFIX_TARGETS.items():
        paginator = client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
            for item in page.get("Contents", []):
                key = item["Key"]
                relative = key[len(prefix) :]
                if not relative or relative.endswith("/"):
                    continue
                destination = target_root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                client.download_file(BUCKET, key, str(destination))
                downloaded += 1
                print(f"Downloaded s3://{BUCKET}/{key}")
    print(f"Finished: downloaded {downloaded} app assets from s3://{BUCKET}/")


if __name__ == "__main__":
    main()
