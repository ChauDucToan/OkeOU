from flask_login import current_user
from backend.daos.payment_daos import get_payments
from backend.daos.session_daos import get_sessions
from backend.models import Receipt, ReceiptDetails, Session
from backend import db
from backend.daos.user_daos import get_users
from backend.models import LoyalCustomer, CustomerCardUsage, OrderStatus, Order
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from backend.utils.order_utils import get_order_details, get_order_price
from backend.utils.room_utils import reset_room_status
from backend.utils.session_utils import finish_session, get_session_price


def create_receipt(session_id, staff_id, payment_method):
    receipt = Receipt(session_id=session_id, staff_id=staff_id)
    db.session.add(receipt)
    db.session.flush()

    order = Order.query.filter(Order.session_id == session_id, Order.status == OrderStatus.SERVED).first()
    session = Session.query.get(session_id)
    total_room_fee = get_session_price(session_id, datetime.now())
    total_order_price = get_order_price(order.id) if order else 0.0

    user = get_users(user_id=session.user_id).first()
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


def change_receipt_status(ref, status):
    receipt = Receipt.query.filter(Receipt.ref == ref).first()
    receipt.status = status
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi lưu DB: {e}")


def update_receipt_ref(id, ref):
    receipt = Receipt.query.get(id)
    receipt.ref = ref
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi lưu DB: {e}")


def get_bill_before_pay(session_id):
    session = get_sessions(session_id=session_id).first()
    finish_session(session_id)

    receipt = get_payments(session_id=session_id).first()
    receipt_detail = receipt.details
    order_details = get_order_details(session_id=session_id)

    total_room_fee = get_session_price(session_id, session.end_time)
    total_order_price = receipt_detail.total_service_fee
    sub_total = round(total_room_fee + total_order_price)

    user = get_users(user_id=session.user_id).first()
    discount = round(receipt.details.discount_rate * sub_total)
    vat = round(receipt_detail.vat_rate * (sub_total - discount))
    deposit_amount = session.deposit_amount
    total_amout = sub_total - discount - deposit_amount + vat

    return {
        "session_id": session_id,
        "customer_name": user.name,
        "staff_id": current_user.id,
        "check_in": session.start_time,
        "check_out": datetime.now(),
        "room_fee": total_room_fee,
        "deposit_amount": deposit_amount,
        "service_fee": total_order_price,
        "service_details": order_details,
        "discount": discount,
        "vat": vat,
        "final_total": round(total_amout, 0)
    }


def process_payment(session_id):
    session = get_sessions(session_id=session_id).first()
    reset_room_status(room_id=session.room_id)
