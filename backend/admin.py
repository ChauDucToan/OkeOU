from flask import redirect, request
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user

from backend import app, db
from backend.daos.revenue_daos import revenue_by_product, revenue_by_room_name, revenue_by_room_type, revenue_by_time
from backend.models import Room, Product, Staff


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
    page_size = app.config['PAGE_SIZE']


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/')

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.is_admin


class MyAdminIndexView(AdminIndexView):
    stats = {
        'rooms': 10, # Thay bằng: Room.query.count()
        'products': 55, # Thay bằng: Product.query.count()
        'staff': 5
    }

    @expose('/')
    def index(self):
        return self.render('admin/index.html', stats=self.stats)
    
class StatsView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/stats.html')

    @expose('/time')
    def time_stats(self):
        period = request.args.get('period')
        return self.render('admin/time_stats.html', revenue_by_room_name=revenue_by_room_name(period),
                           revenue_by_room_type=revenue_by_room_type(period),
                           revenue_by_product=revenue_by_product(period),
                           revenue_by_time=revenue_by_time(period))

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.is_admin
    

class ReturnHomeView(BaseView):
    @expose('/')
    def index(self):
        return redirect('/')

    def is_accessible(self):
        return current_user.is_authenticated


admin = Admin(app=app, name='OkeOU', index_view=MyAdminIndexView())

admin.add_view(AdminView(Staff, db.session))
admin.add_view(RoomView(Room, db.session))
admin.add_view(ProductView(Product, db.session))
admin.add_view(StatsView(name="Thống kê"))
admin.add_view(LogoutView(name='Logout'))
admin.add_view(ReturnHomeView(name='Return to Home'))
