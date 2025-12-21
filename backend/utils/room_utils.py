from sqlalchemy import desc, asc
from backend.daos.room_daos import get_rooms
from backend.models import Room, RoomType
from backend.models import Room, RoomStatus
from backend import db

def filter_rooms(room_id=None, kw=None, price_min=None, price_max=None
                 , sort_by=None, status=None, capacity=None):
    rooms_price = get_rooms(room_id=room_id, kw=kw, status=status).join(RoomType, RoomType.id == Room.room_type)

    if price_min:
        rooms_price = rooms_price.filter(RoomType.hourly_price >= price_min)
    if price_max:
        rooms_price = rooms_price.filter(RoomType.hourly_price <= price_max)
    if capacity:
        rooms_price = rooms_price.filter(Room.capacity >= capacity)

    if sort_by == 'price_asc':
        rooms_price = rooms_price.order_by(asc(RoomType.hourly_price))
    elif sort_by == 'price_desc':
        rooms_price = rooms_price.order_by(desc(RoomType.hourly_price))
    elif sort_by == 'name_desc':
        rooms_price = rooms_price.order_by(desc(Room.name))
    else:
        rooms_price = rooms_price.order_by(asc(Room.name))
    return rooms_price
def reset_room_status(room_id):
    room = Room.query.get(room_id)
    if room:
        room.status = RoomStatus.AVAILABLE

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(f"Lỗi lưu DB: {e}")