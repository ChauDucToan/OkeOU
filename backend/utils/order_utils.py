from backend.models import Order, OrderStatus, Session, SessionStatus, ProductOrder, Product
from backend import db

def get_order_price(order_id):
    order = Order.query.get(order_id)
    if order:
        total_price = 0
        for detail in order.details:
            total_price += detail.amount * detail.price_at_time
        return total_price
    return 0

def get_verify_session(user_id):
    sessionn = Session.query.filter(
        Session.user_id == user_id,
        Session.status == SessionStatus.ACTIVE
    ).first()

    return sessionn

def check_amount_product(id):
    return Product.query.get(id)

def add_order(order, ord):
    if order:
        for o in order.values():
            product = check_amount_product(o['id'])
            if product.amount < o['quantity']:
                raise ValueError(f"Số lượng còn lại của sản phẩm {product.name} là {product.amount}")
            product.amount -= o['quantity']

            r = ProductOrder(
                order_id = ord.id,
                product_id = o['id'],
                amount = o['quantity'],
                price_at_time = o['price']
            )
            db.session.add(r)
            if product.amount == 0:
                product.active = False
        db.session.commit()

def stats_order(order):
    total_quantity, total_amount = 0, 0

    if order:
        for o in order.values():
            total_quantity += o['quantity']
            total_amount += o['quantity'] * o['price']

    return{
        'total_quantity': total_quantity,
        'total_amount': total_amount
    }


def get_order_details(session_id):
    orders = Order.query.filter(Order.session_id == session_id, Order.status == OrderStatus.SERVED).all()
    order_details = []
    for order in orders:
        for detail in order.details:
            total_price = detail.amount * detail.price_at_time
            order_details.append({
                "name": detail.product.name,
                "amount": detail.amount,
                "price": detail.price_at_time,
                "total": total_price
            })

    return order_details