import math
from datetime import datetime, timedelta
from tracemalloc import start
from turtle import st

from flask import render_template, redirect, request, jsonify
from flask_login import current_user, login_required, logout_user, login_user

from backend import app, login, db
from backend.daos.booking_daos import get_bookings
from backend.daos.category_daos import get_categories
from backend.daos.payment_daos import count_payments
from backend.daos.product_daos import count_products, load_products
from backend.daos.room_daos import count_rooms, get_rooms, load_rooms
from backend.daos.user_daos import create_user, get_users
from backend.models import Booking, BookingStatus, RoomStatus, StaffWorkingHour
from backend.utils.booking_utils import cancel_pending_booking, create_booking
from backend.utils.user_utils import auth_user


# ===========================================================
#   Page Redirect
# ===========================================================
@app.route('/')
def index():
    rooms = load_rooms(room_id=request.args.get('room_id'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    if current_user.is_authenticated and current_user.is_staff:
        return redirect('/staffs')

    return render_template('index.html', rooms=rooms,
                           pages=math.ceil(count_rooms() / app.config['PAGE_SIZE']))


@app.route('/login')
def loginView():
    return render_template('login.html')


@app.route('/register')
def registerView():
    return render_template('register.html')


# ===========================================================
#   Login & Logout & Register
# ===========================================================
@app.route('/logout')
def logout_process():
    if current_user.is_authenticated and current_user.is_staff:
        return redirect('/api/logoutcheck')
    logout_user()
    return redirect('/')


@app.route('/login', methods=['POST'])
def login_process():
    username = request.form.get('username')
    password = request.form.get('password')

    user = auth_user(username=username, password=password)
    if user:
        login_user(user=user)
    else:
        err_msg = 'Sai tên đăng nhập hoặc mật khẩu!'
        return render_template('login.html', err_msg=err_msg)

    next = request.args.get('next')
    return redirect(next if next else '/')


@app.route('/register', methods=['POST'])
def register_process():
    data = request.form

    password = data.get('password')
    confirm = data.get('confirm')
    email = data.get('email')
    phoneNumber = data.get('phone')

    if password != confirm:
        err_msg = 'Mật khẩu không khớp!'
        return render_template('register.html', err_msg=err_msg)

    try:
        create_user(name=data.get('name'),
                     username=data.get('username'),
                     password=password,
                     email=email,
                     phoneNumber=phoneNumber)
        return redirect('/login')
    except Exception as ex:
        return render_template('register.html', err_msg=str(ex))


# ===========================================================
#   User Profiles Previews
# ===========================================================
@app.route('/profile')
@login_required
def profile_preview():
    user = get_users(user_id=current_user.id)

    return render_template('profile.html', user=user)


# ===========================================================
#   Products Page
# ===========================================================
@app.route('/products')
def products_preview():
    products = load_products(kw=request.args.get('kw'),
                                category_id=request.args.get('category_id'),
                                page=int(request.args.get('page', 1)))
    categories = get_categories()

    return render_template('products.html', products=products,
                           categories=categories,
                           pages=math.ceil(count_products() / app.config['PAGE_SIZE']))


# ===========================================================
#   Rooms Page
# ===========================================================
@app.route('/rooms')
def rooms_preview():
    status = request.args.get('status')
    rooms = load_rooms(room_id=request.args.get('room_id'),
                           status=status if status else [RoomStatus.AVAILABLE],
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    return render_template('rooms.html', rooms=rooms,
                           pages=math.ceil(count_rooms() / app.config['PAGE_SIZE']))


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
                                    booking_status=[BookingStatus.CONFIRMED,
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

    if not booking or booking.user_id != current_user.id:
        return redirect('/rooms')
    
    if booking.booking_status != BookingStatus.PENDING:
         return redirect('/rooms')
    
    expire_time = booking.booking_date + timedelta(minutes=15)
    remain_time = int((expire_time - datetime.now()).total_seconds())

    if remain_time <= 0:
        booking.booking_status = BookingStatus.CANCELLED
        try:
            db.session.commit()
        except Exception as ex:
            print(str(ex))
        return redirect('/rooms')
    
    room = get_rooms(room_id=booking.room_id)[0]

    return render_template('payment.html', booking=booking,
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
        return jsonify({
                'status': 400,
                'msg': str(ex)
            })

# ===========================================================
#   Payments Page
# ===========================================================
@app.route('/payments')
def payments_preview():
    if not current_user.is_authenticated:
        current_user.id = 1
    return render_template('payments.html',
                           pages=math.ceil(count_payments(user_id=current_user.id) / app.config['PAGE_SIZE']))


@login.user_loader
def load_user(pk):
    return get_users(user_id=pk)


# ===========================================================
#   Staffs Page
# ===========================================================
@app.route('/staffs')
@login_required
def staff_preview():
    rooms = load_rooms(room_id=request.args.get('room_id'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    return render_template('/staff/index.html', rooms=rooms,
                           pages=math.ceil(count_rooms() / app.config['PAGE_SIZE']))


@app.route('/staffs/payments')
@login_required
def staff_payments_preview():
    return render_template('/staff/payments.html',
                           pages=math.ceil(count_payments(user_id=current_user.id) / app.config['PAGE_SIZE']))


@app.route('/staffs/products')
def staff_products_preview():
    products = load_products(kw=request.args.get('kw'),
                                category_id=request.args.get('category_id'),
                                page=int(request.args.get('page', 1)))
    categories = get_categories()

    return render_template('/staff/products.html', products=products,
                           categories=categories,
                           pages=math.ceil(count_products() / app.config['PAGE_SIZE']))


@app.route('/staffs/rooms')
def staff_rooms_preview():
    rooms = load_rooms(room_id=request.args.get('room_id'),
                           status=request.args.get('status'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    return render_template('/staff/rooms.html', rooms=rooms,
                           pages=math.ceil(count_rooms() / app.config['PAGE_SIZE']))


@app.route('/api/logincheck')
@login_required
def staff_logincheck():
    if current_user.is_authenticated and current_user.is_staff:
        is_logout = StaffWorkingHour.query.filter(StaffWorkingHour.staff_id == current_user.id
                                                  ,StaffWorkingHour.logout_date is None).first()
        if not is_logout:
            check = StaffWorkingHour(staff_id=current_user.id)

            db.session.add(check)
            db.session.commit()

            return redirect('/staffs')

    return jsonify({
        'status': 400,
        'err_msg': 'Kiểm tra lại quyền của người dùng'
    })


@app.route('/api/logoutcheck')
@login_required
def staff_logoutcheck():
    if current_user.is_authenticated and current_user.is_staff:
        check = StaffWorkingHour.query.filter(StaffWorkingHour.staff_id == current_user.id
                                              ,StaffWorkingHour.logout_date is None).first()
        if check:
            check.logout_date = datetime.now()

            db.session.add(check)
            db.session.commit()

            logout_user()
            return redirect('/')

    return jsonify({
        'status': 400,
        'err_msg': 'Kiểm tra lại quyền của người dùng'
    })


@login.user_loader
def load_user(pk):
    user = get_users(user_id=pk).first()
    return user


if __name__ == '__main__':
    from backend import admin

    app.run(debug=True)
