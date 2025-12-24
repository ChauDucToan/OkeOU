from backend.models import Receipt, Session
from backend import app


def get_sessions(user_id=None, status=None, start_date=None, end_date=None, room_id=None, session_id=None):
    s = Session.query
    if user_id:
        s = s.filter(Session.user_id == user_id)
    if status:
        s = s.filter(Session.status.in_(status))
    if start_date:
        s = s.filter(Session.start_time >= start_date)
    if end_date:
        s = s.filter(Session.start_time <= end_date)
    if room_id:
        s = s.filter(Session.room_id == room_id)
    if session_id:
        s = s.filter(Session.id == session_id)

    return s


def load_session(user_id=None, status=None, start_date=None, end_date=None, page=1):
    s = get_sessions(user_id=user_id,
                     status=status,
                     start_date=start_date,
                     end_date=end_date)

    if page:
        page_size = app.config["PAGE_SIZE"]
        start = (page - 1) * page_size
        s = s.slice(start, start + page_size)

    return s.all()


def get_session_by_receipt_ref(ref):
    receipt = Receipt.query.filter(Receipt.ref == ref).first()
    return get_sessions(session_id=receipt.session_id).first()
