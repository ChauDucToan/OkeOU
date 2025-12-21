from backend.models import Order, OrderStatus
from backend import db

def get_orders(session_id=None, status=None):
    r = Order.query
    if session_id:
        r = r.filter(Order.session_id == session_id)
    if status:
        r = r.filter(Order.status.in_(status))
    return r.count()

def create_order(session_id):
    ord = Order.query.filter(
        Order.session_id == session_id,
        Order.status == OrderStatus.PENDING
    ).first()

    if not ord:
        ord = Order(session_id=session_id)
        db.session.add(ord)
        db.session.commit()
    return ord