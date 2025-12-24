from backend.models import Room
from backend import app


def get_rooms(room_id=None, status=None, kw=None):
    r = Room.query
    if kw:
        r = r.filter(Room.name.contains(kw))

    if room_id:
        r = r.filter(Room.id.__eq__(room_id))

    if status:
        r = r.filter(Room.status.in_(status))

    return r


def load_rooms(room_id=None, status=None, kw=None, page=1):
    r = get_rooms(room_id, status, kw)

    if page:
        start = (page - 1) * app.config["PAGE_SIZE"]
        r = r.slice(start, start + app.config["PAGE_SIZE"])
    return r.all()


def count_rooms(status=None, kw=None):
    r = get_rooms(status=status, kw=kw)
    return r.count()


def get_room_price(room_id):
    return Room.query.get(room_id).type.hourly_price
