from datetime import datetime, timedelta
from pymysql import IntegrityError
from backend import db
from backend.daos.booking_daos import get_bookings
from backend.models import Booking, BookingStatus, Room, RoomStatus, Session, SessionStatus


def cancel_pending_booking():
    limit_time = datetime.now() - timedelta(minutes=15)

    pending_booking = get_bookings(status=[BookingStatus.PENDING]).filter(Booking.booking_date < limit_time)

    pending_booking.update({Booking.status: BookingStatus.CANCELLED}, synchronize_session=False)

    try:
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        raise Exception(str(ie.orig))


def create_booking(scheduled_start_time, scheduled_end_time, head_count, user_id, room_id, deposit_amount=0):
    cancel_pending_booking()

    existing_booking = get_bookings(room_id=room_id,
                                    status=[BookingStatus.CONFIRMED, BookingStatus.PENDING]).filter(
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

        if booking.status != BookingStatus.PENDING:
            raise Exception("Only pending bookings")

        booking.status = BookingStatus.CONFIRMED
        try:
            db.session.commit()
            return booking
        except IntegrityError as ie:
            db.session.rollback()
            raise Exception(str(ie.orig))
        
        
def convert_booking_to_session(booking_id):
    booking = Booking.query.get(booking_id)
    if booking:
        if booking.status != BookingStatus.CONFIRMED:
            raise Exception("Only confirmed bookings")

        session = Session(
            start_time=booking.scheduled_start_time,
            end_time=booking.scheduled_end_time,
            user_id=booking.user_id,
            room_id=booking.room_id,
            status=SessionStatus.BOOKED,
            deposit_amount=booking.deposit_amount
        )
        booking.status = BookingStatus.COMPLETED

        db.session.add(session)
        try:
            db.session.commit()
            return session
        except IntegrityError as ie:
            db.session.rollback()
            raise Exception(str(ie.orig))