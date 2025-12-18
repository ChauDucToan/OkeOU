from datetime import datetime
from backend import db
from sqlalchemy.exc import IntegrityError
from backend.daos.session_daos import get_sessions
from backend.models import LoyalCustomer, SessionStatus, User
from backend.utils import hash_password


def add_loyal_customer(user_id):
    loyal = LoyalCustomer.query.get(user_id)
    if not loyal:
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        counter = get_sessions(user_id=user_id,
                                 status=SessionStatus.COMPLETED,
                                 start_date=start_date).count()
        if counter >= 10:
            loyal = LoyalCustomer(id=user_id)
            db.session.add(loyal)
            try:
                db.session.commit()
            except IntegrityError as ie:
                db.session.rollback()
                raise Exception(str(ie.orig))
            
            
def auth_user(username, password):
    password = hash_password(password)
    return User.query.filter(User.username == username.strip(),
                             User.password == password).first()