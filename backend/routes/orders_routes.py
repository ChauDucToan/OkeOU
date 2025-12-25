from backend import app
from flask import request, jsonify, session
from flask_login import current_user, login_required
from backend.daos import order_daos
from backend.utils import order_utils


@app.route('/api/orders', methods=['post'])
def add_to_order():
    '''
    {
        '<int:session_id>': {
            '<int:product_id>': {
                'image': 'link',
                'name': 'name',
                'price': price,
                'amount': amount
            }
        } 
    }

    So the working is:
    1. Get the current cart from session_id
    2. If session_id not in cart, create an empty dict for it
    3. Check if product_id is already in the cart for that session_id
        - If yes, increase the quantity by 1
        - If no, add the product with quantity 1
    4. Save the updated cart back to session
    5. Return the stats of the current cart for that session_id
    '''

    if current_user.is_authenticated:
        data = request.json

        session_id = str(data.get('session_id'))
        if not session_id:
            return jsonify({'err_msg': 'Thiếu thông tin làm việc'}), 400

        cart = session.get('order', {})
        if session_id not in cart:
            cart[session_id] = {}

        order = cart[session_id]

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

        cart[session_id] = order
        session['order'] = cart
        return jsonify(order_utils.stats_order(order)), 200
    else:
        return jsonify({'err_msg': 'Vui lòng đăng nhập trước khi đặt dịch vụ'}), 400


@app.route('/api/orders/<id>', methods=['put'])
def update_order(id):
    data = request.json
    session_id = str(data.get('session_id'))
    quantity = int(data.get('quantity'))

    cart = session.get('order', {})

    if session_id in cart and id in cart[session_id]:
        order = cart[session_id]

        if quantity > 30:
            return jsonify({'err_msg': 'Số lượng giới hạn là 30'}), 400
        product = order_utils.check_amount_product(order[id]['id'])
        if product.amount < quantity:
            return jsonify({'err_msg': 'Dịch vụ đặt vượt quá số lượng còn lại'}), 400
        order[id]['quantity'] = quantity

        session['order'] = cart
        return jsonify(order_utils.stats_order(order)), 200
    return jsonify({'err_msg': 'Không tìm thấy sản phẩm'}), 400


@app.route('/api/orders/<id>', methods=['delete'])
def delete_order(id):
    data = request.json
    session_id = str(data.get('session_id'))

    cart = session.get('order', {})

    if session_id in cart and id in cart[session_id]:
        del cart[session_id][id]

        stats = order_utils.stats_order(cart[session_id])

        if not cart[session_id]:
            del cart[session_id]

        session['order'] = cart
        return jsonify(stats), 200

    return jsonify({'total_quantity': 0, 'total_amount': 0})


@app.route('/api/order_process', methods=['post'])
@login_required
def order_process():
    data = request.json
    session_id = data.get('session_id')

    if not session_id:
        return jsonify({'err_msg': 'Không xác định được phiên làm việc'}), 400

    order = session.get('order', {})
    current_order = order.get(str(session_id))

    if not current_order:
        return jsonify({'err_msg': 'Bạn chưa thêm dịch vụ vào giỏ hàng'}), 400

    try:
        ord = order_daos.create_order(session_id=int(session_id))
        order_utils.add_order(current_order, ord)

        del order[str(session_id)]
        session['order'] = order

        return jsonify({'msg': 'Đặt dịch vụ thành công'}), 200
    except ValueError as ve:
        return jsonify({'err_msg': str(ve)}), 400
    except Exception as e:
        return jsonify({'err_msg': str(e)}), 500


@app.template_filter('cart_stats')
def cart_stats_filter(cart_dict):
    return order_utils.stats_order(cart_dict)


@app.context_processor
def common_responses():
    cart = session.get('order', {})
    total_quantity = 0
    total_amount = 0

    if cart:
        for session_cart in cart.values():
            stats = order_utils.stats_order(session_cart)
            total_quantity += stats['total_quantity']
            total_amount += stats['total_amount']

    return {
        'stats_order': {
            'total_quantity': total_quantity,
            'total_amount': total_amount
        }
    }
