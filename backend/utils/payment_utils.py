from backend.models import Receipt, ReceiptDetails, Session
from backend import db
from backend.daos.user_daos import get_users
from backend.models import LoyalCustomer, CustomerCardUsage, OrderStatus, Order
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from backend.utils.order_utils import get_order_price
from backend.utils.session_utils import get_session_price


def sum_monthly_revenue(year):
    pass

def create_receipt(session_id, staff_id, payment_method):
    receipt = Receipt(session_id=session_id, staff_id=staff_id)
    db.session.add(receipt)
    db.session.flush()

    order = Order.query.filter(Order.session_id == session_id, Order.status == OrderStatus.SERVED).first()
    session = Session.query.get(session_id)
    total_room_fee = get_session_price(session_id, datetime.now())
    total_order_price = get_order_price(order.id) if order else 0.0

    user = get_users(user_id = session.user_id).first()
    discount_rate = 0.0
    loyal = LoyalCustomer.query.get(user.id) if user else None
    if loyal:
        discount_rate = 0.05

        card_usage = CustomerCardUsage(
            loyal_customer_id=loyal.id,
        )

        db.session.add(card_usage)

    receipt_details = ReceiptDetails(
        receipt_id=receipt.id,
        total_room_fee=total_room_fee,
        total_service_fee=total_order_price,
        discount_rate=discount_rate,
        payment_method=payment_method
    )

    db.session.add_all([receipt, receipt_details])
    try:
        db.session.commit()
        return receipt, session.deposit_amount - total_room_fee - total_order_price
    except IntegrityError as ie:
        db.session.rollback()
        raise Exception(str(ie.orig))