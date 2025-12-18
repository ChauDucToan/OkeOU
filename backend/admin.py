from flask import redirect
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user

from backend import app, db
from backend.models import Room, RoomType, Product, Staff

from backend import app

class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin


class ProductView(AdminView):
    column_list = [
        'name',
        'price',
        'category_id',
        'amount',
        'unit',
        'active'
    ]

    column_searchable_list = ['name']
    column_filters = ['id', 'name', 'price', 'active']
    page_size = app.config['PAGE_SIZE']
    can_export = True


class RoomView(AdminView):
    column_list = [
        'name',
        'status',
        'room_type',
        'capacity'
    ]

    column_filters = ['name', 'status', 'room_type', 'capacity']


class RoomTypeView(AdminView):
    column_list = [
        'name',
        'hourly_price'
    ]

    column_filters = ['name', 'hourly_price']


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/')

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.is_admin

class StatsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/stats.html')

    @expose('/time')
    def time_stats(self):
        return self.render('admin/time_stats.html')

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.is_admin


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return self.render('admin/index.html')


admin = Admin(app=app, name='OkeOU', index_view=MyAdminIndexView())

admin.add_view(AdminView(Staff, db.session))
admin.add_view(RoomView(Room, db.session))
admin.add_view(RoomTypeView(RoomType, db.session))
admin.add_view(ProductView(Product, db.session))
admin.add_view(StatsView(name="Thống kê"))
admin.add_view(LogoutView(name='Logout'))
