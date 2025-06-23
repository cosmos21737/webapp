import csv
import io
from datetime import datetime

from flask import request, Blueprint, render_template, send_file
from flask_login import login_required
from flask_security import  roles_accepted
from db_models import db, User, MeasurementRecord, MeasurementType
from services import services

records_bp = Blueprint('records', __name__)


@records_bp.route('/<int:member_id>')
@login_required
def records(member_id):
    user = User.query.get_or_404(member_id)
    measurement_types = MeasurementType.query.all()

    # 測定記録を取得（バックエンドでのソート・ページネーションを削除）
    # get_user_records がすでにソートされている可能性があるため確認
    records_list = services.get_user_records(member_id)

    # ランキングデータを取得
    rankings = services.calculate_rankings(member_id)

    # すべてのレコードをフロントエンドに渡す
    return render_template('records.html',
                           user=user,
                           records=records_list,
                           rankings=rankings,
                           measurement_types=measurement_types)


@records_bp.route('/my/records/export_csv/<int:member_id>')
@login_required
@roles_accepted("administer", "member", "coach", "director")
def export_csv(member_id):
    user = User.query.get_or_404(member_id)
    # MeasurementRecord に関連する MeasurementValue も一緒にロード
    records = MeasurementRecord.query.filter_by(user_id=member_id, status='approved').options(
        db.joinedload(MeasurementRecord.values)).all()

    # 測定タイプの情報を取得し、表示名と識別子のリストを生成
    all_measurement_types = MeasurementType.query.all()
    header_names = [mt.display_name for mt in all_measurement_types]
    header_keys = [mt.name for mt in all_measurement_types]

    output = io.BytesIO()
    wrapper = io.TextIOWrapper(output, encoding='utf-8', newline='')
    writer = csv.writer(wrapper)

    headers = ['測定日'] + header_names
    writer.writerow(headers)

    for record in records:
        row = [record.measurement_date.strftime('%Y-%m-%d') if record.measurement_date else '']

        # record.values から、対応する MeasurementValue を探して値を取得
        # 測定タイプの識別子（name）と値のマッピングを作成
        record_values_map = {mv.type.name: mv.value for mv in record.values}

        for key in header_keys:
            # マップから値を取得、存在しない場合は空文字列
            value = record_values_map.get(key, '')
            row.append(value)

        writer.writerow(row)

    wrapper.flush()
    output.seek(0)
    wrapper.detach()

    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"{user.name}_測定記録_{date_str}.csv"

    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename,
        etag=False
    )