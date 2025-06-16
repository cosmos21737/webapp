from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    return redirect(url_for('auth.login'))  # 最初にログインページへ


@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
