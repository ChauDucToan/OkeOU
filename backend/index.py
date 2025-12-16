import math
from flask import render_template, session, redirect, request, jsonify, redirect, request
from flask_login import current_user, login_required, logout_user, login_user

from backend import app, login
from backend import dao
from backend.dao import add_user, auth_user, get_user_by_id
from backend.models import PaymentMethod, UserRole


# ===========================================================
#   Page Redirect
# ===========================================================
@app.route('/')
def index():
    rooms = dao.load_rooms(room_id=request.args.get('room_id'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    return render_template('index.html', rooms=rooms,
                           pages=math.ceil(dao.count_rooms() / app.config['PAGE_SIZE']))


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
    user = get_user_by_id(current_user.id)


    return render_template('profile.html', user=user)


# ===========================================================
#   Products Page
# ===========================================================
@app.route('/products')
def products_preview():
    products = dao.get_products(kw=request.args.get('kw'),
                                category_id=request.args.get('category_id'),
                                page=int(request.args.get('page', 1)))
    categories = dao.get_categories()

    return render_template('products.html', products=products,
                           categories=categories,
                           pages=math.ceil(dao.count_products() / app.config['PAGE_SIZE']))


# ===========================================================
#   Rooms Page
# ===========================================================
@app.route('/rooms')
def rooms_preview():
    rooms = dao.load_rooms(room_id=request.args.get('room_id'),
                           status=request.args.get('status'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    return render_template('rooms.html', rooms=rooms,
                           pages=math.ceil(dao.count_rooms() / app.config['PAGE_SIZE']))

# ===========================================================
#   Payments Page
# ===========================================================
@app.route('/payments')
@login_required
def payments_preview():
    return render_template('payments.html',
                           pages=math.ceil(dao.count_payments(user_id=current_user.id) / app.config['PAGE_SIZE']))


@app.route('/api/payment/caculate', methods=['post'])
@login_required
def caculate_payment():
    if current_user.role != UserRole.STAFF:
        return jsonify({
            'status': 403,
            'err_msg': 'Truy cập bị từ chối! Chỉ nhân viên thu ngân mới có quyền thanh toán.'
        }), 403
    session['bill_detail'] = {}
    room_id = request.json.get('room_id')

    if not room_id:
        return jsonify({'error': 'Thiếu room_id'}), 400
    curr_session = dao.get_current_session(room_id)

    if not curr_session:
        return jsonify({'error': 'Không tìm thấy phiên hát đang hoạt động'}), 404

    bill_detail = dao.calculate_bill(curr_session.id)

    session['bill_detail'] = bill_detail
    return jsonify(bill_detail)


#
@app.route('/api/pay', methods=['post'])
@login_required
def pay():
    try:
        if current_user.role != UserRole.STAFF:
            return jsonify({
                'status': 403,
                'err_msg': 'Truy cập bị từ chối!'
            }), 403
        # Validate cho du lieu dau vao
        data = request.json;
        if data is None:
            return jsonify({'status': 400, 'err_msg': 'Dữ liệu gửi lên không hợp lệ'}), 400
        client_session_id = data.get('session_id')
        try:
            paid_amount = float(data.get('paid_amount', 0))
        except:
            paid_amount = 0

        server_bill = session.get('bill_detail')
        if server_bill is None:
            return jsonify({
                'status': 400,
                'err_msg': 'Phiên giao dịch đã hết hạn hoặc chưa được tạo. Vui lòng tải lại trang!'
            }), 400

        if str(server_bill.get('session_id')) != str(client_session_id):
            return jsonify({
                'status': 400,
                'err_msg': 'Dữ liệu không đồng bộ. Vui lòng tải lại trang!'
            }), 400
        final_total = server_bill.get('final_total', 0)

        if (paid_amount < final_total):
            return jsonify({
                'status': 400,
                'err_msg': 'Không đủ tiền.'
            }), 400

        payment_method = data.get('payment_method', 'CASH').upper()
        if payment_method not in PaymentMethod._member_names_:
            return jsonify({
                'status': 400,
                'err_msg': f'Phương thức thanh toán không hợp lệ.'
            }), 400

        # Tinh lai Bill cho chac
        bill_detail = dao.calculate_bill(session_id=client_session_id)
        dao.add_bill(bill_detail, payment_method)
        del session['bill_detail']

        return jsonify({'status': 200, 'msg': 'Thanh toán thành công!'})
    except Exception as ex:
        return jsonify({'status': 400, 'err_msg': str(ex)}), 400


@app.route('/rooms/')
def rooms():
    return render_template('dashboard/rooms_dashboard.html',
                           get_rooms=dao.load_rooms)


@app.route('/payment/')
def payment_page():
    if current_user.role != UserRole.STAFF:
        return redirect("/rooms")
    data = session.get('bill_detail')
    return render_template('payment/payment.html', bill_detail=data, payment_methods=PaymentMethod)


@login.user_loader
def load_user(pk):
    return get_user_by_id(pk)


if __name__ == '__main__':
    from backend import admin

    app.run(debug=True)
