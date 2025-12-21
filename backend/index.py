import math
from datetime import datetime, timedelta

from flask import render_template, redirect, request, jsonify, session
from flask_login import current_user, login_required, logout_user, login_user

from functools import wraps
from backend import app, login, db
from backend.daos.booking_daos import get_bookings
from backend.daos.category_daos import get_categories
from backend.daos.payment_daos import count_payments
from backend.daos.product_daos import count_products, load_products
from backend.daos.room_daos import count_rooms, get_rooms, load_rooms
from backend.daos.session_daos import get_sessions
from backend.daos.user_daos import create_user, get_users
from backend.daos import order_daos
from backend.models import Booking, BookingStatus, StaffWorkingHour, UserRole, SessionStatus, PaymentMethod
from backend.utils.booking_utils import cancel_pending_booking, create_booking
from backend.utils.general_utils import redirect_to_error
from backend.utils.room_utils import filter_rooms
from backend.utils.user_utils import auth_user
from backend.utils.payment_utils import get_bill_before_pay
from backend.utils import order_utils
from backend.service.payment.payment_handler import PaymentHandlerFactory
from backend.service.payment.payment_strategy import PaymentStrategyFactory


# ===========================================================
#   User role decorators
# ===========================================================
def user_role_required(roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                return redirect_to_error(403, "You do not have permission to access this page.")
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ===========================================================
#   Error Redirect
# ===========================================================
@app.route('/error')
def error_view():
    error_payload = session.pop('error_payload', None)

    if error_payload:
        code = error_payload.get('code')
        msg = error_payload.get('msg')
        return render_template('error.html', status_code=code, err_msg=msg)
    else:
        return redirect_to_error(200, "No error information available.")

# ===========================================================
#   Page Redirect
# ===========================================================
@app.route('/')
def index():
    rooms = load_rooms(page=1)
    
    products = load_products(page=1)

    if current_user.is_authenticated and current_user.is_staff:
        return redirect('/staffs')

    return render_template('index.html', rooms=rooms, products=products)


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
    session.pop('order', None)
    return redirect('/')


@app.route('/login', methods=['POST'])
def login_process():
    username = request.form.get('username')
    password = request.form.get('password')

    user = auth_user(username=username, password=password)
    if user:
        login_user(user=user)
    else:
        err_msg = 'Username or password is incorrect!'
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
        err_msg = 'Passwords do not match!'
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
    user = get_users(user_id=current_user.id).first()

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
                           pages=math.ceil(count_products(request.args.get('kw'), request.args.get('category_id')) / app.config['PAGE_SIZE']))


# ===========================================================
#   Rooms Page
# ===========================================================
@app.route('/rooms/')
def rooms_preview():
    r = request.args
    page=int(r.get('page', 1))
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

    if not booking:
        return redirect_to_error(404, "Booking not found.")
    
    if booking.user_id != current_user.id:
        return redirect_to_error(403, "You do not have permission to access this booking.")
    
    if booking.booking_status != BookingStatus.PENDING:
        return redirect_to_error(400, "Booking is not pending payment.")
    
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
        return redirect_to_error(500, str(ex))

# ===========================================================
#   Payments Page
# ===========================================================
@app.route('/payments')
def payments_preview():
    if not current_user.is_authenticated:
        current_user.id = 1
    return render_template('payments.html',
                           pages=math.ceil(count_payments(user_id=current_user.id) / app.config['PAGE_SIZE']))


@app.route('/api/payment/calculate', methods=['post'])
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def calculate_payment():
    session['bill_detail'] = {}
    room_id = request.json.get('room_id')

    if not room_id:
        return jsonify({'err_msg': 'Thiếu room_id'}), 400
    curr_session = get_sessions(room_id=room_id, status=[SessionStatus.ACTIVE]).first()

    if not curr_session:
        return jsonify({'err_msg': 'Không tìm thấy phiên hát đang hoạt động'}), 404

    bill_detail = get_bill_before_pay(curr_session.id)

    session['bill_detail'] = bill_detail
    return jsonify(bill_detail)

@app.route('/api/payment/create/<method>/<payment_type>', methods=['post'])
@login_required
def create_payment(method, payment_type):
    # Tạo mã giao dịch khác nhau cho mỗi giao dịch
    import uuid
    ref = str(uuid.uuid4())
    handler = PaymentHandlerFactory.get_handler(payment_type)
    try:
        strategy = PaymentStrategyFactory.get_strategy(method_name=method, payment_type=payment_type)
    except Exception as ex:
        print(ex)
        return jsonify({'err_msg': 'Phương thức thanh toán không đc hỗ trợ.'}), 400

    amount = handler.init_payment_and_get_amout(request_data=request.json, session_data=session,
                                                payment_method=strategy.get_payment_method(), ref=ref)
    result = strategy.create_payment(amount=str(int(float(amount))), ref=ref)

    if strategy.get_payment_method() == PaymentMethod.CASH:
        paid_amount = float(request.json.get('paid_amount', 0))
        if paid_amount < float(amount):
            return jsonify({'err_msg': 'Không đủ tiền.'}), 400
        strategy.process_payment({"ref": ref})
        if payment_type.upper() == "CHECKOUT":
            del session['bill_detail']
    return jsonify(result), 200
    # try :
    #     # Tạo mã giao dịch khác nhau cho mỗi giao dịch
    #     import uuid
    #     ref = str(uuid.uuid4())
    #     handler = PaymentHandlerFactory.get_handler(payment_type)
    #     try:
    #         strategy = PaymentStrategyFactory.get_strategy(method_name=method, payment_type=payment_type)
    #     except Exception as ex:
    #         print(ex)
    #         return jsonify({'err_msg': 'Phương thức thanh toán không đc hỗ trợ.'}), 400
    #
    #     amount = handler.init_payment_and_get_amout(request_data=request.json, session_data=session, payment_method=strategy.get_payment_method(), ref=ref)
    #     result = strategy.create_payment(amount=str(int(float(amount))), ref=ref)
    #
    #     if strategy.get_payment_method() == PaymentMethod.CASH:
    #         paid_amount = float(request.json.get('paid_amount', 0))
    #         if paid_amount < float(amount):
    #             return jsonify({'err_msg': 'Không đủ tiền.'}), 400
    #         strategy.process_payment({"ref": ref})
    #         if payment_type.upper() == "CHECKOUT":
    #             del session['bill_detail']
    #     return jsonify(result), 200
    # except Exception as ex :
    #     print(ex)
    #     return jsonify({'err_msg': 'Lỗi hệ thống.'}), 500

@app.route('/api/ipn/<method>/<payment_type>', methods=['post', 'get'])
def return_ipn(method, payment_type):
    try :
        if request.method == 'POST':
            data = request.json
        else:
            data = request.args.to_dict()
        print(data)

        strategy = PaymentStrategyFactory.get_strategy(method_name=method, payment_type=payment_type)
        strategy.process_payment(data)
        # Xử lý thêm để hiện giao diện kêt quả thanh toán
        # if request.method == 'GET':
        #     return render_template('xxx', success=True)
        return jsonify({'msg': 'Thanh toán thành công'}), 204
    except Exception as e:
        print(e)
        # Tng tự
        # if request.method == 'GET':
        # return render_template('xxx', success=False)
        return jsonify({'err_msg': "Lỗi hệ thống!!!"}), 500

@app.route('/rooms-dashboard/')
def rooms():
    return render_template('dashboard/rooms_dashboard.html',
                           get_rooms=load_rooms)

@app.route('/payment/')
def payment_page():
    if current_user.role != UserRole.STAFF  and current_user.role != UserRole.ADMIN:
        return redirect("/rooms-dashboard")
    data = session.get('bill_detail')
    return render_template('payment/payment.html', bill_detail=data, payment_methods=PaymentMethod)


@login.user_loader
def load_user(pk):
    return get_users(user_id=pk)


# ===========================================================
#   Staffs Page
# ===========================================================
@app.route('/staffs')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_preview():
    rooms = load_rooms(room_id=request.args.get('room_id'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    return render_template('/staff/index.html', rooms=rooms,
                           pages=math.ceil(count_rooms() / app.config['PAGE_SIZE']))


@app.route('/staffs/payments')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_payments_preview():
    return render_template('/staff/payments.html',
                           pages=math.ceil(count_payments(user_id=current_user.id) / app.config['PAGE_SIZE']))


@app.route('/staffs/products')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_products_preview():
    products = load_products(kw=request.args.get('kw'),
                                category_id=request.args.get('category_id'),
                                page=int(request.args.get('page', 1)))
    categories = get_categories()

    return render_template('/staff/products.html', products=products,
                           categories=categories,
                           pages=math.ceil(count_products() / app.config['PAGE_SIZE']))


@app.route('/staffs/rooms')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_rooms_preview():
    r = request.args
    page=int(r.get('page', 1))
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

    return render_template('/staff/rooms.html', 
                           rooms=rooms.all(),
                           pages=math.ceil(count / page_size))


@app.route('/api/logincheck')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_logincheck():
    is_logout = StaffWorkingHour.query.filter(StaffWorkingHour.staff_id == current_user.id
                                                ,StaffWorkingHour.logout_date is None).first()
    if not is_logout:
        check = StaffWorkingHour(staff_id=current_user.id)

        db.session.add(check)
        db.session.commit()

        return redirect('/staffs')


@app.route('/api/logoutcheck')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_logoutcheck():
    check = StaffWorkingHour.query.filter(StaffWorkingHour.staff_id == current_user.id
                                            ,StaffWorkingHour.logout_date is None).first()
    if check:
        check.logout_date = datetime.now()

        db.session.commit()

    logout_user()
    return redirect('/')



@login.user_loader
def load_user(pk):
    user = get_users(user_id=pk).first()
    return user

# ===========================================================
#   Orders Page
# ===========================================================
@app.route('/orders')
def orders_preview():
    return render_template('orders.html')

@app.route('/api/orders', methods=['post'])
def add_to_order():
    if current_user.is_authenticated:
        data = request.json

        order = session.get('order')

        if not order:
            order = {}

        id = str(data.get('id'))
        image = data.get('image')
        name = data.get('name')
        price = data.get('price')
        amount = data.get('amount')

        product = order_utils.check_amount_product(id)
        if id in order:
            order[id]["quantity"] += 1
            if order[id]["quantity"] > 30:
                return jsonify({'err_msg': 'Đặt vượt qua số lượng cho phép'}), 400
            if product.amount < order[id]["quantity"]:
                return jsonify({'err_msg': 'Dịch vụ đặt vượt quá số lượng còn lại'}), 400
        else:
            order[id] = {
                'id': id,
                'image': image,
                'name': name,
                'quantity': 1,
                'price': price,
                'amount': amount
            }
        session['order'] = order
        return jsonify(order_utils.stats_order(order)), 200
    else:
        return jsonify({'err_msg': 'Vui lòng đăng nhập trước khi đặt dịch vụ'}), 400

@app.route('/api/orders/<id>', methods=['put'])
def update_order(id):
    order = session.get('order')

    if order and id in order:
        quantity = int(request.json.get('quantity'))
        if quantity > 30:
            return jsonify({'err_msg': 'Số lượng giới hạn là 30'}), 400
        product = order_utils.check_amount_product(order[id]['id'])
        if product.amount < quantity:
            return jsonify({'err_msg': 'Dịch vụ đặt vượt quá số lượng còn lại'}), 400
        order[id]['quantity'] = quantity

    session['order'] = order
    return jsonify(order_utils.stats_order(order)), 200

@app.route('/api/orders/<id>', methods=['delete'])
def delete_order(id):
    order = session.get('order')

    if order and id in order:
        del order[id]

    session['quantity'] = order

    if session.get('order') == {}:
        del session['order']

    return jsonify(order_utils.stats_order(order))

@app.context_processor
def common_responses():
    return{
        'stats_order': order_utils.stats_order(session.get('order'))
    }

@app.route('/api/order_process', methods=['post'])
@login_required
def order_process():
    sess = order_utils.get_verify_session(current_user.id)
    if not sess:
        return jsonify({'err_msg': 'Bạn chưa đặt phòng hát'}), 400

    order = session.get('order')
    if not order:
        return jsonify({'err_msg': 'Bạn chưa đặt dịch vụ'}), 400

    try:
        ord = order_daos.create_order(session_id=sess.id)
        order_utils.add_order(order=session.get('order'), ord=ord)
        del session['order']

        return jsonify({'message': 'Đặt dịch vụ thành công'}), 200
    except ValueError as ex:
        return jsonify({'err_msg': str(ex)}), 400
    except Exception as ex:
        return jsonify({'err_msg': str(ex)}), 500


if __name__ == '__main__':
    from backend import admin

    app.run(debug=True)
