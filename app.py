from flask import Flask, render_template

from helpers import init_db
from modules import auth_bp, products_bp, settings_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = 'saham-secret-key'

    app.register_blueprint(auth_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(products_bp)

    @app.route('/')
    def index():
        return render_template('index.html', title='Home')

    @app.route('/about')
    def about():
        return render_template('about.html', title='About')

    @app.route('/contact')
    def contact():
        return render_template('contact.html', title='Contact')

    return app


app = create_app()
init_db()


if __name__ == '__main__':
    app.run(debug=True)
