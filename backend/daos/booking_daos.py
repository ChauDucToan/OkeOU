from backend.models import Booking


def get_bookings(room_id=None, user_id=None, booking_status=None, 
                 scheduled_start_time=None, scheduled_end_time=None,
                 ref=None):
    b = Booking.query

    if user_id:
        b = b.filter(Booking.user_id == user_id)

    if room_id:
        b = b.filter(Booking.room_id == room_id)

    if booking_status:
        b = b.filter(Booking.booking_status.in_(booking_status))

    if scheduled_start_time:
        b = b.filter(Booking.scheduled_start_time >= scheduled_start_time)

    if scheduled_end_time:
        b = b.filter(Booking.scheduled_end_time <= scheduled_end_time)
    if ref:
        b = b.filter(Booking.ref == ref)

    return b


def count_bookings(user_id=None, booking_status=None, 
                 scheduled_start_time=None, scheduled_end_time=None):
    b = get_bookings(user_id=user_id, booking_status=booking_status,
                     scheduled_start_time=scheduled_start_time,
                     scheduled_end_time=scheduled_end_time)
    return b.count()