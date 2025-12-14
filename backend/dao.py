import cloudinary
from flask_login import current_user

from sqlalchemy.exc import IntegrityError
from backend.models import Category, Product, User, Job, Room, RoomStatus, Session, SessionStatus, Order, product_order, \
    RoomType, LoyalCustomer, CustomerCardUsage, PaymentMethod, Receipt, ReceiptDetails
from backend import app, db
from backend.utils import hash_password

from datetime import datetime


def get_categories():
    return Category.query.all()


def get_products(kw=None, category_id=None, page=1):
    products = Product.query

    if category_id:
        products = products.filter(Product.category_id == category_id)

    if kw:
        products = products.filter(Product.name.contains(kw))

    if page:
        page = int(page)
        page_size = app.config.get("PAGE_SIZE", 10)
        start = (page - 1) * page_size
        products = products.slice(start, start + page_size)

    return products.all()


def get_jobs():
    return Job.query.all()


def count_products():
    return Product.query.count()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def auth_user(username, password):
    password = hash_password(password)
    return User.query.filter(User.username == username.strip(),
                             User.password == password).first()


def add_user(name, username, password, email, 
            phoneNumber,
            avatar = "https://res.cloudinary.com/dtcjixfyd/image/upload/v1765710152/no-profile-picture-15257_kw9uht.png"):
    u = User(name=name,
             username=username.strip(),
             password=hash_password(password),
             email=email,
             phone=phoneNumber)

    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.avatar = res.get('secure_url')

    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        raise Exception(str(ie.orig))

def load_rooms(status=None):
    query = Room.query
    if status:
        query = query.filter(Room.status==status)
    return query.all()

def get_current_session(room_id):
    return Session.query.filter(Session.room_id==room_id,
                                Session.session_status==SessionStatus.ACTIVE).first()

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
        details = db.session.query(
            Product.name,
            product_order.c.amount,
            product_order.c.price_at_time
        ).join(Product).filter(product_order.c.order_id == o.id).all()

        for name, amount, price_at_time in details:
            total_price = int(amount) * float(price_at_time)
            service_fee += total_price
            order_details.append(
                {
                    "name": name,
                    "amount": amount,
                    "price": price_at_time,
                    "total": total_price
                }
            )

        sub_total = total_room_fee + service_fee
        discount = 0
        customer = User.query.get(curr_session.user_id)

        loyal_customer = LoyalCustomer.query.get(curr_session.user_id)
        if loyal_customer:
            point = loyal_customer.customer_points
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
        discount_amount = bill_details.get('discount', 0)
        vat_amount = bill_details.get('vat', 0)

        # Cap nhat gio ket thuc cua phien hat
        session = Session.query.get(session_id)
        if not session:
            raise Exception(f"Không tìm thấy phiên hát với ID {session_id}")

        if session.session_status == SessionStatus.FINISHED:
            raise Exception("CẢNH BÁO: Hóa đơn này đã được thanh toán trước đó!")

        session.end_time = bill_details['check_out']
        session.session_status = SessionStatus.FINISHED
        # Cap nhat trang thai phong
        room = Room.query.get(session.room_id)
        room.status = RoomStatus.AVAILABLE
        # Cap nhat diem tich luy cho khach hang
        customer = LoyalCustomer.query.get(session.user_id)
        if customer:
            customer.customer_points += 1
            usage = CustomerCardUsage(loyal_customer_id=customer.id, amount=bill_details['final_total'])
            db.session.add(usage)

        method = PaymentMethod.CASH
        # Chua lam
        # if payment_method == "TRANSFER":
        #     method = PaymentMethod.TRANSFER
        # elif payment_method == "CARD":
        #     method = PaymentMethod.CARD

        # Cap nhat hoa don
        receipt = Receipt(user_id=session.user_id, session_id=session_id, staff_id=staff_id)
        db.session.add(receipt)

        details = ReceiptDetails(
            receipt=receipt,
            total_room_fee=total_room_fee,
            total_service_fee=total_service_fee,
            discount_amount=discount_amount,
            vat_amount=vat_amount,
            payment_method=method
        )


        db.session.add(details)

        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        print(calculate_bill(1))

