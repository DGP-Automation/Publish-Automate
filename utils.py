import httpx
import os
import hashlib


def calculate_file_sha512(file_path):
    sha512 = hashlib.sha512()
    with open(file_path, 'rb') as f:
        sha512.update(f.read())
    return sha512.hexdigest()


def download_stream_file(url, file_name, headers=None):
    os.makedirs("./cache", exist_ok=True)
    with httpx.stream("GET", url, headers=headers) as r:
        with open(f"./cache/{file_name}", "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)