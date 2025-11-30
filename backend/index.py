from flask import render_template

from backend import app, login
from models import User


@app.route('/')
def index():
    return render_template('index.html')

@login.user_loader
def load_user(id):
    return User.query.get(id)

if __name__ == '__main__':
    app.run(debug=True)
