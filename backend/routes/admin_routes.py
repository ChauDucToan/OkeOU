from backend.models import Application, ApplicationStatus, Order, OrderStatus, UserRole
from backend.utils.general_utils import user_role_required
from backend import app, db
from flask import jsonify, redirect, send_from_directory

from backend.utils.jobs_utils import update_job_application_count


@app.route('/api/admin/serve_all')
@user_role_required([UserRole.ADMIN])
def serve_all_orders():
    try:
        pending_orders = Order.query.filter(Order.status == OrderStatus.PENDING)
        pending_orders = pending_orders.update({Order.status: OrderStatus.SERVED})

        db.session.commit()

        return jsonify({
            'status': 200,
            'message': "All pending orders have been marked as served.",
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 500, 'message': str(e)}), 500


@app.route('/uploads/cvs/<filename>')
def serve_cv(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/admin/applications/<int:app_id>/status/<string:action>', methods=['POST'])
def update_application_status(app_id, action):
    application = Application.query.get(app_id)
    msg = ''
    if action == 'approve':
        application.status = ApplicationStatus.APPROVED
        msg = f'Đã duyệt hồ sơ của {application.full_name}'
    elif action == 'reject':
        application.status = ApplicationStatus.REJECTED
        msg = f'Đã từ chối hồ sơ của {application.full_name}'
    else:
        msg = 'Hành động không hợp lệ'
    
    update_job_application_count(application.job_id)
    db.session.commit()
    
    return redirect('/admin/applications')