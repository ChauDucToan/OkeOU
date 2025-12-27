from sqlalchemy import func, select
from backend.models import Order, OrderStatus, Session, SessionStatus, ProductOrder, Product
from backend import db, app


def get_order_price(order_id):
    total_price = db.session.query(
        func.sum(ProductOrder.amount * ProductOrder.price_at_time)
    ).filter(
        ProductOrder.order_id == order_id
    ).scalar()
    return total_price or 0


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
                order_id=ord.id,
                product_id=o['id'],
                amount=o['quantity'],
                price_at_time=o['price']
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

    return {
        'total_quantity': total_quantity,
        'total_amount': total_amount
    }


def get_order_details(session_id):
    orders = select(
        Product.name,
        ProductOrder.amount,
        ProductOrder.price_at_time,
        (ProductOrder.amount * ProductOrder.price_at_time).label('total')
    ).select_from(ProductOrder
    ).join(Order, Order.id == ProductOrder.order_id
    ).join(Product, ProductOrder.product_id == Product.id
    ).where(Order.session_id == session_id, Order.status == OrderStatus.SERVED)

    total = db.session.execute(orders).all()

    order_details = []
    for detail in total:
        order_details.append({
            "name": detail.name,
            "amount": detail.amount,
            "price": detail.price_at_time,
            "total": detail.total
        })

    return order_details

if __name__ == "__main__":
    with app.app_context():
        print(get_order_details(1321))
