"""Private S3 helpers for archiving FinIntel AI data and model artifacts."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import boto3
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUCKET = "finintel-ai-parit-2026-unique"


def s3_client():
    """Create an S3 client using the normal AWS credential chain or AWS profile."""
    load_dotenv(PROJECT_ROOT / ".env")
    region = os.getenv("AWS_DEFAULT_REGION", os.getenv("AWS_REGION", "us-east-1"))
    profile = os.getenv("AWS_PROFILE")
    session = boto3.Session(profile_name=profile, region_name=region) if profile else boto3.Session(region_name=region)
    return session.client("s3")


def upload_file(path: str | Path, key: str, bucket: str | None = None) -> dict:
    """Upload a file privately and verify the remote size and SHA-256 metadata."""
    source = Path(path).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"File to archive does not exist: {source}")
    bucket = bucket or os.getenv("FININTEL_S3_BUCKET", DEFAULT_BUCKET)
    digest = hashlib.sha256()
    with source.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    checksum = digest.hexdigest()
    client = s3_client()
    client.upload_file(
        str(source), bucket, key,
        ExtraArgs={"Metadata": {"sha256": checksum}, "ServerSideEncryption": "AES256"},
    )
    remote = client.head_object(Bucket=bucket, Key=key)
    if remote["ContentLength"] != source.stat().st_size:
        raise IOError(f"S3 size verification failed for s3://{bucket}/{key}")
    if remote.get("Metadata", {}).get("sha256") != checksum:
        raise IOError(f"S3 SHA-256 metadata verification failed for s3://{bucket}/{key}")
    remote_digest = hashlib.sha256()
    response = client.get_object(Bucket=bucket, Key=key)
    for block in iter(lambda: response["Body"].read(1024 * 1024), b""):
        remote_digest.update(block)
    response["Body"].close()
    if remote_digest.hexdigest() != checksum:
        raise IOError(f"S3 content checksum verification failed for s3://{bucket}/{key}")
    return {"bucket": bucket, "key": key, "size_bytes": remote["ContentLength"], "sha256": checksum}


def download_file(key: str, destination: str | Path, bucket: str | None = None) -> Path:
    """Download a private S3 object to a local path."""
    bucket = bucket or os.getenv("FININTEL_S3_BUCKET", DEFAULT_BUCKET)
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    s3_client().download_file(bucket, key, str(target))
    return target
