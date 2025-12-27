from flask import redirect
from backend import app
from backend.models import UserRole
from backend.utils.general_utils import user_role_required
from backend.utils.session_utils import begin_session

@app.route('/api/sessions/<int:session_id>/begin_session')
@user_role_required([UserRole.STAFF, UserRole.ADMIN])
def start_session(session_id):
    begin_session(session_id)
    return redirect('/staffs')