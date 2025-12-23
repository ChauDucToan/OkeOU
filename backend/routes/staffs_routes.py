import math
from datetime import datetime
from flask import redirect, render_template, request, session
from flask_login import current_user, logout_user
from backend import app, db
from backend.daos.category_daos import get_categories
from backend.daos.payment_daos import count_payments
from backend.daos.product_daos import count_products, load_products
from backend.daos.session_daos import get_sessions
from backend.models import SessionStatus, StaffWorkingHour, User, UserRole, Session
from backend.utils.general_utils import user_role_required
from backend.utils.room_utils import filter_rooms

@app.route('/staffs')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_preview():
    data = request.args
    page = int(data.get("page", 1))
    page_size = app.config['PAGE_SIZE']

    sessions = get_sessions(status=[SessionStatus.ACTIVE])

    count = sessions.count()
    if page:
        start = (page - 1) * page_size
        sessions = sessions.slice(start, start + page_size)

    return render_template('/staff/index.html', sessions=sessions.all(),
                           pages=math.ceil(count / page_size), current_page=page)


@app.route('/staffs/orders')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_orders_preview():
    return render_template('/staff/orders.html')


@app.route('/staffs/sessions')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_sessions_preview():
    data = request.args
    page = int(data.get("page", 1))
    page_size = app.config['PAGE_SIZE']

    sessions = get_sessions(start_date=data.get("start_date"), end_date=data.get("end_date"))
    
    status = data.get('status')
    if status:
        status_enum = SessionStatus[status]
        sessions = sessions.filter(Session.status == status_enum)

    user_name = data.get('kw')
    if user_name:
        sessions = sessions.join(User).filter(User.name.contains(user_name))

    count = sessions.count()
    if page:
        start = (page - 1) * page_size
        sessions = sessions.slice(start, start + page_size)

    return render_template('/staff/sessions.html', sessions=sessions.all(),
                           pages=math.ceil(count / page_size), current_page=page)


@app.route('/staffs/payments')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_payments_preview():
    return render_template('/staff/payments.html',
                           pages=math.ceil(count_payments(user_id=current_user.id) / app.config['PAGE_SIZE']))


@app.route('/staffs/<int:session_id>/order')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_products_preview(session_id):
    products = load_products(kw=request.args.get('kw'),
                                category_id=request.args.get('category_id'),
                                page=int(request.args.get('page', 1)))
    categories = get_categories()

    s = get_sessions(session_id=session_id).first()

    return render_template('/staff/products.html', products=products,
                           categories=categories, ss=s,
                           pages=math.ceil(count_products() / app.config['PAGE_SIZE']))


@app.route('/staffs/rooms')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_rooms_preview():
    r = request.args
    page=int(r.get('page', 1))
    page_size = app.config['PAGE_SIZE']
    rooms = filter_rooms(room_id=r.get('room_id'),
                           status=r.get('status'),
                           kw=r.get('kw'),
                           capacity=r.get('capacity'),
                           price_max=r.get('price_max'),
                           sort_by=r.get('sort'))
    
    count = rooms.count()

    if page:
        start = (page - 1) * app.config["PAGE_SIZE"]
        rooms = rooms.slice(start, start + app.config["PAGE_SIZE"])

    return render_template('/staff/rooms.html', 
                           rooms=rooms.all(),
                           pages=math.ceil(count / page_size))


@app.route('/api/logincheck')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_logincheck():
    is_logout = StaffWorkingHour.query.filter(StaffWorkingHour.staff_id == current_user.id
                                                ,StaffWorkingHour.logout_date is None).first()
    if not is_logout:
        check = StaffWorkingHour(staff_id=current_user.id)

        db.session.add(check)
        db.session.commit()

        return redirect('/staffs')


@app.route('/api/logoutcheck')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_logoutcheck():
    check = StaffWorkingHour.query.filter(StaffWorkingHour.staff_id == current_user.id
                                            ,StaffWorkingHour.logout_date is None).first()
    if check:
        check.logout_date = datetime.now()

        db.session.commit()

    logout_user()
    return redirect('/')
