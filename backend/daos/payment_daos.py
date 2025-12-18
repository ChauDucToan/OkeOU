from backend.models import Receipt, Session, SessionStatus, Room, RoomType, RoomStatus, CustomerCardUsage, PaymentMethod, Order, ReceiptDetails, User, LoyalCustomer
from flask_login import current_user
from backend import app, db
from datetime import datetime

def get_payments(session_id=None):
    r = Receipt.query

    if session_id:
        r = r.filter(Receipt.session_id == session_id)

    return r


def load_payments(session_id=None, page=1):
    r = get_payments(session_id=session_id)

    if page:
        page_size = app.config["PAGE_SIZE"]
        start = (page - 1) * page_size
        r = r.slice(start, start + page_size)
    return r.all()


def count_payments(user_id=None):
    r = Receipt.query
    if user_id:
        r = r.join(Session, Receipt.session_id == Session.id).filter(Session.user_id == user_id)
    return r.count()


def calculate_bill(session_id):
    curr_session = Session.query.get(session_id)

    if not curr_session or curr_session.session_status == SessionStatus.FINISHED:
        return None

    room = Room.query.get(curr_session.room_id)
    room_type = RoomType.query.get(room.room_type)

    end_time = datetime.now()
    if curr_session.end_time:
        end_time = curr_session.end_time
    duration = (end_time - curr_session.start_time).total_seconds() / 3600
    total_room_fee = round(duration * room_type.hourly_price)

    orders = Order.query.filter(Order.session_id == session_id).all()
    service_fee = 0
    order_details = []

    for o in orders:
        for detail in o.details:
            total_price = detail.amount * detail.price_at_time
            service_fee += total_price

            order_details.append({
                "name": detail.product.name,
                "amount": detail.amount,
                "price": detail.price_at_time,
                "total": total_price
            })

        sub_total = total_room_fee + service_fee
        discount = 0
        customer = User.query.get(curr_session.user_id)

        loyal_customer = LoyalCustomer.query.get(curr_session.user_id)
        if loyal_customer:
            point = len(loyal_customer.card_usages)
            if point >= 10:
                discount = round(0.05 * sub_total)
        vat = round(0.1 * (sub_total - discount))

        final_total = sub_total - discount + vat
        return {
            "session_id": curr_session.id,
            "room_name": room.name,
            "customer_name": customer.name,
            "check_in": curr_session.start_time,
            "check_out": end_time,
            "duration_hours": round(duration, 2),
            "hourly_price": room_type.hourly_price,
            "room_fee": total_room_fee,
            "service_details": order_details,
            "service_fee": service_fee,
            "discount": discount,
            "vat": vat,
            "final_total": round(final_total, 0)
        }


def add_bill(bill_details, payment_method="CASH"):
    if bill_details:
        session_id = bill_details['session_id']
        staff_id = current_user.id

        total_room_fee = bill_details['room_fee']
        total_service_fee = bill_details['service_fee']
        # discount_amount = bill_details.get('discount', 0)
        # vat_amount = bill_details.get('vat', 0)

        # Cap nhat gio ket thuc cua phien hat
        session = Session.query.get(session_id)
        if not session:
            raise Exception(f"Không tìm thấy phiên hát với ID {session_id}")

        if session.session_status == SessionStatus.FINISHED:
            raise Exception("Hóa đơn này đã được thanh toán trước đó!")

        session.end_time = bill_details['check_out']
        session.session_status = SessionStatus.FINISHED
        # Cap nhat trang thai phong
        room = Room.query.get(session.room_id)
        room.status = RoomStatus.AVAILABLE
        # Cap nhat diem tich luy cho khach hang
        customer = LoyalCustomer.query.get(session.user_id)
        if customer:
            usage = CustomerCardUsage(loyal_customer_id=customer.id)
            db.session.add(usage)

        method = PaymentMethod.CASH
        # Chua lam
        # if payment_method == "TRANSFER":
        #     method = PaymentMethod.TRANSFER
        # elif payment_method == "CARD":
        #     method = PaymentMethod.CARD

        # Cap nhat hoa don
        receipt = Receipt(session_id=session_id, staff_id=staff_id)
        db.session.add(receipt)

        details = ReceiptDetails(
            receipt=receipt,
            total_room_fee=total_room_fee,
            total_service_fee=total_service_fee,
            # discount_amount=discount_amount,
            # vat_amount=vat_amount,
            payment_method=method
        )

        db.session.add(details)

        db.session.commit()