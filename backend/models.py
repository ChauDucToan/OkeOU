from flask_login import UserMixin
from sqlalchemy import Enum, Column, String, JSON, Integer, DateTime, ForeignKey
from enum import Enum as GeneralEnum
import sqlalchemy.sql.functions as func
from sqlalchemy.orm import relationship

from backend import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)


# ===========================================================
#   User
# ===========================================================
class UserRole(GeneralEnum):
    USER = 1
    ADMIN = 2
    STAFF = 3
    CUSTOMER = 4
    LOYAL_CUSTOMER = 5


class User(BaseModel, UserMixin):
    name = Column(String(80), nullable=False)
    avatar = Column(String(100))
    username = Column(String(50), nullable=False, unique=True)
    password = Column(String(50), nullable=False)
    phones = relationship('UserPhone', back_populates='user', lazy=True)
    emails = relationship('UserEmail', back_populates='user', lazy=True)
    role = Column(Enum(UserRole), default=UserRole.USER)

    def __str__(self):
        return self.name


class UserEmail(BaseModel):
    email = Column(String(50), nullable=False, unique=True)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


class UserPhone(BaseModel):
    phone = Column(String(50), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


class LoyalCustomer(User):
    customer_points = Column(Integer, default=0)


class Staff(User):
    identity_card = Column(String(50), nullable=False)
    working_hour = relationship('WorkingHour', backref='staff', lazy=True)


class StaffWorkingHour(BaseModel):
    working_hour = Column(Integer, nullable=False)
    working_date = Column(DateTime, default=func.now())
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)


# ===========================================================
#   Application
# ===========================================================
class ApplicationStatus(GeneralEnum):
    REJECTED = 1
    PENDING = 2
    APPROVED = 3


class Application(BaseModel):
    applicationDetails = Column(JSON, nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    submit_date = Column(DateTime, default=func.now())

    def __str__(self):
        return self.applicationDetails


# ===========================================================
#   Room & Device
# ===========================================================
class RoomStatus(GeneralEnum):
    AVAILABLE = 1
    BOOKED = 2
    OCCUPIED = 3
    MAINTENANCE = 4


class RoomType(BaseModel):
    name = Column(String(80), nullable=False)
    price = Column(String(50), nullable=False)


class Room(BaseModel):
    name = Column(String(80), nullable=False)
    capacity = Column(Integer, nullable=False)
    status = Column(Enum(RoomStatus), default=RoomStatus.AVAILABLE)
    room_type = Column(Integer, ForeignKey(RoomType.id), nullable=False)
    devices = relationship('RoomDevice', backref='room', lazy=True)

    def __str__(self):
        return self.name


class Device(BaseModel):
    name = Column(String(80), nullable=False)
    type = Column(String(80), nullable=False)


class RoomDevice(BaseModel):
    device_id = Column(Integer, ForeignKey(Device.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    install_date = Column(DateTime, default=func.now())


class DeviceMaintenance(BaseModel):
    device_id = Column(Integer, ForeignKey(Device.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)
    maintained_date = Column(DateTime, default=func.now())
    maintained_price = Column(Integer, nullable=False)


# ===========================================================
#   Booking
# ===========================================================
class SessionStatus(GeneralEnum):
    ACTIVE = 1
    PAUSED = 2
    FINISHED = 3


class Booking(BaseModel):
    booking_date = Column(DateTime)
    scheduled_date = Column(DateTime)
    deposit_amount = Column(Integer, nullable=False)
    expiry_date = Column(DateTime)


class Session(BaseModel):
    start_time = Column(DateTime, default=func.now())
    end_time = Column(DateTime)
    session_status = Column(Enum(SessionStatus), default=SessionStatus.ACTIVE)


class UserRoomSession(BaseModel):
    session_id = Column(Integer, ForeignKey(Session.id), nullable=False)
    user_id = Column(Integer, ForeignKey(User.id), nullable=False)
    room_id = Column(Integer, ForeignKey(Room.id), nullable=False)

# ===========================================================
#   Other Services (Food)
# ===========================================================
class Category(BaseModel):
    name = Column(String(80), nullable=False)
    products = relationship('Product', backref='category', lazy=True)

    def __str__(self):
        return self.name

class Product(BaseModel):
    name = Column(String(80), nullable=False)
    description = Column(String(200))
    price = Column(Integer, nullable=False)
    category_id = Column(Integer, ForeignKey(Category.id), nullable=False)

    def __str__(self):
        return self.name