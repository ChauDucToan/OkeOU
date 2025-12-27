from flask_login import current_user
from backend.daos.session_daos import get_sessions
from backend.models import Receipt, ReceiptDetails, Session, TransactionStatus
from backend import db, app
from backend.daos.user_daos import get_users
from backend.models import LoyalCustomer, CustomerCardUsage, OrderStatus, Order, Transaction
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from sqlalchemy.orm import joinedload

from backend.utils.order_utils import get_order_details, get_order_price
from backend.utils.room_utils import reset_room_status
from backend.utils.session_utils import get_session_price


def create_receipt(session_id, staff_id, payment_method):
    receipt = Receipt.query.filter(Receipt.session_id == session_id).first()

    if not receipt:
        raise Exception("Không tìm thấy hóa đơn cho phiên hát này.")
    
    if receipt.detail:
        return receipt, receipt.detail.total_room_fee + receipt.detail.total_service_fee

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
        id=receipt.id,
        total_room_fee=total_room_fee,
        total_service_fee=total_order_price,
        discount_rate=discount_rate,
        payment_method=payment_method
    )

    db.session.add(receipt_details)
    try:
        db.session.commit()
        return receipt
    except IntegrityError as ie:
        db.session.rollback()
        raise Exception(str(ie.orig))


def change_transaction_status(ref, status):
    transaction = Transaction.query.filter(Transaction.id == ref).first()
    transaction.status = TransactionStatus[str(status.name)]

    receipt = Receipt.query.filter(Receipt.id == transaction.receipt_id).first()
    receipt.status = status
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi lưu DB: {e}")


def update_transaction_ref(id, ref, amount):
    transaction = Transaction(
        id = ref,
        receipt_id = id,
        amount = amount,
    )
    db.session.add(transaction)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Lỗi lưu DB: {e}")


def get_bill_before_pay(session_id):
    session = Session.query.options(
        joinedload(Session.user),
        joinedload(Session.room),
        joinedload(Session.receipt).joinedload(Receipt.detail),
        joinedload(Session.receipt).subqueryload(Receipt.transactions)
    ).filter(
        Session.id == session_id
    ).first()
    
    receipt = session.receipt
    receipt_detail = receipt.detail
    user = session.user
    total_room_fee = get_session_price(session_id, session.end_time)

    deposit_amount = 0.0
    if receipt.transactions:
        deposit_amount = sum(t.amount for t in receipt.transactions if t.status == TransactionStatus.COMPLETED)

    if deposit_amount > total_room_fee:
        total_room_fee = deposit_amount

    total_order_price = receipt_detail.total_service_fee
    sub_total = total_room_fee + total_order_price

    discount = round(receipt_detail.discount_rate * sub_total)
    vat = round(receipt_detail.vat_rate * (sub_total - discount))
    total_amount = sub_total - discount - deposit_amount + vat

    order_details = get_order_details(session_id)
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
        "final_total": round(total_amount, 0)
    }


def process_payment(session_id):
    session = get_sessions(session_id=session_id).first()
    reset_room_status(room_id=session.room_id)
