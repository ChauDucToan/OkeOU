from re import U
from sqlalchemy import desc, func

from backend.models import Product, Room, Session, SessionStatus, Order, \
    RoomType, Receipt, ReceiptDetails, ProductOrder, Staff, StaffWorkingHour, User
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
             .filter(Session.status == SessionStatus.FINISHED)
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
             .filter(Session.status == SessionStatus.FINISHED)
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
             .filter(Session.status == SessionStatus.FINISHED)
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
                                        ReceiptDetails.total_service_fee).label('total_revenue'))
              .join(Receipt, Session.id == Receipt.session_id)
              .join(ReceiptDetails, ReceiptDetails.id == Receipt.id)
              .join(Room, Room.id == Session.room_id)
              .filter(Session.status == SessionStatus.FINISHED)
              .filter(func.extract('year', Session.end_time) == current_date.year)))

    if time_unit == 'month':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
    elif time_unit == 'week':
        query = query.filter(func.week(Session.end_time, 3) == current_date.date().isocalendar()[1])
    elif time_unit == 'day':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
        query = query.filter(func.extract('day', Session.end_time) == current_date.day)

    return query.group_by(Session.room_id).order_by(desc('total_revenue')).all()


def revenue_by_room_type(time_unit='day'):
    current_date = datetime.now()

    query = ((db.session.query(RoomType.name,
                               func.sum(ReceiptDetails.total_room_fee +
                                        ReceiptDetails.total_service_fee).label('total_revenue'))
              .join(Receipt, ReceiptDetails.id == Receipt.id)
              .join(Session, Session.id == Receipt.session_id)
              .join(Room, Room.id == Session.room_id)
              .filter(Session.status == SessionStatus.FINISHED))
             .join(RoomType, RoomType.id == Room.room_type)
             .filter(func.extract('year', Session.end_time) == current_date.year))

    if time_unit == 'month':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
    elif time_unit == 'week':
        query = query.filter(func.week(Session.end_time, 3) == current_date.date().isocalendar()[1])
    elif time_unit == 'day':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
        query = query.filter(func.extract('day', Session.end_time) == current_date.day)

    return query.group_by(RoomType.name).order_by(desc('total_revenue')).all()


def revenue_by_product(time_unit='day'):
    current_date = datetime.now()

    query = ((db.session.query(Product.name,
                               func.sum(ProductOrder.amount * ProductOrder.price_at_time).label('total_revenue'))
              .join(Product, ProductOrder.product_id == Product.id)
              .join(Order, Order.id == ProductOrder.order_id)
              .join(Session, Session.id == Order.session_id))
             .filter(Session.status == SessionStatus.FINISHED)
             .filter(func.extract('year', Session.end_time) == current_date.year))

    if time_unit == 'month':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
    elif time_unit == 'week':
        query = query.filter(func.week(Session.end_time, 3) == current_date.date().isocalendar()[1])
    elif time_unit == 'day':
        query = query.filter(func.extract('month', Session.end_time) == current_date.month)
        query = query.filter(func.extract('day', Session.end_time) == current_date.day)

    return query.group_by(Product.name).order_by(desc('total_revenue')).all()


def get_top_customers():
    query = (db.session.query(User.name,
                              func.count(Session.id).label('session_count'))
             .join(User, User.id == Session.user_id)
             .filter(Session.status == SessionStatus.FINISHED)
             .filter(User.id != 1)
             .group_by(Session.user_id)
             .order_by(desc('session_count')))

    return query.all()


def get_staffs_receipt_count():
    query = (db.session.query(Receipt.staff_id,
                              func.count(Receipt.id).label('receipt_count'))
             .group_by(Receipt.staff_id)
             .order_by(desc('receipt_count')))

    return query.all()


def get_staffs_working_hours():
    seconds_diff = func.unix_timestamp(StaffWorkingHour.logout_date) - func.unix_timestamp(StaffWorkingHour.login_date)

    total_hours_expr = (func.sum(seconds_diff) / 3600).label('total_hours')
    query = (db.session.query(Staff.name,
                              total_hours_expr)
             .filter(StaffWorkingHour.logout_date.isnot(None))
             .group_by(StaffWorkingHour.staff_id)
             .order_by(desc('total_hours')).join(Staff, Staff.id == StaffWorkingHour.staff_id))

    return query.all()


if __name__ == '__main__':
    current_date = datetime.now()
    with app.app_context():
        print(count_customers(time_unit='day'))
