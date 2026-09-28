from flask import Blueprint, render_template

bp = Blueprint('products', __name__, url_prefix='/products')


@bp.route('/')
def index():
    return render_template('products.html', title='Products')
