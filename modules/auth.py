from flask import Blueprint, redirect, render_template, request, session, url_for

from helpers import login_user

bp = Blueprint('auth', __name__)


@bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = login_user(username, password)
        if user:
            return redirect(url_for('index'))

        error = 'Username atau password salah.'

    return render_template('login.html', error=error, title='Login')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))
