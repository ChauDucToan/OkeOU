from datetime import datetime, timedelta
from flask import redirect, request
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user, logout_user

from backend import app, db
from backend.daos.revenue_daos import get_staffs_working_hours, get_top_customers, revenue_by_product, revenue_by_room_name, revenue_by_room_type, revenue_by_time
from backend.models import Application, ApplicationStatus, Job, Order, OrderStatus, Room, Product, Session, Staff, StaffWorkingHour


class AdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin


class ProductView(AdminView):
    column_list = [
        'name',
        'price',
        'categories.name',
        'amount',
        'unit',
        'active'
    ]

    column_labels = {
        'name': 'Tên sản phẩm',
        'price': 'Giá',
        'categories.name': 'Danh mục',
        'amount': 'Số lượng',
        'unit': 'Đơn vị',
        'active': 'Hoạt động'
    }

    column_searchable_list = ['name']
    column_filters = ['id', 'name', 'price', 'active']
    page_size = app.config['PAGE_SIZE']
    can_export = True


class StaffView(AdminView):
    column_list = [
        'name',
        'email',
        'phone',
        'active',
        'identity_card'
    ]

    column_searchable_list = ['name', 'email', 'phone']
    column_filters = ['active']
    page_size = app.config['PAGE_SIZE']


class RoomView(AdminView):
    column_list = [
        'name',
        'status',
        'type.name',
        'capacity'
    ]

    column_labels = {
        'name': 'Tên phòng',
        'status': 'Trạng thái',
        'type.name': 'Loại phòng',
        'capacity': 'Sức chứa'
    }

    column_filters = ['name', 'status', 'type.name', 'capacity']
    page_size = app.config['PAGE_SIZE']


class LogoutView(BaseView):
    @expose('/')
    def index(self):
        logout_user()
        return redirect('/')

    def is_accessible(self) -> bool:
        return current_user.is_authenticated and current_user.is_admin


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        pending_count = Order.query.filter(Order.status == OrderStatus.PENDING).count()

        active_session = Session.query.filter(Session.status == 'ACTIVE').count()

        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        staff_today = Staff.query.filter(StaffWorkingHour.logout_date < tomorrow,
                                        StaffWorkingHour.login_date >= today).join(StaffWorkingHour).count()

        top_employees = get_staffs_working_hours()
        top_customers = get_top_customers()

        application_count = Application.query.filter(Application.status == ApplicationStatus.PENDING).count()

        return self.render('admin/index.html', pending_count=pending_count, active_session=active_session, 
                           staff_today=staff_today, top_employees=top_employees, top_customers=top_customers,
                           application_count=application_count)
    
    @expose('/time')
    def time_stats(self):
        period = request.args.get('period')
        return self.render('admin/time_stats.html', revenue_by_room_name=revenue_by_room_name(period),
                           revenue_by_room_type=revenue_by_room_type(period),
                           revenue_by_product=revenue_by_product(period),
                           revenue_by_time=revenue_by_time(period))
    
    @expose('/applications')
    def applications(self):
        apps = Application.query.order_by(Application.submit_date.desc()).all()
        return self.render('admin/applications.html', apps=apps)
    

    @expose('/applications/<int:app_id>')
    def cv_details(self, app_id):
        application = Application.query.get(app_id)
        print(application.__dict__)
        return self.render('admin/cv_details.html', app=application)
    

class JobModelView(ModelView):
    can_view_details = True
    column_searchable_list = [
        'title',
        'description'
    ]

    column_filters = [
        'is_active',
        'min_salary',
        'max_salary'
    ]

    column_labels = {
        'title': 'Tiêu đề',
        'min_salary': 'Lương từ',
        'max_salary': 'Lương đến',
        'hired_quantity': 'Đã tuyển',
        'target_quantity': 'Mục tiêu',
        'deadline': 'Hạn nộp',
        'is_active':'Đang hiển thị',
        'applications': 'CV Ứng tuyển'
    }

    column_list = ('title', 'min_salary', 'max_salary', 'hired_quantity', 'deadline', 'is_active')

class ReturnHomeView(BaseView):
    @expose('/')
    def index(self):
        return redirect('/')

    def is_accessible(self):
        return current_user.is_authenticated


admin = Admin(app=app, name='OkeOU', index_view=MyAdminIndexView())

admin.add_view(StaffView(Staff, db.session))
admin.add_view(RoomView(Room, db.session))
admin.add_view(ProductView(Product, db.session))
admin.add_view(JobModelView(Job, db.session))
admin.add_view(LogoutView(name='Logout'))
admin.add_view(ReturnHomeView(name='Return to Home'))
