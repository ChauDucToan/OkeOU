from backend.models import Receipt, Session
from backend import app


def get_payments(session_id=None):
    r = Receipt.query

    if session_id:
        r = r.filter(Receipt.session_id == session_id)

    return r


def load_payments(session_id=None, page=1):
    r = get_payments(session_id=session_id)

    if page:
        page_size = app.config["PAGE_SIZE"]
        start = (page - 1) * page_size
        r = r.slice(start, start + page_size)
    return r.all()


def count_payments(user_id=None):
    r = Receipt.query
    if user_id:
        r = r.join(Session, Receipt.session_id == Session.id).filter(Session.user_id == user_id)
    return r.count()
