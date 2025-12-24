from backend.models import Order, OrderStatus, UserRole
from backend.utils.general_utils import user_role_required
from backend import app, db
from flask import jsonify


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
