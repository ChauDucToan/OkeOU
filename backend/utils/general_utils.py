import hashlib

from flask import redirect, session


def hash_password(password: str) -> str:
    if not password:
        raise ValueError('Password cannot be empty')
    return str(hashlib.sha256(password.encode('utf-8')).hexdigest())


def redirect_to_error(status_code: int, err_msg: str):
    session['error_payload'] = {
        'code': status_code,
        'msg': err_msg
    }
    return redirect('/error')