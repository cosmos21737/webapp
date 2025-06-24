import io
import csv
from datetime import datetime

from flask import Blueprint, request, render_template, redirect, url_for, flash, Response, send_file
from flask_security import login_required, current_user, roles_required, roles_accepted
from sqlalchemy import func
from db_models import db, User, MeasurementRecord, Role

# service をインポート
from . import members_bp
from . import services


@members_bp.route('/')
@login_required
@roles_accepted("administer", "coach", "director")
def members():
    # 現在のページネーションの行を削除またはコメントアウトし、すべてのユーザーを取得する
    # pagination = User.query.filter(~User.roles.any(Role.name == 'administer')).order_by(sort_column).paginate(page=page, per_page=per_page)
    # members_list = pagination.items

    # すべてのメンバーを取得する (または、フロントエンドで処理できる適切なサブセット)
    members_list = User.query.filter(~User.roles.any(Role.name == 'administer')).all()

    return render_template('members/members.html',
                           members=members_list,
                           # paginationオブジェクトは不要になるため削除
                           # sort_byとsort_orderも不要になるため削除
                           )


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
    grade = request.form.get('member_grade')
    member_role = request.form.get('member_role')
    password = "password123"  # 固定パスワード

    success, message = services.register_new_member(name, grade, member_role, password)
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('members.members'))


@members_bp.route('/records/<int:member_id>')
@login_required
@roles_accepted("administer", "coach", "director")
def member_records(member_id):
    return redirect(url_for('records.records', member_id=member_id))


@members_bp.route('/push_team/<int:member_id>', methods=['POST'])
@login_required
@roles_accepted("administer", "coach", "director")
def push_team(member_id):
    user = db.session.get(User, member_id)
    if user:  # ユーザーが存在するかチェック
        user.team_status = True
        db.session.commit()  # 変更をデータベースに保存
        flash('チームステータスを更新しました', 'success')
    else:
        flash('ユーザーが見つかりません', 'error')
    return redirect(url_for('members.members'))


@members_bp.route('/delete_team/<int:member_id>', methods=['POST'])
@login_required
@roles_accepted("administer", "coach", "director")
def delete_team(member_id):
    user = db.session.get(User, member_id)
    if user:  # ユーザーが存在するかチェック
        user.team_status = False
        db.session.commit()  # 変更をデータベースに保存
        flash('チームステータスを更新しました', 'success')
    else:
        flash('ユーザーが見つかりません', 'error')
    return redirect(url_for('members.members'))


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
