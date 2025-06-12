from flask import request, Blueprint, render_template, redirect, url_for, session
from flask_login import login_required, current_user
from flask_security import roles_required, roles_accepted
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
@roles_required("member")
def my_records():
    user_id = current_user.get_id()
    records = MeasurementRecord.query.filter_by(user_id=user_id).all()
    user = User.query.get(user_id)

    return render_template('/my/records.html', user=user, records=records)


