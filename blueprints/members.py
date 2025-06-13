import csv
import io

from flask import Blueprint, request, render_template, redirect, url_for, flash, Response
from db_models import User, Role, db, MeasurementRecord
from flask_security import login_required, current_user, roles_required, roles_accepted
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash, check_password_hash
from db_models import db, User

members_bp = Blueprint('members', __name__, url_prefix='/members')


@members_bp.route('/')
@login_required
@roles_accepted("coach", "director")
def members():
    # "member" ロールを持つアクティブなユーザーを取得
    members_list = User.query.options(joinedload(User.roles)).filter(
        User.is_active == True,
        User.roles.any(Role.name == "member")  # ここが修正点
    ).all()

    return render_template('/members/members.html', members=members_list)


@members_bp.route('/new')
@login_required
@roles_accepted("coach", "director")
def new_member():
    return render_template('/members/new_member.html')  # 部員登録ページへ


@members_bp.route('/register', methods=['POST'])
@login_required
@roles_accepted("coach", "director")
def register_member():
    name = request.form.get('name')
    grade = request.form.get('grade')
    is_active = request.form.get('is_active') == "true"
    password = "mypassword123"
    hashed_password = generate_password_hash(password)

    # "member" ロールを取得
    member_role = Role.query.filter_by(name="member").first()
    if not member_role:
        print("エラー: 'member' ロールがデータベースに存在しません")
        return redirect(url_for('members.members'))

    # ユーザーを作成してロールを追加
    member_instance = User(
        name=name,
        grade=int(grade) if grade else None,
        is_active=is_active,
        password_hash=hashed_password
    )
    member_instance.roles.append(member_role)  # 多対多リレーションを適用

    db.session.add(member_instance)
    db.session.commit()

    return redirect(url_for('members.members'))


@members_bp.route('/records/<int:member_id>')
@login_required
@roles_accepted("coach", "director")
def member_records(member_id):
    user = User.query.get(member_id)  # 指定された部員の情報を取得
    if not user:
        return "部員が見つかりません", 404

    records = MeasurementRecord.query.filter_by(user_id=member_id).all()
    return render_template('my/records.html', user=user, records=records)


@members_bp.route('/delete/<int:member_id>', methods=['POST'])
@login_required
@roles_accepted("coach", "director")
def delete_member(member_id):
    user = User.query.get(member_id)
    if not user:
        return "部員が見つかりません", 404

    try:
        db.session.delete(user)
        db.session.commit()
    except Exception as e:
        print(f"削除エラー: {e}")
        db.session.rollback()
        return "削除に失敗しました", 500

    return redirect(url_for('members.members'))


@members_bp.route('/csv_import', methods=['GET', 'POST'])
@login_required
@roles_accepted("coach", "director")
def csv_import():
    """CSV一括インポート画面とファイル処理"""
    if request.method == 'GET':
        return render_template('/members/csv_import.html')

    # POST処理
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

    try:
        # CSVファイルを読み込み（自動で区切り文字判定）
        file_content = file.stream.read().decode("UTF8")
        dialect = csv.Sniffer().sniff(file_content.split('\n')[0])
        stream = io.StringIO(file_content, newline=None)
        csv_reader = csv.DictReader(stream, dialect=dialect)

        success_count = 0
        error_messages = []
        default_password = "password123"
        roles_cache = {r.name: r for r in Role.query.all()}

        if not roles_cache.get('member'):
            flash('システムエラー: memberロールが存在しません', 'error')
            return redirect(url_for('members.csv_import'))

        for row_num, row in enumerate(csv_reader, start=2):
            try:
                # フィールド名の正規化（大文字小文字、全角半角を統一）
                normalized_row = {
                    key.strip().lower().translate(str.maketrans('　', ' ')): value
                    for key, value in row.items()
                }

                # 必須フィールドの検証
                name = normalized_row.get('name') or normalized_row.get('氏名')
                if not name or not name.strip():
                    error_messages.append(f"行{row_num}: 氏名が入力されていません")
                    continue

                # 既存ユーザーチェック
                if User.query.filter_by(name=name.strip()).first():
                    error_messages.append(f"行{row_num}: 部員「{name}」は既に登録されています")
                    continue

                # 各種フィールド取得
                password = (normalized_row.get('password') or
                           normalized_row.get('パスワード') or
                           default_password).strip()

                role_name = (normalized_row.get('role') or
                           normalized_row.get('役割') or
                           'member').lower().strip()

                grade = (normalized_row.get('grade') or
                        normalized_row.get('学年') or
                        '').strip()

                is_active = str(normalized_row.get('active') or
                            normalized_row.get('活動') or
                            '1').strip() == '1'

                # ユーザー作成
                new_user = User(
                    name=name.strip(),
                    grade=int(grade) if grade and grade.isdigit() else None,
                    is_active=is_active,
                    password_hash=generate_password_hash(password)
                )
                new_user.roles.append(roles_cache.get(role_name) or roles_cache['member'])

                db.session.add(new_user)
                success_count += 1

            except Exception as e:
                error_messages.append(f"行{row_num}: 処理中にエラーが発生しました - {str(e)}")

        # データベースにコミット
        if success_count > 0:
            db.session.commit()
            flash(f'{success_count}件の部員を正常に登録しました', 'success')

        if error_messages:
            for msg in error_messages[:10]:
                flash(msg, 'error')
            if len(error_messages) > 10:
                flash(f'その他{len(error_messages) - 10}件のエラーがあります', 'error')

    except Exception as e:
        db.session.rollback()
        flash(f'CSVファイルの処理中にエラーが発生しました: {str(e)}', 'error')

    return redirect(url_for('members.csv_import'))


@members_bp.route('/download_csv_template')
@login_required
@roles_accepted("coach", "director")
def download_csv_template():
    """CSVテンプレートファイルのダウンロード"""
    template_content = """氏名,パスワード,役割,学年,活動
山田太郎,pass123,member,1,1
佐藤花子,pass456,manager,,1
鈴木一郎,,coach,2,0"""

    return Response(
        template_content,
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=member_template.csv"}
    )