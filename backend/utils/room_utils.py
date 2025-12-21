from backend.models import Room, RoomStatus
from backend import db

def reset_room_status(room_id):
    room = Room.query.get(room_id)
    if room:
        room.status = RoomStatus.AVAILABLE

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi lưu DB: {e}")