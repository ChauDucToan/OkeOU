from backend import app
from flask import render_template, request, jsonify, session, redirect
from flask_login import current_user, login_required
from backend.daos.room_daos import load_rooms
from backend.daos.session_daos import get_sessions
from backend.daos.payment_daos import count_payments
from backend.models import PaymentMethod, UserRole
from backend.services.payment.payment_handler import PaymentHandlerFactory
from backend.services.payment.payment_strategy import PaymentStrategyFactory
from backend.utils.general_utils import user_role_required
from backend.utils.payment_utils import create_receipt, get_bill_before_pay
from backend.utils.session_utils import SessionStatus, finish_session
import math


@app.route('/payments')
def payments_preview():
    if not current_user.is_authenticated:
        current_user.id = 1
    return render_template('payments.html',
                           pages=math.ceil(count_payments(user_id=current_user.id) / app.config['PAGE_SIZE']))


@app.route('/payment')
def payment_page():
    if current_user.role != UserRole.STAFF and current_user.role != UserRole.ADMIN:
        return redirect("/room-dashboard")
    data = session.get('bill_detail')
    return render_template('payment.html', bill_detail=data, payment_methods=PaymentMethod)


@app.route('/api/payment/calculate', methods=['post'])
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def calculate_payment():
    session['bill_detail'] = {}
    session_id = request.json.get('session_id')

    if not session_id:
        return jsonify({'err_msg': 'Thiếu session_id'}), 400
    curr_session = get_sessions(session_id=session_id, status=[SessionStatus.ACTIVE]).first()
    if not curr_session:
        return jsonify({'err_msg': 'Không tìm thấy phiên hát đang hoạt động'}), 404

    bill = create_receipt(session_id=session_id, staff_id=current_user.id, payment_method=PaymentMethod.CASH)
    bill_detail = get_bill_before_pay(bill[0].id)
    finish_session(curr_session.id)

    session['bill_detail'] = bill_detail
    return jsonify(bill_detail)


@app.route('/api/payment/create/<method>/<payment_type>', methods=['post'])
@login_required
def create_payment(method, payment_type):
    import uuid
    ref = str(uuid.uuid4())
    handler = PaymentHandlerFactory.get_handler(payment_type)
    try:
        strategy = PaymentStrategyFactory.get_strategy(method_name=method, payment_type=payment_type)
    except Exception as ex:
        print(ex)
        return jsonify({'err_msg': 'Phương thức thanh toán không đc hỗ trợ.'}), 400

    amount = handler.init_payment_and_get_amount(request_data=request.form, session_data=session,
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

@app.route('/api/ipn/<method>/<payment_type>', methods=['post', 'get'])
def return_ipn(method, payment_type):
    try:
        if request.method == 'POST':
            data = request.json
        else:
            data = request.args.to_dict()
        print(data)

        strategy = PaymentStrategyFactory.get_strategy(method_name=method, payment_type=payment_type)
        strategy.process_payment(data)
        if request.method == 'GET':
            return render_template('payment_result.html', data=data)
        return jsonify({'msg': 'Thanh toán thành công'}), 204
    except Exception as e:
        print(e)
        # Tng tự
        if request.method == 'GET':
            return render_template('payment_result.html', data=data)
        return jsonify({'err_msg': "Lỗi hệ thống!!!"}), 500


@app.route('/rooms-dashboard')
def rooms():
    return render_template('/room_dashboard.html',
                           get_rooms=load_rooms)