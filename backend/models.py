from flask_login import UserMixin
from sqlalchemy import Enum, Column, String, Integer, DateTime, ForeignKey, Float, Boolean, CheckConstraint
from enum import Enum as GenericEnum
from datetime import datetime
from sqlalchemy.orm import relationship

from backend import db, app


class BaseModel(db.Model):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)


# ===========================================================
#   User
# ===========================================================
class UserRole(GenericEnum):
    USER = 1
    ADMIN = 2
    STAFF = 3
    CUSTOMER = 4

class User(BaseModel, UserMixin):
    name = Column(String(80), nullable=False)
    avatar = Column(String(100))
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(64), nullable=False)
    phone = Column(String(16), nullable=False)
    email = Column(String(128), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER)
    active = Column(Boolean, default=True)

    def __str__(self):
        return self.name

    @property
    def is_staff(self):
        return self.role == UserRole.STAFF

    @property
    def is_admin(self):
        return self.role == UserRole.ADMIN

    @property
    def is_customer(self):
        return self.role == UserRole.CUSTOMER


class LoyalCustomer(User):
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    card_usages = relationship('CustomerCardUsage', lazy=True)


class CustomerCardUsage(BaseModel):
    loyal_customer_id = Column(Integer, ForeignKey(LoyalCustomer.id), nullable=False)
    usage_date = Column(DateTime, default=datetime.now)


class Staff(User):
    id = Column(Integer, ForeignKey(User.id), primary_key=True)
    identity_card = Column(String(50), nullable=False)
    working_history = relationship('StaffWorkingHour', backref='staff', lazy=True)


class StaffWorkingHour(BaseModel):
    working_hour = Column(Integer, nullable=False)
    working_date = Column(DateTime, default=datetime.now)
    staff_id = Column(Integer, ForeignKey(Staff.id), nullable=False)
    bonus = Column(Float, default=0.0)


# ===========================================================
#   Application
# ===========================================================
class ApplicationStatus(GenericEnum):
    REJECTED = 1
    PENDING = 2
    APPROVED = 3


class Job(BaseModel):
    title = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    target_quantity = Column(Integer, default=1)
    hired_quantity = Column(Integer, default=0)
    salary_range = Column(String(100))

    is_active = Column(Boolean, default=True)
    created_date = Column(DateTime, default=datetime.now)
    deadline = Column(DateTime)

    applications = relationship('Application', backref='jobs', lazy=True)

    def __str__(self):
        return self.title

class Application(BaseModel):

    job_id = Column(Integer, ForeignKey(Job.id), nullable=False)

    full_name = Column(String(80), nullable=False)
    email = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    cv_file = Column(String(200))

    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    submit_date = Column(DateTime, default=datetime.now)

    def __str__(self):
        return self.full_name

# ===========================================================
#   Room & Device
# ===========================================================
class RoomStatus(GenericEnum):
    AVAILABLE = 1
    BOOKED = 2
    OCCUPIED = 3
    MAINTENANCE = 4


class RoomType(BaseModel):
    name = Column(String(80), nullable=False)
    hourly_price = Column(Integer, nullable=False)


class Room(BaseModel):
    name = Column(String(80), nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(Enum(RoomStatus), default=RoomStatus.AVAILABLE)
    image = Column(String(100))
    room_type = Column(Integer, ForeignKey(RoomType.id), nullable=False)

    type = relationship('RoomType', backref='rooms', lazy=True)

    def __str__(self):
        return self.name

# ===========================================================
#   Booking
# ===========================================================
class SessionStatus(GenericEnum):
    ACTIVE = 1
    FINISHED = 2


class Booking(BaseModel):
    booking_date = Column(DateTime, default=datetime.now)
    scheduled_start_time = Column(DateTime, nullable=False)
    scheduled_end_time = Column(DateTime, nullable=False)
    head_count = Column(Integer, default=1, nullable=False)
    deposit_amount = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)

    # MySQL khong dung cai rang buoc kia duoc
    __table_args__ = (
        CheckConstraint(
            'scheduled_end_time > scheduled_start_time',
            name='chk_booking_time_order'
        ),
        CheckConstraint(
            'head_count > 0 AND head_count <= 15',
            name='chk_booking_head_count'
        ),
    )

# If the user want to transfer room then set the SessionStatus.FINISHED
# and create new session
#
# To be extendable, session can be use in order table in case the customer
# want to eat some food
class Session(BaseModel):
    start_time = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime)
    session_status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)

    __table_args__ = (
        CheckConstraint(
            'end_time > start_time',
            name='chk_session_time_order'
        ),
    )

# ===========================================================
#   Other Services (Food)
# ===========================================================
class OrderStatus(GenericEnum):
    PENDING = 1
    SERVED = 2


class Category(BaseModel):
    name = Column(String(80), nullable=False)
    products = relationship('Product', backref='category', lazy=True)

    def __str__(self):
        return self.name


class Product(BaseModel):
    name = Column(String(80), nullable=False)
    description = Column(String(255))
    price = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)
    created_date = Column(DateTime, default=datetime.now)
    image = Column(String(100))
    amount = Column(Integer, nullable=False)
    unit = Column(String(100), nullable=False)
    active = Column(Boolean, default=True)
    orders = relationship('ProductOrder', backref='product', lazy=True)

    def __str__(self):
        return self.name


class ProductOrder(BaseModel):
    product_id = Column(Integer, ForeignKey(Product.id), primary_key=True)
    order_id = Column(Integer, ForeignKey('order.id'), primary_key=True)
    amount = Column(Integer, nullable=False)
    price_at_time = Column(Integer, nullable=False)


class Order(BaseModel):
    session_id = Column(Integer, ForeignKey(Session.id), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    details = relationship('ProductOrder', backref='order', lazy=True)


# ===========================================================
#   Payments
# ===========================================================
class PaymentMethod(GenericEnum):
    CASH = 1
    TRANSFER = 2
    CARD = 3


class Receipt(BaseModel):
    session_id = Column(Integer, ForeignKey(Session.id), nullable=False, unique=True)
    staff_id = Column(Integer, ForeignKey(Staff.id), nullable=True)

    created_date = Column(DateTime, default=datetime.now())
    details = relationship('ReceiptDetails', backref='receipt', lazy=True)


class ReceiptDetails(BaseModel):
    receipt_id = Column(Integer, ForeignKey(Receipt.id), nullable=False)

    total_room_fee = Column(Float, default=0.0)
    total_service_fee = Column(Float, default=0.0)
    discount_rate = Column(Float, default=0.0)
    vat_rate = Column(Float, default=0.1)

    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()