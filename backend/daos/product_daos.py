from backend.models import Product
from backend import app


def get_products(kw=None, category_id=None):
    p = Product.query

    if category_id:
        p = p.filter(Product.category_id == category_id)

    if kw:
        p = p.filter(Product.name.contains(kw))

    return p


def load_products(kw=None, category_id=None, page=1):
    p = get_products(kw=kw, category_id=category_id)

    if page:
        page_size = app.config["PAGE_SIZE"]
        start = (page - 1) * page_size
        p = p.slice(start, start + page_size)

    return p.all()


def count_products(kw=None, category_id=None):
    p = get_products(kw=kw, category_id=category_id)
    if p.count() > 0:
        return p.count()
    else:
        return 0