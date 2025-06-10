from flask import request, Blueprint, render_template, redirect, url_for, session
from flask_login import login_required, current_user
from db_models import db, User, MeasurementRecord

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    return redirect(url_for('auth.login'))  # 最初にログインページへ


@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@main_bp.route('/my/records')
@login_required
def my_records():
    user_id = current_user.get_id()
    records = MeasurementRecord.query.filter_by(user_id=user_id).all()
    user = User.query.get(user_id)

    return render_template('/my/records.html', user=user, records=records)


@main_bp.route('/records/<int:member_id>')
@login_required
def member_records(member_id):
    user = User.query.get(member_id)  # 指定された部員の情報を取得
    if not user:
        return "部員が見つかりません", 404

    records = MeasurementRecord.query.filter_by(user_id=member_id).all()
    return render_template('my/records.html', user=user, records=records)
