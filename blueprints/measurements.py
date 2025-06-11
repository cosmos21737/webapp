from flask import Blueprint, request, redirect, url_for, render_template, session
from flask_login import login_required, current_user
from flask_security import roles_required
from db_models import db, User,MeasurementRecord
from datetime import datetime

measurements_bp = Blueprint('measurements', __name__)


@measurements_bp.route('input', methods=['GET', 'POST'])
@login_required
@roles_required("manager")
def records_input():
    user = User.query.get(current_user.get_id())
    return render_template('/measurements/input.html', user=user)


@measurements_bp.route('/submit_record', methods=['POST'])
@login_required
@roles_required("manager")
def submit_record():
    created_by = current_user.get_id() # 記入者（ログインしているユーザー）
    member_name = request.form.get('member_name')  # 記録を保存する対象の部員名
    measurement_date = request.form.get('measurement_date')

    # 指定された名前の部員を検索
    user = User.query.filter_by(name=member_name).first()
    if not user:
        return "部員が見つかりません", 404  # ユーザーが存在しない場合のエラーハンドリング

    # 測定記録を作成
    new_record = MeasurementRecord(
        user_id=user.user_id,  # 記録対象の部員の ID を設定
        measurement_date=datetime.strptime(measurement_date, '%Y-%m-%d'),
        run_50m=request.form.get('run_50m'),
        base_running=request.form.get('base_running'),
        long_throw=request.form.get('long_throw'),
        straight_speed=request.form.get('straight_speed'),
        hit_speed=request.form.get('hit_speed'),
        swing_speed=request.form.get('swing_speed'),
        bench_press=request.form.get('bench_press'),
        squat=request.form.get('squat'),
        status='draft',
        created_by=created_by  # 記入者の ID を記録
    )

    db.session.add(new_record)
    db.session.commit()

    return redirect(url_for('main.dashboard'))