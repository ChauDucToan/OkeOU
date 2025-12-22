from functools import wraps
import hashlib

from flask import redirect, session
from flask_login import current_user


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


def user_role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                return redirect_to_error(403, "You do not have permission to access this page.")
            return f(*args, **kwargs)
        return decorated_function
    return decorator