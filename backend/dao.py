import cloudinary.uploader
import cloudinary
from flask_login import current_user

from datetime import timedelta, datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from backend.models import Category, Product, User, Job, Room, RoomStatus, Session, SessionStatus, Order, \
    RoomType, LoyalCustomer, CustomerCardUsage, PaymentMethod, Receipt, ReceiptDetails, UserRole
from backend import app, db
from backend.utils import hash_password


# ===========================================================
#   Rooms dao functions
# ===========================================================
def count_rooms():
    return Room.query.count()


def load_rooms(room_id=None, status=None, kw=None, page=1):
    q = Room.query
    if kw:
        q = q.filter(Room.name.contains(kw))

    if room_id:
        q = q.filter(Room.id.__eq__(room_id))

    if status:
        q = q.filter(Room.status.__eq__(status))

    if page:
        start = (page - 1) * app.config["PAGE_SIZE"]
        q = q.slice(start, start + app.config["PAGE_SIZE"])

    return q.all()

def get_room_price(room_id):
    room = Room.query.get(room_id)
    if room:
        return room.type.hourly_price
    return 0

# ===========================================================
#   Categories dao functions
# ===========================================================
def get_categories():
    return Category.query.all()


# ===========================================================
#   Products dao functions
# ===========================================================
def get_products(kw=None, category_id=None, page=1):
    products = Product.query

    if category_id:
        products = products.filter(Product.category_id == category_id)

    if kw:
        products = products.filter(Product.name.contains(kw))

    if page:
        page_size = app.config["PAGE_SIZE"]
        start = (page - 1) * page_size
        products = products.slice(start, start + page_size)

    return products.all()


def count_products(kw=None, category_id=None):
    p = Product.query

    if category_id:
        p = p.filter(Product.category_id.__eq__(category_id))

    if kw:
        p = p.filter(Product.name.contains(kw))

    return p.count()


# ===========================================================
#   Jobs dao functions
# ===========================================================
def get_jobs():
    return Job.query.all()


# ===========================================================
#   Users dao functions
# ===========================================================
def get_user_by_id(user_id):
    return User.query.get(user_id)


def is_loyal_customer(user_id):
    user = get_user_by_id(user_id)
    loyal_user = LoyalCustomer.query.get(user.id)
    if loyal_user:
        return True
    return False


def auth_user(username, password):
    password = hash_password(password)
    return User.query.filter(User.username == username.strip(),
                             User.password == password).first()


def add_user(name, username, password, email,
             phoneNumber,
             avatar="https://res.cloudinary.com/dtcjixfyd/image/upload/v1765710152/no-profile-picture-15257_kw9uht.png"):
    u = User(name=name,
             username=username.strip(),
             password=hash_password(password),
             email=email,
             role=UserRole.CUSTOMER,
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


def add_loyal_customer(user_id):
    loyal = LoyalCustomer.query.get(user_id)
    if not loyal:
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        counter = count_sessions(user_id=user_id,
                                status=SessionStatus.COMPLETED,
                                start_date=start_date)
        if counter >= 10:
            loyal = LoyalCustomer(id=user_id)
            db.session.add(loyal)
            try:
                db.session.commit()
            except IntegrityError as ie:
                db.session.rollback()
                raise Exception(str(ie.orig))


# ===========================================================
#   Sessions dao functions
# ===========================================================
def count_sessions(user_id=None, status=None, start_date=None, end_date=None):
    r = Session.query
    if user_id:
        r = r.filter(Session.user_id == user_id)
    if status:
        r = r.filter(Session.session_status == status)
    if start_date:
        r = r.filter(Session.start_time >= start_date)
    if end_date:
        r = r.filter(Session.start_time <= end_date)
    return r.count()


def get_user_from_session(session_id):
    session = Session.query.get(session_id)
    if session:
        return get_user_by_id(session.user_id)
    return None


def get_sessions(user_id=None, status=None, page=1):
    s = Session.query
    if user_id:
        s = s.filter(Session.user_id == user_id)
    if status:
        s = s.filter(Session.session_status == status)

    if page:
        page_size = app.config["PAGE_SIZE"]
        start = (page - 1) * page_size
        s = s.slice(start, start + page_size)

    return s.all()


def get_session_price(session_id, end_time):
    session = Session.query.get(session_id)
    if session:
        room_hourly_price = get_room_price(session.room_id)

        if end_time < session.end_time:
            end_time = session.end_time

        duration_hours = timedelta(end_time - session.start_time).total_seconds() / 3600
        total_price = int(duration_hours * room_hourly_price)
        return total_price

    return 0


# ===========================================================
#   Payments dao functions
# ===========================================================
def count_orders(session_id=None, status=None):
    r = Order.query
    if session_id:
        r = r.filter(Order.session_id == session_id)
    if status:
        r = r.filter(Order.status == status)
    return r.count()


def get_order_price(order_id):
    order = Order.query.get(order_id)
    if order:
        total_price = 0
        for detail in order.details:
            total_price += detail.amount * detail.price_at_time
        return total_price
    return 0


# ===========================================================
#   Payments dao functions
# ===========================================================
def count_payments(user_id=None):
    r = Receipt.query
    if user_id:
        r = r.join(Session, Receipt.session_id == Session.id).filter(Session.user_id == user_id)
    return r.count()


def get_payments(session_id=None, page=1):
    r = Receipt.query

    if session_id:
        r = r.filter(Receipt.session_id == session_id)

    if page:
        page_size = app.config["PAGE_SIZE"]
        start = (page - 1) * page_size
        r = r.slice(start, start + page_size)
    return r.all()


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

        db.session.add_all([loyal, card_usage])

    order = Order.query.filter(Order.session_id == session_id, Order.status == OrderStatus.SERVED).first()
    receipt_details = ReceiptDetails(
        receipt_id=receipt.id,
        total_room_fee=get_session_price(session_id, datetime.now()),
        total_service_fee=get_order_price(order.id) if order else 0.0,
        discount_rate= discount_rate,
        payment_method=payment_method
    )

    db.session.add_all([receipt, receipt_details])
    try:
        db.session.commit()
        return receipt
    except IntegrityError as ie:
        db.session.rollback()
        raise Exception(str(ie.orig))

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


def revenue_by_time(time='month', year=datetime.now().year):
    query = ((db.session.query(func.extract(time, Receipt.created_date),
                               func.sum(ReceiptDetails.total_room_fee +
                                        ReceiptDetails.total_service_fee -
                                        ReceiptDetails.discount_amount +
                                        ReceiptDetails.vat_amount))
              .join(ReceiptDetails, ReceiptDetails.receipt_id == Receipt.id))
             .filter(func.extract('year', Receipt.created_date) == year))
    return query.group_by(func.extract(time, Receipt.created_date)).all()


if __name__ == '__main__':
    with app.app_context():
        print(calculate_bill(1))

