import hashlib


def hash_password(password: str) -> str:
    if not password:
        raise ValueError('Password cannot be empty')
    return str(hashlib.sha256(password.encode('utf-8')).hexdigest())
