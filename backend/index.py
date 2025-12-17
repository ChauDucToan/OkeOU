import math
from flask import render_template, redirect, request
from flask_login import current_user, login_required, logout_user, login_user

from backend import app, login, dao


# ===========================================================
#   Page Redirect
# ===========================================================
@app.route('/')
def index():
    rooms = dao.load_rooms(room_id=request.args.get('room_id'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    if current_user.is_authenticated and current_user.is_staff:
        return redirect('/staffs')

    return render_template('index.html', rooms=rooms,
                           pages=math.ceil(dao.count_rooms() / app.config['PAGE_SIZE']))


@app.route('/login')
def loginView():
    return render_template('login.html')


@app.route('/register')
def registerView():
    return render_template('register.html')


# ===========================================================
#   Login & Logout & Register
# ===========================================================
@app.route('/logout')
def logout_process():
    logout_user()
    return redirect('/')


@app.route('/login', methods=['POST'])
def login_process():
    username = request.form.get('username')
    password = request.form.get('password')

    user = dao.auth_user(username=username, password=password)
    if user:
        login_user(user=user)
    else:
        err_msg = 'Sai tên đăng nhập hoặc mật khẩu!'
        return render_template('login.html', err_msg=err_msg)

    next = request.args.get('next')
    return redirect(next if next else '/')


@app.route('/register', methods=['POST'])
def register_process():
    data = request.form

    password = data.get('password')
    confirm = data.get('confirm')
    email = data.get('email')
    phoneNumber = data.get('phone')

    if password != confirm:
        err_msg = 'Mật khẩu không khớp!'
        return render_template('register.html', err_msg=err_msg)

    try:
        dao.add_user(name=data.get('name'),
                     username=data.get('username'),
                     password=password,
                     email=email,
                     phoneNumber=phoneNumber)
        return redirect('/login')
    except Exception as ex:
        return render_template('register.html', err_msg=str(ex))


# ===========================================================
#   User Profiles Previews
# ===========================================================
@app.route('/profile')
@login_required
def profile_preview():
    user = dao.get_user_by_id(current_user.id)

    return render_template('profile.html', user=user)


# ===========================================================
#   Products Page
# ===========================================================
@app.route('/products')
def products_preview():
    products = dao.get_products(kw=request.args.get('kw'),
                                category_id=request.args.get('category_id'),
                                page=int(request.args.get('page', 1)))
    categories = dao.get_categories()

    return render_template('products.html', products=products,
                           categories=categories,
                           pages=math.ceil(dao.count_products() / app.config['PAGE_SIZE']))


# ===========================================================
#   Rooms Page
# ===========================================================
@app.route('/rooms')
def rooms_preview():
    rooms = dao.load_rooms(room_id=request.args.get('room_id'),
                           status=request.args.get('status'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    return render_template('rooms.html', rooms=rooms,
                           pages=math.ceil(dao.count_rooms() / app.config['PAGE_SIZE']))


# ===========================================================
#   Payments Page
# ===========================================================
@app.route('/payments')
@login_required
def payments_preview():
    return render_template('payments.html',
                           pages=math.ceil(dao.count_payments(user_id=current_user.id) / app.config['PAGE_SIZE']))


@login.user_loader
def load_user(pk):
    return dao.get_user_by_id(pk)


# ===========================================================
#   Staffs Page
# ===========================================================
@app.route('/staffs')
@login_required
def staff_preview():
    rooms = dao.load_rooms(room_id=request.args.get('room_id'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    return render_template('/staff/index.html', rooms=rooms,
                           pages=math.ceil(dao.count_rooms() / app.config['PAGE_SIZE']))


@app.route('/staffs/payments')
@login_required
def staff_payments_preview():
    return render_template('/staff/payments.html',
                           pages=math.ceil(dao.count_payments(user_id=current_user.id) / app.config['PAGE_SIZE']))


@app.route('/staffs/products')
def staff_products_preview():
    products = dao.get_products(kw=request.args.get('kw'),
                                category_id=request.args.get('category_id'),
                                page=int(request.args.get('page', 1)))
    categories = dao.get_categories()

    return render_template('/staff/products.html', products=products,
                           categories=categories,
                           pages=math.ceil(dao.count_products() / app.config['PAGE_SIZE']))


@app.route('/staffs/rooms')
def staff_rooms_preview():
    rooms = dao.load_rooms(room_id=request.args.get('room_id'),
                           status=request.args.get('status'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

    return render_template('/staff/rooms.html', rooms=rooms,
                           pages=math.ceil(dao.count_rooms() / app.config['PAGE_SIZE']))


@app.route('/api/logincheck')
def staff_logincheck():
    pass


@login.user_loader
def load_user(pk):
    return dao.get_user_by_id(pk)


if __name__ == '__main__':
    from backend import admin

    app.run(debug=True)
