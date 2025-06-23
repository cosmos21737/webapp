import math

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from db_models import News, AdminContact

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    return redirect(url_for('auth.login'))  # 最初にログインページへ


@main_bp.route('/dashboard')
@login_required
def dashboard():
    news_list = News.query.order_by(News.post_date.desc()).limit(5).all()
    return render_template('dashboard.html', news_list=news_list)


@main_bp.route('/help')
def help():
    contact_info = AdminContact.query.first()
    return render_template('help.html', contact=contact_info)
