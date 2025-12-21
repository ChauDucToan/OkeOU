import json
import math
import uuid
from datetime import datetime, timedelta
from flask import render_template, session, jsonify, redirect, request
from flask_login import current_user, login_required, logout_user, login_user

from backend import app, login, db
from backend.daos.category_daos import get_categories
from backend.daos.payment_daos import count_payments
from backend.daos.product_daos import count_products, load_products
from backend.daos.room_daos import count_rooms, load_rooms
from backend.daos.user_daos import add_user, get_users
from backend.daos.session_daos import get_sessions
from backend.models import StaffWorkingHour, UserRole, PaymentMethod, SessionStatus, ReceiptStatus
from backend.utils.user_utils import auth_user
from backend.service.payment.payment_strategy import PaymentStrategyFactory
from service.payment.payment_handler import PaymentHandlerFactory
from utils import payment_utils
from utils.payment_utils import get_bill_before_pay


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
    # if current_user.is_authenticated and current_user.is_staff:
    #     return redirect('/api/logoutcheck')
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
        add_user(name=data.get('name'),
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
    rooms = load_rooms(room_id=request.args.get('room_id'),
                           status=request.args.get('status'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    return render_template('rooms.html', rooms=rooms,
                           pages=math.ceil(count_rooms() / app.config['PAGE_SIZE']))


# ===========================================================
#   Payments Page
# ===========================================================
@app.route('/payments')
@login_required
def payments_preview():
    return render_template('payments.html',
                           pages=math.ceil(count_payments(user_id=current_user.id) / app.config['PAGE_SIZE']))


@app.route('/api/payment/calculate', methods=['post'])
@login_required
def calculate_payment():
    if current_user.is_staff and current_user.is_admin:
        return jsonify({'err_msg': 'Truy cập bị từ chối!'}), 403
    session['bill_detail'] = {}
    room_id = request.json.get('room_id')

    if not room_id:
        return jsonify({'err_msg': 'Thiếu room_id'}), 400
    curr_session = get_sessions(room_id=room_id, status=[SessionStatus.ACTIVE]).first()

    if not curr_session:
        return jsonify({'err_msg': 'Không tìm thấy phiên hát đang hoạt động'}), 404

    bill_detail = get_bill_before_pay(curr_session.id)
    print(bill_detail)

    session['bill_detail'] = bill_detail
    return jsonify(bill_detail)

@app.route('/api/payment/create/<method>/<payment_type>', methods=['post'])
@login_required
def create_payment(method, payment_type):
    try :
        # Tạo mã giao dịch khác nhau cho mỗi giao dịch
        ref = str(uuid.uuid4())
        handler = PaymentHandlerFactory.get_handler(payment_type)
        try:
            strategy = PaymentStrategyFactory.get_strategy(method_name=method, payment_type=payment_type)
        except Exception as ex:
            print(ex)
            return jsonify({'err_msg': 'Phương thức thanh toán không đc hỗ trợ.'}), 400

        amount = handler.init_payment_and_get_amout(request_data=request.json, session_data=session, payment_method=strategy.get_payment_method(), ref=ref)
        result = strategy.create_payment(amount=str(int(amount)), ref=ref)

        if strategy.get_payment_method() == PaymentMethod.CASH:
            paid_amount = float(request.json.get('paid_amount', 0))
            if paid_amount < float(amount):
                return jsonify({'err_msg': 'Không đủ tiền.'}), 400
            strategy.process_payment({"ref": ref})
            if payment_type.upper() == "CHECKOUT":
                del session['bill_detail']
        return jsonify(result), 200
    except Exception as ex :
        print(ex)
        return jsonify({'err_msg': 'Lỗi hệ thống.'}), 500

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
        #     return render_template('xxx', seccess=True)
        return jsonify({'msg': 'Thanh toán thành công'}), 204
    except Exception as e:
        print(e)
        # Tng tự
        # if request.method == 'GET':
        # return render_template('xxx', seccess=False)
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
    return get_users(user_id=pk).first()


if __name__ == '__main__':
    from backend import admin

    app.run(debug=True)
