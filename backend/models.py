from flask_login import UserMixin
from sqlalchemy import Enum, Column, String, JSON, Integer, DateTime, ForeignKey
from enum import Enum as GeneralEnum
import sqlalchemy.sql.functions as func

from backend import db


class BaseModel(db.Model):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)


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
    role = Column(Enum(UserRole), default=UserRole.USER)

    def __str__(self):
        return self.name


class ApplicationStatus(GeneralEnum):
    REJECTED = 1
    PENDING = 2
    APPROVED = 3


class Application(BaseModel):
    applicationDetails = Column(JSON, nullable=False)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    submitDate = Column(DateTime, default=func.now())

    def __str__(self):
        return self.applicationDetails


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
    roomType = Column(Integer, ForeignKey(RoomType.id), nullable=False)

    def __str__(self):
        return self.name
