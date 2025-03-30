import os
import sys

import boto3
from botocore.config import Config

filename = sys.argv[1]

config = Config(signature_version='s3v4')
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("S3_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("S3_SECRET_KEY"),
    endpoint_url=os.getenv("S3_ENDPOINT"),
    config=config
)
bucket_name = "hutao-distribute"
print("Uploading to hutao-dist R2 bucket...", flush=True)
s3_client.upload_file(filename, bucket_name, filename)

minio_s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    endpoint_url=os.getenv("MINIO_ENDPOINT"),
    config=config
)
minio_bucket_name = "hutao"
print("Uploading to hutao-dist MinIO bucket...", flush=True)
minio_s3_client.upload_file(filename, minio_bucket_name, filename)