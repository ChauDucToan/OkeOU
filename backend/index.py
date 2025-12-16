import math
from flask import render_template, redirect, request
from flask_login import current_user, login_required, logout_user, login_user

from backend import app, login
from backend import dao
from backend.dao import add_user, auth_user, get_user_by_id


# ===========================================================
#   Page Redirect
# ===========================================================
@app.route('/')
def index():
    rooms = dao.load_rooms(room_id=request.args.get('room_id'),
                           kw=request.args.get('kw'),
                           page=int(request.args.get('page', 1)))

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

    user = auth_user(username=username, password=password)
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
        add_user(name=data.get('name'),
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
    user = get_user_by_id(current_user.id)

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
    return get_user_by_id(pk)


if __name__ == '__main__':
    from backend import admin

    app.run(debug=True)
