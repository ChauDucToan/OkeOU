from backend.models import Order


def get_orders(session_id=None, status=None):
    r = Order.query
    if session_id:
        r = r.filter(Order.session_id == session_id)
    if status:
        r = r.filter(Order.status.in_(status))
    return r.count()


def get_order_price(order_id):
    order = Order.query.get(order_id)
    if order:
        total_price = 0
        for detail in order.details:
            total_price += detail.amount * detail.price_at_time
        return total_price
    return 0