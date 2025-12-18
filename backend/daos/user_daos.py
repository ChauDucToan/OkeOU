from backend.models import Session, User, UserRole
from backend import db, cloudinary
from backend.utils import hash_password
from sqlalchemy.exc import IntegrityError

def get_users(user_id=None, name=None, username=None,
              phone=None, email=None, role=None):
    u = User.query

    if user_id:
        u = u.filter(User.id.__eq__(user_id))
    
    if name:
        u = u.filter(User.name.contains(name.strip()))

    if phone:
        u = u.filter(User.phone.__eq__(phone.strip()))

    if role:
        u = u.filter(User.role.in_(role))

    if username:
        u = u.filter(User.username.__eq__(username.strip()))

    if email:
        u = u.filter(User.email.__eq__(email.strip()))

    return u


def add_user(name, username, password, email,
             phoneNumber,
             avatar="https://res.cloudinary.com/dtcjixfyd/image/upload/v1765710152/no-profile-picture-15257_kw9uht.png"):
    u = User(name=name,
             username=username.strip(),
             password=hash_password(password),
             email=email,
             role=UserRole.CUSTOMER,
             phone=phoneNumber)

    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.avatar = res.get('secure_url')

    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError as ie:
        db.session.rollback()
        raise Exception(str(ie.orig))
            

def get_user_from_session(session_id):
    return get_users(user_id = Session.query.get(session_id)
                        .user_id).first()