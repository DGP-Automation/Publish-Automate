import os
import sys
import threading

import boto3
from botocore.config import Config

class ProgressPercentage(object):
    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()

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
s3_client.upload_file(filename, bucket_name, filename, Callback=ProgressPercentage(filename))
print("Uploading to hutao-dist R2 bucket done", flush=True)

minio_s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("MINIO_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("MINIO_SECRET_KEY"),
    endpoint_url=os.getenv("MINIO_ENDPOINT"),
    config=config
)
minio_bucket_name = "hutao"
print("Uploading to hutao-dist MinIO bucket...", flush=True)
minio_s3_client.upload_file(filename, minio_bucket_name, filename, Callback=ProgressPercentage(filename))
print("Uploading to hutao-dist MinIO bucket done", flush=True)