import hashlib


def hash_password(password):
    return str(hashlib.sha256(password.encode('utf-8')).hexdigest())