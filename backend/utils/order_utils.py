from backend.models import Order


def get_order_price(order_id):
    order = Order.query.get(order_id)
    if order:
        total_price = 0
        for detail in order.details:
            total_price += detail.amount * detail.price_at_time
        return total_price
    return 0

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
