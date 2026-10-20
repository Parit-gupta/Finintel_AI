
import boto3

bucket = "finintel-ai-parit-2026-unique"
key = "raw/loan_applications.csv"

session = boto3.Session(profile_name="finintel")
s3 = session.client("s3", region_name="us-east-1")

response = s3.head_object(Bucket=bucket, Key=key)

print("S3 connection successful")
print("Dataset:", key)
print("Size:", response["ContentLength"], "bytes")

data = s3.get_object(Bucket=bucket, Key=key)
print("First 200 bytes:")
print(data["Body"].read(200).decode("utf-8", errors="replace"))
