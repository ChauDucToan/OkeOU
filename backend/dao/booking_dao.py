from backend.models import Booking, BookingStatus, Room, RoomStatus, Session, SessionStatus
from backend import db
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timedelta


def get_bookings(room_id=None, user_id=None, booking_status=None, 
                 scheduled_start_time=None, scheduled_end_time=None):
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

    return b


def count_bookings(user_id=None, booking_status=None, 
                 scheduled_start_time=None, scheduled_end_time=None):
    b = get_bookings(user_id=user_id, booking_status=booking_status,
                     scheduled_start_time=scheduled_start_time,
                     scheduled_end_time=scheduled_end_time)
    return b.count()


def cancel_pending_booking():
    limit_time = datetime.now() - timedelta(minutes=15)

    pending_booking = get_bookings(booking_status = BookingStatus.PENDING).filter(Booking.booking_date < limit_time).all()

    for booking in pending_booking:
        booking.booking_status = BookingStatus.CANCELLED

    try:
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        raise Exception(str(ie.orig))

def create_booking(scheduled_start_time, scheduled_end_time, head_count, user_id, room_id, deposit_amount=0):
    cancel_pending_booking()

    existing_booking = get_bookings(room_id=room_id,
                                    booking_status=[BookingStatus.CONFIRMED, BookingStatus.PENDING]).filter(
                                        Booking.scheduled_start_time < scheduled_end_time,
                                        Booking.scheduled_end_time > scheduled_start_time
                                    ).with_for_update().first()
    if existing_booking:
        raise Exception("Room is already booked for the selected time slot.")

    room = Room.query.get(room_id)
    if room.capacity < head_count:
        raise Exception("Head count exceeds")

    booking = Booking(
        scheduled_start_time=scheduled_start_time,
        scheduled_end_time=scheduled_end_time,
        head_count=head_count,
        user_id=user_id,
        room_id=room_id,
        deposit_amount=deposit_amount
    )

    db.session.add(booking)
    try:
        db.session.commit()
        return booking
    except IntegrityError as ie:
        db.session.rollback()
        raise Exception(str(ie.orig))
    

def confirm_booking(booking_id):
    booking = Booking.query.get(booking_id)
    if booking:
        room = Room.query.get(booking.room_id)
        if not room:
            raise Exception("Room not found")
        
        room.status = RoomStatus.BOOKED

        if booking.booking_status != BookingStatus.PENDING:
            raise Exception("Only pending bookings")

        booking.booking_status = BookingStatus.CONFIRMED
        try:
            db.session.commit()
            return booking
        except IntegrityError as ie:
            db.session.rollback()
            raise Exception(str(ie.orig))
        
        
def convert_booking_to_session(booking_id):
    booking = Booking.query.get(booking_id)
    if booking:
        if booking.booking_status != BookingStatus.CONFIRMED:
            raise Exception("Only confirmed bookings")

        session = Session(
            start_time=booking.scheduled_start_time,
            end_time=booking.scheduled_end_time,
            user_id=booking.user_id,
            room_id=booking.room_id,
            session_status=SessionStatus.ACTIVE
        )
        booking.booking_status = BookingStatus.COMPLETED

        db.session.add(session)
        try:
            db.session.commit()
            return session
        except IntegrityError as ie:
            db.session.rollback()
            raise Exception(str(ie.orig))