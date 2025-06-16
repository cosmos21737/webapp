import codecs
import csv
import io
from datetime import datetime
from io import StringIO

from flask import request, Blueprint, render_template, redirect, url_for, session, Response, send_file
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

@main_bp.route('/my/notice')
@login_required
@roles_accepted("member", "manager", "coach")
def notice():
    user_id = current_user.get_id()
    user = User.query.get(user_id)
    if current_user.has_role("member"):
        records = MeasurementRecord.query.filter_by(user_id=user_id, status='draft').all()
    if current_user.has_role("coach"):
        records = MeasurementRecord.query.filter_by(status='pending_coach').all()
    if current_user.has_role("manager"):
        records = MeasurementRecord.query.filter_by(status='rejected').all()

    return render_template('notice.html', user=user, records=records)


@main_bp.route("/approve_records", methods=["POST"])
@login_required
@roles_accepted("member", "manager", "coach")
def approve_records():
    selected_record_ids = request.form.getlist("record_ids")  # 選択されたIDのリスト
    action = request.form.get('action')

    if selected_record_ids:
        # データベース更新処理
        records = MeasurementRecord.query.filter(MeasurementRecord.record_id.in_(selected_record_ids)).all()
        for record in records:
            if action == "reject":
                record.status = 'rejected'
            elif current_user.has_role("member"):
                record.status = 'pending_coach'  # 承認フラグを更新
            elif current_user.has_role("coach"):
                record.status = 'approved'
            elif current_user.has_role("manager"):
                db.session.delete(record)
        db.session.commit()

    return redirect(url_for("main.notice"))
