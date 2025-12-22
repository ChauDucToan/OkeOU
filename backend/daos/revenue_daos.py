import time
from sqlalchemy import func

from backend.models import  Product,  Room,  Session, SessionStatus, Order, \
    RoomType, Receipt, ReceiptDetails, ProductOrder
from backend import db, app

from datetime import datetime


def get_total_amount(time_unit='day'):
    current_date = datetime.now()
    query = (db.session.query(func.sum(ReceiptDetails.total_room_fee + ReceiptDetails.total_service_fee))
                    .join(Receipt, ReceiptDetails.id == Receipt.id)
                    .join(Session, Session.id == Receipt.session_id)
                    .filter(func.extract('year', Session.end_time) == current_date.year))

    if time_unit == 'month':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
    elif time_unit == 'week':
        query = query.filter(func.week(Session.end_time, 3) == current_date.date().isocalendar()[1])
    elif time_unit == 'day':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
        query = query.filter(func.extract('day', Session.end_time) == current_date.day)

    result = query.first()[0]
    return int(result) if result is not None else 0

def count_orders(time_unit='day'):
    current_date = datetime.now()

    query = (db.session.query(func.count(Order.id))
                    .join(Session, Order.session_id == Session.id)
                    .filter(Session.session_status == SessionStatus.FINISHED)
                    .filter(func.extract('year', Session.end_time) == current_date.year))
    
    if time_unit == 'month':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
    elif time_unit == 'week':
        query = query.filter(func.week(Session.end_time, 3) == current_date.date().isocalendar()[1])
    elif time_unit == 'day':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
        query = query.filter(func.extract('day', Session.end_time) == current_date.day)

    result = query.first()[0]
    return result if result is not None else 0

def count_sessions(time_unit='day'):
    current_date = datetime.now()
    query = (db.session.query(func.count(Session.id))
                      .filter(Session.session_status == SessionStatus.FINISHED)
                      .filter(func.extract('year', Session.end_time) == current_date.year))

    if time_unit == 'month':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
    elif time_unit == 'week':
        query = query.filter(func.week(Session.end_time, 3) == current_date.date().isocalendar()[1])
    elif time_unit == 'day':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
        query = query.filter(func.extract('day', Session.end_time) == current_date.day)

    result = query.first()[0]
    return result if result is not None else 0

def count_customers(time_unit='day'):
    current_date = datetime.now()

    query = (db.session.query(func.count(Session.user_id))
             .filter(Session.session_status == SessionStatus.FINISHED)
             .filter(func.extract('year', Session.end_time) == current_date.year))

    if time_unit == 'month':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
    elif time_unit == 'week':
        query = query.filter(func.week(Session.end_time, 3) == current_date.date().isocalendar()[1])
    elif time_unit == 'day':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
        query = query.filter(func.extract('day', Session.end_time) == current_date.day)

    result = query.first()[0]
    return result if result is not None else 0

def revenue_by_time(time_unit='day'):
    total_amount = get_total_amount(time_unit)

    cnt_orders = count_orders(time_unit)

    cnt_customers = count_customers(time_unit)

    cnt_sessions = count_sessions(time_unit)

    return {
        "total_amount": total_amount,
        "count_orders": cnt_orders,
        "count_sessions": cnt_sessions,
        "count_customers": cnt_customers,
    }

def revenue_by_room_name(time_unit='day'):
    current_date = datetime.now()

    query = ((db.session.query(Session.room_id, Room.name,
                               func.sum(ReceiptDetails.total_room_fee +
                                        ReceiptDetails.total_service_fee))
              .join(Receipt, Session.id == Receipt.session_id)
              .join(ReceiptDetails, ReceiptDetails.id == Receipt.id)
              .join(Room, Room.id == Session.room_id)
              .filter(Session.session_status == SessionStatus.FINISHED)
              .filter(func.extract('year', Session.end_time) == current_date.year)))

    if time_unit == 'month':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
    elif time_unit == 'week':
        query = query.filter(func.week(Session.end_time, 3) == current_date.date().isocalendar()[1])
    elif time_unit == 'day':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
        query = query.filter(func.extract('day', Session.end_time) == current_date.day)

    return query.group_by(Session.room_id).all()


def revenue_by_room_type(time_unit='day'):
    current_date = datetime.now()

    query = ((db.session.query(RoomType.name,
                               func.sum(ReceiptDetails.total_room_fee +
                                        ReceiptDetails.total_service_fee))
              .join(Receipt, ReceiptDetails.id == Receipt.id)
              .join(Session, Session.id == Receipt.session_id)
              .join(Room, Room.id == Session.room_id)
              .filter(Session.session_status == SessionStatus.FINISHED))
             .join(RoomType, RoomType.id == Room.room_type)
             .filter(func.extract('year', Session.end_time) == current_date.year))

    if time_unit == 'month':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
    elif time_unit == 'week':
        query = query.filter(func.week(Session.end_time, 3) == current_date.date().isocalendar()[1])
    elif time_unit == 'day':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
        query = query.filter(func.extract('day', Session.end_time) == current_date.day)

    return query.group_by(RoomType.name).all()


def revenue_by_product(time_unit='day'):
    current_date = datetime.now()

    query = ((db.session.query(Product.name,
                               func.sum(ProductOrder.amount * ProductOrder.price_at_time))
              .join(Product, ProductOrder.product_id == Product.id)
              .join(Order, Order.id == ProductOrder.order_id)
              .join(Session, Session.id == Order.session_id))
             .filter(Session.session_status == SessionStatus.FINISHED)
             .filter(func.extract('year', Session.end_time) == current_date.year))

    if time_unit == 'month':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
    elif time_unit == 'week':
        query = query.filter(func.week(Session.end_time, 3) == current_date.date().isocalendar()[1])
    elif time_unit == 'day':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
        query = query.filter(func.extract('day', Session.end_time) == current_date.day)

    return query.group_by(Product.name).all()

if __name__ == '__main__':
    current_date = datetime.now()
    with app.app_context():
        print(count_customers(time_unit='day'))