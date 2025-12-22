from backend.models import Booking


def get_bookings(room_id=None, user_id=None, status=None, 
                 scheduled_start_time=None, scheduled_end_time=None):
    b = Booking.query

    if user_id:
        b = b.filter(Booking.user_id == user_id)

    if room_id:
        b = b.filter(Booking.room_id == room_id)

    if status:
        b = b.filter(Booking.status.in_(status))

    if scheduled_start_time:
        b = b.filter(Booking.scheduled_start_time >= scheduled_start_time)

    if scheduled_end_time:
        b = b.filter(Booking.scheduled_end_time <= scheduled_end_time)

    return b


def count_bookings(user_id=None, status=None, 
                 scheduled_start_time=None, scheduled_end_time=None):
    b = get_bookings(user_id=user_id, status=status,
                     scheduled_start_time=scheduled_start_time,
                     scheduled_end_time=scheduled_end_time)
    return b.count()