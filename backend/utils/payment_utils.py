from backend.models import Receipt, ReceiptDetails
from backend import db
from backend.daos.session_daos import get_session_price
from backend.daos.user_daos import get_user_from_session
from backend.daos.order_daos import get_order_price
from backend.models import LoyalCustomer, CustomerCardUsage, OrderStatus, Order
from sqlalchemy.exc import IntegrityError
from datetime import datetime


def create_receipt(session_id, staff_id, payment_method):
    receipt = Receipt(session_id=session_id, staff_id=staff_id)
    db.session.add(receipt)
    db.session.flush()

    user = get_user_from_session(session_id)
    discount_rate = 0.0
    loyal = LoyalCustomer.query.get(user.id) if user else None
    if loyal:
        discount_rate = 0.05

        card_usage = CustomerCardUsage(
            loyal_customer_id=loyal.id,
        )

        db.session.add(card_usage)

    order = Order.query.filter(Order.session_id == session_id, Order.status == OrderStatus.SERVED).first()
    receipt_details = ReceiptDetails(
        receipt_id=receipt.id,
        total_room_fee=get_session_price(session_id, datetime.now()),
        total_service_fee=get_order_price(order.id) if order else 0.0,
        discount_rate=discount_rate,
        payment_method=payment_method
    )

    db.session.add_all([receipt, receipt_details])
    try:
        db.session.commit()
        return receipt
    except IntegrityError as ie:
        db.session.rollback()
        raise Exception(str(ie.orig))