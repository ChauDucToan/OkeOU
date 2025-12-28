from tracemalloc import start

from flask import redirect
from flask.cli import F
from backend.daos.room_daos import get_room_price
from backend.daos.session_daos import get_sessions
from backend.models import Session, SessionStatus
from backend import db
from datetime import datetime

from backend.utils.general_utils import redirect_to_error


def get_session_price(session_id, end_time):
    session = get_sessions(session_id=session_id).first()
    if session:
        room_hourly_price = get_room_price(session.room_id)

        duration_min = (end_time - session.start_time).total_seconds() / 60.0
        
        if duration_min < 5:
            return 0

        duration_hours = duration_min / 60.0
        total_price = int(duration_hours * room_hourly_price)
        return total_price

    return 0


def begin_session(session_id):
    session = get_sessions(session_id=session_id, status=[SessionStatus.BOOKED]).first()
    if session:
        duration = session.end_time - session.start_time
        session.start_time = datetime.now()
        session.end_time = session.start_time + duration
        session.status = SessionStatus.ACTIVE

        current_active_session = get_sessions(
            status=[SessionStatus.ACTIVE],
            room_id=session.room_id,
        ).filter(
            Session.start_time<=session.start_time,
            Session.end_time>=session.start_time,
            Session.id!=session.id
        ).all()

        if current_active_session:
            return False

        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            return False

def finish_session(session_id):
    session = get_sessions(session_id=session_id, status=[SessionStatus.ACTIVE]).first()
    if session:
        session.end_time = datetime.now()
        session.status = SessionStatus.FINISHED

        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            redirect_to_error(500, f"Lỗi lưu phiên hát: {e}")
