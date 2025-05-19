import json
import hashlib


def generate_etag(data: str) -> str:
    if type(data) == dict:
        data = json.dumps(data)

    return hashlib.md5(data.encode()).hexdigest()