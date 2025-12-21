from backend.models import Order, Session, SessionStatus, ProductOrder
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
        Session.session_status == SessionStatus.ACTIVE
    ).first()

    return sessionn

def add_order(order, ord):
    if order:
        for o in order.values():
            r = ProductOrder(
                order_id = ord.id,
                product_id = o['id'],
                amount = o['quantity'],
                price_at_time = o['price']
            )
            db.session.add(r)
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


def get_order_details(order:Order):
    order_details = []
    for detail in order.details:
        total_price = detail.amount * detail.price_at_time
        order_details.append({
            "name": detail.product.name,
            "amount": detail.amount,
            "price": detail.price_at_time,
            "total": total_price
        })

    return order_details
