import csv
import io
from datetime import datetime

from flask import request, Blueprint, render_template, redirect, url_for, session, Response, send_file
from flask_login import login_required, current_user
from flask_security import roles_required, roles_accepted
from sqlalchemy import func
from db_models import db, User, MeasurementRecord

records_bp = Blueprint('records', __name__)


@records_bp.route('/my_records')
@login_required
def my_records():
    user_id = current_user.get_id()
    records = MeasurementRecord.query.filter_by(user_id=user_id, status='approved').all()
    user = User.query.get(user_id)

    # 各測定項目の順位を計算
    rankings = {
        '50m走': calculate_rank(user.user_id, 'run_50m', asc=True),  # 速い方が良いので昇順
        'ベースランニング': calculate_rank(user.user_id, 'base_running', asc=True),
        '遠投距離': calculate_rank(user.user_id, 'long_throw', asc=False),
        'ストレート球速': calculate_rank(user.user_id, 'straight_speed', asc=False),
        '打球速度': calculate_rank(user.user_id, 'hit_speed', asc=False),
        'スイング速度': calculate_rank(user.user_id, 'swing_speed', asc=False),
        'ベンチプレス': calculate_rank(user.user_id, 'bench_press', asc=False),
        'スクワット': calculate_rank(user.user_id, 'squat', asc=False)
    }

    return render_template('my/records.html', user=user, records=records, rankings=rankings)


def calculate_rank(user_id, metric, asc=True):
    # 全ユーザーの最新記録を取得して順位を計算
    subquery = db.session.query(
        MeasurementRecord.user_id,
        func.max(MeasurementRecord.measurement_date).label('max_date')
    ).group_by(MeasurementRecord.user_id).subquery()

    latest_records = db.session.query(MeasurementRecord).join(
        subquery,
        (MeasurementRecord.user_id == subquery.c.user_id) &
        (MeasurementRecord.measurement_date == subquery.c.max_date)
    )

    # ソート方向を決定
    if asc:
        ordered_records = latest_records.order_by(getattr(MeasurementRecord, metric).asc())
    else:
        ordered_records = latest_records.order_by(getattr(MeasurementRecord, metric).desc())

    # 順位を計算
    records_list = ordered_records.all()
    for idx, record in enumerate(records_list, start=1):
        if record.user_id == user_id:
            return idx

    return "N/A"  # 記録がない場合


@records_bp.route('/my/records/export_csv')
@login_required
@roles_required("member")
def export_csv():
    # ユーザーと記録データを取得
    user_id = current_user.get_id()
    records = MeasurementRecord.query.filter_by(user_id=user_id, status='approved').all()
    user = User.query.get(user_id)

    # CSVデータをメモリに生成
    output = io.BytesIO()
    wrapper = io.TextIOWrapper(output, encoding='utf-8', newline='')
    writer = csv.writer(wrapper)

    # ヘッダー行 (テンプレートと一致させる)
    headers = [
        '測定日',
        '50m走 (秒)',
        'ベースランニング (秒)',
        '遠投距離 (m)',
        'ストレート球速 (km/h)',
        '打球速度 (km/h)',
        'スイング速度 (km/h)',
        'ベンチプレス (kg)',
        'スクワット (kg)'
    ]
    writer.writerow(headers)

    # データ行
    for record in records:
        row = [
            record.measurement_date.strftime('%Y-%m-%d') if record.measurement_date else '',
            record.run_50m if record.run_50m is not None else '',
            record.base_running if record.base_running is not None else '',
            record.long_throw if record.long_throw is not None else '',
            record.straight_speed if record.straight_speed is not None else '',
            record.hit_speed if record.hit_speed is not None else '',
            record.swing_speed if record.swing_speed is not None else '',
            record.bench_press if record.bench_press is not None else '',
            record.squat if record.squat is not None else ''
        ]
        writer.writerow(row)

    # バッファを準備
    wrapper.flush()
    output.seek(0)
    wrapper.detach()  # BytesIOを閉じないようにする

    # ファイル名生成 (テンプレートのユーザー名と一致)
    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"{user.name}_測定記録_{date_str}.csv"

    # レスポンス返却
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename,
        etag=False
    )