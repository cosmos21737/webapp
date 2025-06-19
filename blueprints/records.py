import csv
import io
from datetime import datetime

from flask import request, Blueprint, render_template, redirect, url_for, session, Response, send_file
from flask_login import login_required, current_user
from flask_security import roles_required, roles_accepted
from sqlalchemy import func
from db_models import db, User, MeasurementRecord

records_bp = Blueprint('records', __name__)


@records_bp.route('/records/<int:member_id>')
@login_required
def records(member_id):
    user = User.query.get(member_id)

    # クエリを構築（まだ実行しない）
    records_query = MeasurementRecord.query.filter_by(user_id=member_id, status='approved')

    # 各測定項目の順位を計算
    rankings = {
        '50m走': calculate_rank(user.user_id, 'run_50m', asc=True),
        'ベースランニング': calculate_rank(user.user_id, 'base_running', asc=True),
        '遠投距離': calculate_rank(user.user_id, 'long_throw', asc=False),
        'ストレート球速': calculate_rank(user.user_id, 'straight_speed', asc=False),
        '打球速度': calculate_rank(user.user_id, 'hit_speed', asc=False),
        'スイング速度': calculate_rank(user.user_id, 'swing_speed', asc=False),
        'ベンチプレス': calculate_rank(user.user_id, 'bench_press', asc=False),
        'スクワット': calculate_rank(user.user_id, 'squat', asc=False)
    }

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'measurement_date', type=str)
    sort_order = request.args.get('sort_order', 'asc', type=str)

    # ソート処理
    if sort_by == 'measurement_date':
        sort_column = MeasurementRecord.measurement_date
    else:
        sort_column = getattr(MeasurementRecord, sort_by, MeasurementRecord.measurement_date)

    if sort_order == 'desc':
        sort_column = sort_column.desc()
    else:
        sort_column = sort_column.asc()

    # クエリにソートを適用してページネーション
    pagination = records_query.order_by(sort_column).paginate(page=page, per_page=per_page)
    records_list = pagination.items

    return render_template('records.html',
                           user=user,
                           records=records_list,
                           rankings=rankings,
                           pagination=pagination,
                           sort_by=sort_by,
                           sort_order=sort_order)


def calculate_rank(user_id, metric, asc=True):
    try:
        print("start")
        # テーブル名とカラム名を確認
        column = getattr(MeasurementRecord, metric)

        # SQLite用に簡略化したバージョン
        # 1. 各ユーザーの代表値を取得
        if asc:
            subquery = db.session.query(
                MeasurementRecord.user_id,
                func.min(column).label('target_value')
            )
        else:
            subquery = db.session.query(
                MeasurementRecord.user_id,
                func.max(column).label('target_value')
            )

        subquery = subquery.filter(
            MeasurementRecord.status == 'approved'
        ).group_by(
            MeasurementRecord.user_id
        ).subquery()

        # 2. ユーザーの値を取得
        user_value = db.session.query(
            subquery.c.target_value
        ).filter(
            subquery.c.user_id == user_id
        ).scalar()

        if user_value is None:
            return {'rank': "N/A", 'stddev': "N/A", 'value': "N/A"}

        # 3. SQLite互換の統計計算
        # 平均と標準偏差をPythonで計算
        all_values = [x[0] for x in db.session.query(
            subquery.c.target_value
        ).filter(
            subquery.c.target_value.isnot(None)
        ).all()]

        if not all_values:
            return {'rank': "N/A", 'stddev': "N/A", 'value': "N/A"}

        avg = sum(all_values) / len(all_values)
        variance = sum((x - avg) ** 2 for x in all_values) / len(all_values)
        stddev = variance ** 0.5

        # 4. 順位計算 (SQLite用の代替方法)
        # より良い値を先に並べる (asc=Trueなら小さい値が良い)
        ordered_users = db.session.query(
            subquery.c.user_id,
            subquery.c.target_value
        ).order_by(
            subquery.c.target_value.asc() if asc else subquery.c.target_value.desc()
        ).all()

        rank = next(
            (i + 1 for i, (uid, _) in enumerate(ordered_users) if uid == user_id),
            "N/A"
        )

        # 偏差値計算
        def calc_std_score(value, avg, stddev):
            return 50 + 10 * (value - avg) / stddev if stddev != 0 else 50

        return {
            'rank': rank,
            'stddev': round(calc_std_score(user_value, avg, stddev), 1),
            'value': round(user_value, 2)
        }

    except Exception as e:
        print(f"Error in calculate_rank: {str(e)}")
        return {'rank': "Error", 'stddev': "Error", 'value': "Error"}


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
