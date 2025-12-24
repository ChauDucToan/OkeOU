from backend import app
from backend.daos.category_daos import get_categories
from backend.daos.product_daos import count_products, load_products
from flask import render_template, request
import math


@app.route('/products')
def products_preview():
    products = load_products(kw=request.args.get('kw'),
                             category_id=request.args.get('category_id'),
                             page=int(request.args.get('page', 1)))
    categories = get_categories()
    return render_template('products.html', products=products,
                           categories=categories,
                           pages=math.ceil(
                               count_products(request.args.get('kw'), request.args.get('category_id')) / app.config[
                                   'PAGE_SIZE']))
