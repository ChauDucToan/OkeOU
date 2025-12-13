import cloudinary

from sqlalchemy.exc import IntegrityError
from backend.models import Category, Product, User, Job
from backend import app, db
from backend.utils import hash_password


def get_categories():
    return Category.query.all()


def get_products(kw=None, category_id=None, page=1):
    products = Product.query

    if category_id:
        products = products.filter(Product.category_id == category_id)

    if kw:
        products = products.filter(Product.name.contains(kw))

    if page:
        page = int(page)
        page_size = app.config.get("PAGE_SIZE", 10)
        start = (page - 1) * page_size
        products = products.slice(start, start + page_size)

    return products.all()


def get_jobs():
    return Job.query.all()


def count_products():
    return Product.query.count()


def get_user_by_id(user_id):
    return User.query.get(user_id)


def auth_user(username, password):
    password = hash_password(password)
    return User.query.filter(User.username == username.strip(),
                             User.password == password).first()


def add_user(name, username, password, avatar):
    u = User(name=name,
             username=username.strip(),
             password=hash_password(password))

    if avatar:
        res = cloudinary.uploader.upload(avatar)
        u.avatar = res.get('secure_url')

    db.session.add(u)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Exception('Username đã tồn tại!')
