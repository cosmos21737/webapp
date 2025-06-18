import io
import csv
from datetime import datetime

from flask import Blueprint, request, render_template, redirect, url_for, flash, Response, send_file
from flask_security import login_required, current_user, roles_required, roles_accepted
from sqlalchemy import func
from db_models import db, User, MeasurementRecord

# service をインポート
from . import members_bp
from . import services


@members_bp.route('/')
@login_required
@roles_accepted("administer", "coach", "director")
def members():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by')

    # 現在のソート状態を取得
    current_sort_by = request.args.get('sort_by')
    current_sort_order = request.args.get('sort_order')

    # 新しいソート順序を決定
    if sort_by == current_sort_by:
        # 同じカラムがクリックされたら順序をトグル
        new_sort_order = 'desc' if current_sort_order == 'asc' else 'asc'
    else:
        # 別のカラムがクリックされたら昇順で開始
        new_sort_order = 'asc'

    # デフォルトソート（何も指定がない場合）
    if not sort_by:
        sort_by = 'grade'
        new_sort_order = 'asc'

    # ソート処理
    if sort_by == 'name':
        sort_column = User.name
    elif sort_by == 'grade':
        sort_column = User.grade
    elif sort_by == 'status':
        sort_column = User.is_active

    sort_column = sort_column.desc() if new_sort_order == 'desc' else sort_column.asc()

    # クエリ実行
    pagination = User.query.order_by(sort_column).paginate(page=page, per_page=per_page)
    members_list = pagination.items

    return render_template('members/members.html',
                           members=members_list,
                           pagination=pagination,
                           sort_by=sort_by,
                           sort_order=new_sort_order)


@members_bp.route('/new')
@login_required
@roles_accepted("administer", "coach", "director")
def new_member():
    return render_template('/members/new_member.html')


@members_bp.route('/register', methods=['POST'])
@login_required
@roles_accepted("administer", "coach", "director")
def register_member():
    name = request.form.get('name')
    grade = request.form.get('grade')
    is_active = request.form.get('is_active') == "true"
    password = "password123"  # 固定パスワード

    success, message = services.register_new_member(name, grade, is_active, password)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('members.members'))


@members_bp.route('/records/<int:member_id>')
@login_required
@roles_accepted("administer", "coach", "director")
def member_records(member_id):
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
    records = pagination.items

    return render_template('my/records.html',
                           user=user,
                           records=records,
                           rankings=rankings,
                           pagination=pagination,
                           sort_by=sort_by,
                           sort_order=sort_order)


def calculate_rank(user_id, metric, asc=True):
    # 各ユーザーの最小値 or 最大値を取得
    if asc:
        value_query = func.min(getattr(MeasurementRecord, metric))
    else:
        value_query = func.max(getattr(MeasurementRecord, metric))

    subquery = db.session.query(
        MeasurementRecord.user_id,
        value_query.label('target_value')  # 最小値 or 最大値
    ).group_by(MeasurementRecord.user_id).subquery()

    # 取得した値と一致するレコードのみ取得
    target_records = db.session.query(MeasurementRecord).join(
        subquery,
        (MeasurementRecord.user_id == subquery.c.user_id) &
        (getattr(MeasurementRecord, metric) == subquery.c.target_value)
    )

    # ソート方向を決定
    ordered_records = target_records.order_by(
        getattr(MeasurementRecord, metric).asc() if asc else getattr(MeasurementRecord, metric).desc())

    # 順位を計算
    records_list = ordered_records.all()
    for idx, record in enumerate(records_list, start=1):
        if record.user_id == user_id:
            return idx

    return "N/A"  # 記録がない場合


@members_bp.route('/delete/<int:member_id>', methods=['POST'])
@login_required
@roles_accepted("administer", "coach", "director")
def delete_member(member_id):
    success, message = services.delete_member_by_id(member_id)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('members.members'))


@members_bp.route('/csv_import', methods=['GET', 'POST'])
@login_required
@roles_accepted("administer", "coach", "director")
def csv_import():
    if request.method == 'GET':
        return render_template('/members/csv_import.html')

    if 'csv_file' not in request.files:
        flash('ファイルが選択されていません', 'error')
        return redirect(request.url)

    file = request.files['csv_file']
    if file.filename == '':
        flash('ファイルが選択されていません', 'error')
        return redirect(request.url)

    if not file.filename.lower().endswith('.csv'):
        flash('CSVファイルを選択してください', 'error')
        return redirect(request.url)

    success_count, error_messages = services.process_csv_upload(file)

    if success_count > 0:
        flash(f'{success_count}件の部員を正常に登録しました', 'success')

    if error_messages:
        for msg in error_messages[:10]:
            flash(msg, 'error')
        if len(error_messages) > 10:
            flash(f'その他{len(error_messages) - 10}件のエラーがあります', 'error')

    return redirect(url_for('members.csv_import'))


@members_bp.route('/download_csv_template')
@login_required
@roles_accepted("administer", "coach", "director")
def download_csv_template():
    template_content = services.generate_csv_template_content()
    return Response(
        template_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=member_template.csv"}
    )


@members_bp.route('/export_csv')  # Blueprintを使用している場合
@login_required
@roles_accepted("administer", "coach", "director")
def export_csv():
    # 部員一覧を取得（必要に応じて権限チェックを追加）

    members_list = services.get_members_list()

    # CSVデータを作成
    output = io.BytesIO()
    wrapper = io.TextIOWrapper(output, encoding='utf-8', newline='')
    writer = csv.writer(wrapper)

    # ヘッダー行
    headers = [
        '氏名',
        '学年',
        '活動状況',
        '登録日',
        'ユーザーID'
    ]
    writer.writerow(headers)

    # データ行
    for member in members_list:
        row = [
            member.name,
            f"{member.grade}年" if member.grade else '',
            '現役' if member.is_active else '引退',
            member.created_at.strftime('%Y-%m-%d'),
            member.user_id
        ]
        writer.writerow(row)

    # レスポンスを作成

    wrapper.flush()
    output.seek(0)
    wrapper.detach()

    # ファイル名を生成
    date_str = datetime.now().strftime('%Y%m%d')
    filename = f"部員一覧_{date_str}.csv"

    # レスポンスヘッダーを設定
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename,
        etag=False
    )
