import csv
import io
from datetime import datetime

from flask import request, Blueprint, render_template, redirect, url_for, session, Response, send_file
from flask_login import login_required, current_user
from flask_security import roles_required, roles_accepted
from sqlalchemy import func
from db_models import db, User, MeasurementRecord, MeasurementType
from services import services

records_bp = Blueprint('records', __name__)


@records_bp.route('/<int:member_id>')
@login_required
def records(member_id):
    user = User.query.get_or_404(member_id)
    measurement_types = MeasurementType.query.all()

    # 測定記録を取得
    records_list = services.get_user_records(member_id)

    # ランキングデータを取得
    rankings = services.calculate_rankings(member_id)

    # ページネーションとソート処理
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'measurement_date', type=str)
    sort_order = request.args.get('sort_order', 'asc', type=str)

    # ソート処理（簡略化版）
    if sort_by == 'measurement_date':
        records_list.sort(
            key=lambda x: x.measurement_date,
            reverse=(sort_order == 'desc')
        )
    else:
        # 他のソート条件が必要な場合は追加
        pass

    # 簡易ページネーション
    total_records = len(records_list)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_records = records_list[start:end]

    return render_template('records.html',
                           user=user,
                           records=paginated_records,
                           rankings=rankings,
                           pagination={
                               'page': page,
                               'per_page': per_page,
                               'total': total_records,
                               'pages': (total_records + per_page - 1) // per_page
                           },
                           sort_by=sort_by,
                           sort_order=sort_order,
                           measurement_types=measurement_types)

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
        '遠投 (m)',
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