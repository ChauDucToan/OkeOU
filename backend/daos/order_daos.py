from backend.models import Order


def get_orders(session_id=None, status=None):
    r = Order.query
    if session_id:
        r = r.filter(Order.session_id == session_id)
    if status:
        r = r.filter(Order.status.in_(status))
    return r.count()