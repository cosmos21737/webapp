# blueprints/auth.py
from flask import Blueprint, request, redirect, url_for, render_template, session
from db_models import db, User,MeasurementRecord
from werkzeug.security import generate_password_hash, check_password_hash



auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(name=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.user_id
            session['username'] = user.name
            return redirect(url_for('main.dashboard'))
        else:
            return "ログイン失敗！"

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))