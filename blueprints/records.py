import codecs
import csv
import io
from datetime import datetime
from io import StringIO

from flask import request, Blueprint, render_template, redirect, url_for, session, Response, send_file
from flask_login import login_required, current_user
from flask_security import roles_required, roles_accepted
from db_models import db, User, MeasurementRecord


records_bp = Blueprint('records', __name__)

@records_bp.route('/my/records')
@login_required
@roles_required("member")
def my_records():
    user_id = current_user.get_id()
    records = MeasurementRecord.query.filter_by(user_id=user_id, status='approved').all()
    user = User.query.get(user_id)

    return render_template('/my/records.html', user=user, records=records)


@records_bp.route('/my/records/export_csv')
@login_required
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