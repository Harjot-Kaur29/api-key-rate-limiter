import secrets
import hashlib


def generate_api_key_value(prefix: str = "sk", length: int = 32) -> str:
    random_string = secrets.token_hex(length)

    return f"{prefix}_{random_string}"

def hash_api_key(api_key: str) -> str:
    return hashlib.sha256(api_key.encode('utf-8')).hexdigest()