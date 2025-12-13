from flask import render_template, redirect, request
from flask_login import logout_user, login_user

from backend import app, login, dao
from backend.models import User

# ===========================================================
#   Page Redirect
# ===========================================================
@app.route('/')
def index():
    return render_template('index.html')

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
    return redirect('/login')

@app.route('/login', methods=['POST'])
def login_process():
    username = request.form['username']
    password = request.form['password']

    user = dao.auth_user(username=username, password=password)
    if user:
        login_user(user=user)

    next = request.args.get('next')
    return redirect(next if next else '/')

@login.user_loader
def load_user(pk):
    return dao.get_user_by_id(pk)

if __name__ == '__main__':
    from backend import admin
    app.run(debug=True)
