from datetime import timedelta
from backend.daos.room_daos import get_room_price
from backend.models import Session


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