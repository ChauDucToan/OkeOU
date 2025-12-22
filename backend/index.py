from backend import app, login
from flask import render_template, redirect, session
from flask_login import current_user
from backend.daos.product_daos import load_products
from backend.daos.room_daos import load_rooms
from backend.daos.user_daos import get_users
from backend.utils.general_utils import redirect_to_error


@app.route('/error')
def error_view():
    error_payload = session.pop('error_payload', None)

    if error_payload:
        code = error_payload.get('code')
        msg = error_payload.get('msg')
        return render_template('error.html', status_code=code, err_msg=msg)
    else:
        return redirect_to_error(200, "No error information available.")

@app.route('/')
def index():
    rooms = load_rooms(page=1)
    
    products = load_products(page=1)

    if current_user.is_authenticated and current_user.is_staff:
        return redirect('/staffs')

    return render_template('index.html', rooms=rooms, products=products)


@login.user_loader
def load_user(pk):
    user = get_users(user_id=pk).first()
    return user


if __name__ == '__main__':
    from backend import admin
    from backend.routes import users_routes, rooms_routes, products_routes, \
          staffs_routes, orders_routes, payment_routes

    app.run(debug=True)
