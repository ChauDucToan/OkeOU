from datetime import datetime, timedelta
import math

from backend import app, db
from backend.daos.booking_daos import get_bookings
from backend.daos.room_daos import get_rooms, load_rooms
from backend.models import Booking, BookingStatus, Session, SessionStatus
from backend.utils.booking_utils import cancel_pending_booking, create_booking
from backend.utils.general_utils import redirect_to_error
from backend.utils.room_utils import filter_rooms
from flask import render_template, redirect, request, jsonify
from flask_login import current_user


@app.route('/rooms')
def rooms_preview():
    r = request.args
    page = int(r.get('page', 1))
    page_size = app.config['PAGE_SIZE']
    rooms = filter_rooms(room_id=r.get('room_id'),
                         status=r.get('status'),
                         kw=r.get('kw'),
                         capacity=r.get('capacity'),
                         price_max=r.get('price_max'),
                         sort_by=r.get('sort'))

    count = rooms.count()

    if page:
        start = (page - 1) * app.config["PAGE_SIZE"]
        rooms = rooms.slice(start, start + app.config["PAGE_SIZE"])

    return render_template('rooms.html',
                           rooms=rooms.all(),
                           pages=math.ceil(count / page_size))


@app.route('/rooms/<int:room_id>')
def room_detail_preview(room_id):
    rooms = load_rooms(room_id=room_id)

    if not rooms:
        return redirect('/rooms')

    return render_template('room_detail.html', room=rooms[0])


@app.route('/api/bookings/occupies/<int:room_id>')
def room_occupies_preview(room_id):
    cancel_pending_booking()
    date_str = request.args.get('date')

    if date_str:
        start_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        end_date_obj = start_date_obj + timedelta(days=1)

        occ_bookings = get_bookings(room_id=room_id,
                                    status=[BookingStatus.CONFIRMED,
                                            BookingStatus.PENDING,
                                            BookingStatus.COMPLETED],
                                    scheduled_start_time=start_date_obj,
                                    scheduled_end_time=end_date_obj)

        result = {}
        for idx, b in enumerate(occ_bookings):
            result[str(idx)] = [
                b.scheduled_start_time.isoformat(),
                b.scheduled_end_time.isoformat()
            ]

        return jsonify(result)
    return jsonify({})


@app.route('/bookings/<int:booking_id>/payment')
def booking_payment_preview(booking_id):
    booking = Booking.query.get(booking_id)

    if not current_user.is_authenticated:
        current_user.id = 1

    if not booking:
        return redirect_to_error(404, "Booking not found.")

    if booking.user_id != current_user.id:
        return redirect_to_error(403, "You do not have permission to access this booking.")

    if booking.status != BookingStatus.PENDING:
        return redirect_to_error(400, "Booking is not pending payment.")

    expire_time = booking.booking_date + timedelta(minutes=15)
    remain_time = int((expire_time - datetime.now()).total_seconds())

    if remain_time <= 0:
        booking.status = BookingStatus.CANCELLED
        try:
            db.session.commit()
        except Exception as ex:
            print(str(ex))
        return redirect('/rooms')

    room = get_rooms(room_id=booking.room_id)[0]

    return render_template('booking_payment.html', booking=booking,
                           room=room,
                           remain_time=remain_time)


@app.route('/api/bookings/confirm', methods=['POST'])
def confirm_booking():
    try:
        data = request.form

        room_id = data.get('room_id')
        start_str = data.get('start_time')
        end_str = data.get('end_time')
        head_count = data.get('head_count')

        start_time = datetime.strptime(start_str, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(end_str, '%Y-%m-%d %H:%M:%S')

        if not current_user.is_authenticated:
            current_user.id = 1

        booking = create_booking(user_id=current_user.id,
                                 room_id=room_id,
                                 scheduled_start_time=start_time,
                                 scheduled_end_time=end_time,
                                 head_count=int(head_count))

        return jsonify({
            'status': 200,
            'booking_id': booking.id,
            'msg': 'Created booking'
        })

    except Exception as ex:
        return redirect_to_error(500, str(ex))
    

@app.route('/api/booking/update_status', methods=['POST'])
def update_booking_status():
    data = request.json
    booking_id = data.get('booking_id')
    new_status = data.get('status')
    booking = Booking.query.get(booking_id)

    if not booking:
        return jsonify({'err_msg': 'Booking not found'}), 404

    booking.status = BookingStatus[new_status]
    time_del = booking.scheduled_end_time - booking.scheduled_start_time
    amount = time_del.total_seconds() / 3600 * booking.room.type.hourly_price
    booking.deposit_amount = amount


    session = Session(
        start_time=booking.scheduled_start_time,
        end_time=booking.scheduled_end_time,
        user_id=booking.user_id,
        room_id=booking.room_id,
        status= SessionStatus.BOOKED,
    )

    try:
        db.session.add(session)
        db.session.commit()

        return jsonify({'status': 200, 'msg': 'Booking status updated successfully', 'session_id': session.id, 'amount': amount}), 200
    except Exception as ex:
        db.session.rollback()
        return jsonify({'err_msg': str(ex)}), 500