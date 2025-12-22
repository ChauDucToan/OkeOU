from backend import app
from flask import render_template, request, jsonify, session
from flask_login import current_user, login_required
from backend.daos import order_daos
from backend.utils import order_utils

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
