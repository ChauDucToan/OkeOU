from backend import app
from flask import render_template, request, redirect, session
from flask_login import current_user, login_user, logout_user, login_required
from backend.daos.user_daos import create_user, get_users
from backend.utils.user_utils import auth_user


@app.route('/login')
def loginView():
    return render_template('login.html')


@app.route('/register')
def registerView():
    return render_template('register.html')


@app.route('/profile')
@login_required
def profile_preview():
    user = get_users(user_id=current_user.id).first()

    return render_template('profile.html', user=user)


@app.route('/logout')
def logout_process():
    if current_user.is_authenticated and current_user.is_staff:
        return redirect('/api/logoutcheck')
    logout_user()
    session.pop('order', None)
    return redirect('/')


@app.route('/login', methods=['POST'])
def login_process():
    username = request.form.get('username')
    password = request.form.get('password')

    user = auth_user(username=username, password=password)
    if user:
        login_user(user=user)
    else:
        err_msg = 'Username or password is incorrect!'
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
        err_msg = 'Passwords do not match!'
        return render_template('register.html', err_msg=err_msg)

    try:
        create_user(name=data.get('name'),
                    username=data.get('username'),
                    password=password,
                    email=email,
                    phoneNumber=phoneNumber)
        return redirect('/login')
    except Exception as ex:
        return render_template('register.html', err_msg=str(ex))
