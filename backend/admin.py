from flask_admin import Admin

from backend import app

admin = Admin(app = app, name='OkeOU')

