from backend.models import Session
from backend import app
from backend.dao.room_dao import get_room_price
from datetime import timedelta


def get_sessions(user_id=None, status=None, start_date=None, end_date=None):
    s = Session.query
    if user_id:
        s = s.filter(Session.user_id == user_id)
    if status:
        s = s.filter(Session.session_status.in_(status))
    if start_date:
        s = s.filter(Session.start_time >= start_date)
    if end_date:
        s = s.filter(Session.start_time <= end_date)

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

def get_session_price(session_id, end_time):
    session = Session.query.get(session_id)
    if session:
        room_hourly_price = get_room_price(session.room_id)

        if end_time < session.end_time:
            end_time = session.end_time

        duration_hours = timedelta(end_time - session.start_time).total_seconds() / 3600
        total_price = int(duration_hours * room_hourly_price)
        return total_price

    return 0