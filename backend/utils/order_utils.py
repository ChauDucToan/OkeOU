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
            db.session.execute(r)
        db.session.commit()