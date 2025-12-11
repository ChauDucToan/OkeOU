from flask import render_template

import dao
from backend import app, login
from models import User


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def loginView():
    return render_template('login.html')

@app.route('/register')
def registerView():
    return render_template('register.html')

@login.user_loader
def load_user(pk):
    return dao.get_user_by_id(pk)

if __name__ == '__main__':
    from backend import admin
    app.run(debug=True)
