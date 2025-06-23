import csv
import io
from db_models import User, Role, db, MeasurementRecord
from sqlalchemy.orm import joinedload
from werkzeug.security import generate_password_hash, check_password_hash

# CSV処理のためのユーティリティ関数をインポート
from .utils.csv_utils import parse_csv_file, normalize_csv_row_keys


def get_members_list():
    """ "member" ロールを持つアクティブなユーザーを取得する """
    return User.query.options(joinedload(User.roles)).filter(
        User.roles.any(Role.name == "member")
    ).all()


def register_new_member(name, grade, member_role, password):
    """新しい部員を登録する"""
    hashed_password = generate_password_hash(password)
    role_instance = Role.query.filter_by(name=member_role).first()

    member_instance = User(
        name=name,
        grade=int(grade) if grade else None,
        is_active = True,
        password_hash=hashed_password
    )
    member_instance.roles.append(role_instance)

    try:
        db.session.add(member_instance)
        db.session.commit()
        return True, "部員を登録しました"
    except Exception as e:
        db.session.rollback()
        print(f"部員登録エラー: {e}")
        return False, "部員登録に失敗しました"


def get_member_and_records(member_id):
    """指定された部員の情報と測定記録を取得する"""
    user = User.query.get(member_id)
    if not user:
        return None, None
    records = MeasurementRecord.query.filter_by(user_id=member_id).all()
    return user, records


def delete_member_by_id(member_id):
    """指定された部員をデータベースから削除する"""
    user = User.query.get(member_id)
    if not user:
        return False, "部員が見つかりません"

    try:
        db.session.delete(user)
        db.session.commit()
        return True, "部員を削除しました"
    except Exception as e:
        db.session.rollback()
        print(f"削除エラー: {e}")
        return False, "削除に失敗しました"


def process_csv_upload(csv_file_stream):
    """
    アップロードされたCSVファイルを処理し、部員を一括登録する

    Args:
        csv_file_stream: Werkzeug FileStorage オブジェクトの stream (ファイル内容へのアクセス用)

    Returns:
        tuple: (success_count, error_messages_list)
    """
    success_count = 0
    error_messages = []
    default_password = "password123"
    roles_cache = {r.name: r for r in Role.query.all()}

    if not roles_cache.get('member'):
        error_messages.append('システムエラー: memberロールが存在しません')
        return 0, error_messages

    # csv_utils.py から parse_csv_file を呼び出す
    try:
        rows = parse_csv_file(csv_file_stream)
    except Exception as e:
        error_messages.append(f"CSVファイルの読み込み中にエラーが発生しました: {str(e)}")
        return 0, error_messages

    for row_num, row in enumerate(rows, start=2):  # ヘッダー行を考慮して2から開始
        try:
            normalized_row = normalize_csv_row_keys(row)

            name = normalized_row.get('name') or normalized_row.get('氏名')
            if not name or not name.strip():
                error_messages.append(f"行{row_num}: 氏名が入力されていません")
                continue

            if User.query.filter_by(name=name.strip()).first():
                error_messages.append(f"行{row_num}: 部員「{name}」は既に登録されています")
                continue

            password = (normalized_row.get('password') or
                        normalized_row.get('パスワード') or
                        default_password).strip()

            role_name = (normalized_row.get('role') or
                         normalized_row.get('役割') or
                         'member').lower().strip()
            if role_name == "administer":
                error_messages.append("管理者は既に登録されています")
                continue

            grade = (normalized_row.get('grade') or
                     normalized_row.get('学年') or
                     '').strip()

            is_active = str(normalized_row.get('active') or
                            normalized_row.get('活動') or
                            '1').strip() == '1'

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

    if success_count > 0:
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            error_messages.append(f"データベースコミット中にエラーが発生しました: {str(e)}")
            success_count = 0  # コミット失敗時は成功件数をリセット

    return success_count, error_messages


def generate_csv_template_content():
    """CSVテンプレートのコンテンツを生成する"""
    return """氏名,パスワード,役割,学年,活動
山田太郎,pass123,member,1,1
佐藤花子,pass456,manager,,1
鈴木一郎,,coach,2,0"""
