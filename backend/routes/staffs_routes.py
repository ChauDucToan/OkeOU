import math
from datetime import datetime
from flask import redirect, render_template, request
from flask_login import current_user, logout_user
from backend import app, db
from backend.daos.category_daos import get_categories
from backend.daos.payment_daos import count_payments
from backend.daos.product_daos import count_products, load_products
from backend.daos.room_daos import count_rooms, load_rooms
from backend.models import StaffWorkingHour, UserRole
from backend.utils.general_utils import user_role_required
from backend.utils.room_utils import filter_rooms

@app.route('/staffs')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_preview():
    rooms = load_rooms(room_id=request.args.get('room_id'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    return render_template('/staff/index.html', rooms=rooms,
                           pages=math.ceil(count_rooms() / app.config['PAGE_SIZE']))


@app.route('/staffs/payments')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_payments_preview():
    return render_template('/staff/payments.html',
                           pages=math.ceil(count_payments(user_id=current_user.id) / app.config['PAGE_SIZE']))


@app.route('/staffs/products')
@user_role_required(roles=[UserRole.STAFF, UserRole.ADMIN])
def staff_products_preview():
    products = load_products(kw=request.args.get('kw'),
                                category_id=request.args.get('category_id'),
                                page=int(request.args.get('page', 1)))
    categories = get_categories()

    return render_template('/staff/products.html', products=products,
                           categories=categories,
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
