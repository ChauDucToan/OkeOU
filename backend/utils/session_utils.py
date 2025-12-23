from backend.daos.room_daos import get_room_price
from backend.daos.session_daos import get_sessions
from backend.models import SessionStatus
from backend import db
from datetime import datetime

from backend.utils.general_utils import redirect_to_error


def get_session_price(session_id, end_time):
    session = get_sessions(session_id=session_id).first()
    if session:
        room_hourly_price = get_room_price(session.room_id)

        if end_time < session.end_time:
            end_time = session.end_time

        duration_hours = (end_time - session.start_time).total_seconds() / 3600
        total_price = int(duration_hours * room_hourly_price)
        return total_price

    return 0


def finish_session(session_id):
    session = get_sessions(session_id=session_id, status=[SessionStatus.ACTIVE]).first()
    if session and not session.end_time:
        session.end_time = datetime.now()
        session.status = SessionStatus.FINISHED

        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            redirect_to_error(500, f"Lỗi lưu phiên hát: {e}")