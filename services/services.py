import statistics
from datetime import datetime
from zoneinfo import ZoneInfo
from app import app


from flask import current_app
from werkzeug.security import generate_password_hash

from db_models import User, Role, db, MeasurementRecord, MeasurementType, MeasurementValue

from sqlalchemy import func


def create_record(user_id, measurement_date, created_by, values_dict, comment=None):
    """新しい測定記録を作成"""
    record = MeasurementRecord(
        user_id=user_id,
        measurement_date=measurement_date,
        created_by=created_by,
        comment=comment,
        status='draft'
    )

    db.session.add(record)
    db.session.flush()  # record.idを取得するために必要

    for type_name, value in values_dict.items():
        m_type = MeasurementType.query.filter_by(name=type_name).first()
        if m_type and value is not None:
            m_value = MeasurementValue(
                record_id=record.id,
                type_id=m_type.id,
                value=value
            )
            db.session.add(m_value)

    db.session.commit()
    return record


def get_record_values(record_id):
    """記録IDから測定値を辞書形式で取得"""
    record = MeasurementRecord.query.get_or_404(record_id)
    values = {v.type.name: v.value for v in record.values}
    return values


def update_record_values(record_id, values_dict):
    """測定値を更新"""
    record = MeasurementRecord.query.get_or_404(record_id)

    for type_name, value in values_dict.items():
        m_type = MeasurementType.query.filter_by(name=type_name).first()
        if not m_type:
            continue

        # 既存の値を検索
        existing = MeasurementValue.query.filter_by(
            record_id=record.id,
            type_id=m_type.id
        ).first()

        if existing:
            existing.value = value
        else:
            new_value = MeasurementValue(
                record_id=record.id,
                type_id=m_type.id,
                value=value
            )
            db.session.add(new_value)

    record.updated_at = datetime.now(tz=ZoneInfo('Asia/Tokyo'))
    db.session.commit()


def get_user_records(member_id, status='approved'):
    """ユーザーの測定記録を取得"""
    return MeasurementRecord.query.filter_by(
        user_id=member_id,
        status=status
    ).order_by(MeasurementRecord.measurement_date.desc()).all()


def calculate_rankings(member_id):
    """全測定項目のランキングを計算"""
    rankings = {}
    measurement_types = MeasurementType.query.all()

    for m_type in measurement_types:
        rankings[m_type.display_name] = calculate_rank(
            member_id,
            m_type.name,
            m_type.evaluation_direction == 'asc'
        )

    return rankings


def calculate_rank(user_id, metric_name, asc=True):
    """特定の測定項目のランクを計算"""
    try:
        # 1. 各ユーザーの最新の測定値を取得
        subquery = db.session.query(
            MeasurementRecord.user_id,
            MeasurementValue.value.label('target_value')
        ).join(
            MeasurementValue,
            MeasurementRecord.id == MeasurementValue.record_id
        ).join(
            MeasurementType,
            MeasurementValue.type_id == MeasurementType.id
        ).filter(
            MeasurementRecord.status == 'approved',
            MeasurementType.name == metric_name
        ).group_by(
            MeasurementRecord.user_id
        ).subquery()

        # 2. 対象ユーザーの値を取得
        user_value = db.session.query(
            subquery.c.target_value
        ).filter(
            subquery.c.user_id == user_id
        ).scalar()

        if user_value is None:
            return {'rank': "N/A", 'stddev': "N/A", 'value': "N/A"}

        # 3. 全ユーザーの値を取得して統計計算
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

        # 4. 順位計算
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
        rank = int(rank)

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


def calculate_statuses():
    """全測定項目のランキングを計算"""
    rankings = {}
    measurement_types = MeasurementType.query.all()

    for m_type in measurement_types:
        rankings[m_type.display_name] = calculate_status(
            m_type.name,
            m_type.evaluation_direction == 'asc'
        )
    print("start")
    return rankings


def calculate_status(metric_name, asc=True):
    """特定の測定項目のランクを計算"""
    try:
        # 1. 各ユーザーの最新の測定値を取得
        subquery = db.session.query(
            MeasurementRecord.user_id,
            MeasurementValue.value.label('target_value')
        ).join(
            MeasurementValue,
            MeasurementRecord.id == MeasurementValue.record_id
        ).join(
            MeasurementType,
            MeasurementValue.type_id == MeasurementType.id
        ).filter(
            MeasurementRecord.status == 'approved',
            MeasurementType.name == metric_name
        ).group_by(
            MeasurementRecord.user_id
        ).subquery()

        # 2. チームの平均を取得

        team_members = db.session.query(User.user_id).filter(User.team_status == True).all()
        team_values = []

        for member_id in team_members:
            member_value = db.session.query(
                subquery.c.target_value
            ).filter(
                subquery.c.user_id == member_id[0]
            ).scalar()
            team_values.append(member_value)

        team_avg = statistics.mean(team_values)

        if team_values is None:
            print("part1")
            return {'stddev': "N/A", 'value': "N/A"}

        # 3. 全ユーザーの値を取得して統計計算
        all_values = [x[0] for x in db.session.query(
            subquery.c.target_value
        ).filter(
            subquery.c.target_value.isnot(None)
        ).all()]

        if not all_values:
            print("part2")
            return {'stddev': "N/A", 'value': "N/A"}

        avg = sum(all_values) / len(all_values)
        variance = sum((x - avg) ** 2 for x in all_values) / len(all_values)
        stddev = variance ** 0.5

        # 偏差値計算
        def calc_std_score(value, avg, stddev):
            return 50 + 10 * (value - avg) / stddev if stddev != 0 else 50

        return {
            'stddev': round(calc_std_score(team_avg, avg, stddev), 1),
            'value': round(team_avg, 2)
        }

    except Exception as e:
        print(f"Error in calculate_status: {str(e)}")
        return {'stddev': "Error", 'value': "Error"}


def initialize_database():
    """データベースの初期化処理"""
    with app.app_context():
        # テーブルを作成
        db.create_all()
        print("データベーステーブルを作成しました")

        # デフォルトロールを作成
        create_default_roles()
        # 記録項目を追加
        init_measurement_types()

        # 管理者を登録
        success, message = register_administer()
        if not success:
            print(f"管理者登録失敗: {message}")
        else:
            print(f"管理者登録成功: {message}")


def register_administer():
    """管理者ユーザーを登録する"""
    # 既存の管理者をチェック
    existing_admin = User.query.join(User.roles).filter(Role.name == "administer").first()
    if existing_admin:
        print("管理者は既に存在します")
        return True, "管理者は既に存在します"

    password = "password123"
    hashed_password = generate_password_hash(password)
    admin_role = Role.query.filter_by(name="administer").first()

    # 管理者ユーザーを作成
    admin_user = User(
        name="管理者",
        is_active=True,
        password_hash=hashed_password
    )
    admin_user.roles.append(admin_role)

    try:
        db.session.add(admin_user)
        db.session.commit()
        print("管理者を登録しました")
        return True, "管理者を登録しました"
    except Exception as e:
        db.session.rollback()
        print(f"登録エラー: {e}")
        return False, f"管理者登録に失敗しました: {e}"


def init_measurement_types():
    types = [
        {'name': 'run_50m', 'display_name': '50m走', 'unit': '秒', 'evaluation_direction': 'desc'},  # 速いほど良い→降順
        {'name': 'base_running', 'display_name': 'ベースランニング', 'unit': '秒', 'evaluation_direction': 'desc'},
        {'name': 'long_throw', 'display_name': '遠投距離', 'unit': 'm', 'evaluation_direction': 'asc'},
        {'name': 'straight_speed', 'display_name': 'ストレート球速', 'unit': 'km/h', 'evaluation_direction': 'asc'},
        {'name': 'hit_speed', 'display_name': '打球速度', 'unit': 'km/h', 'evaluation_direction': 'asc'},
        {'name': 'swing_speed', 'display_name': 'スイング速度', 'unit': 'km/h', 'evaluation_direction': 'asc'},
        {'name': 'bench_press', 'display_name': 'ベンチプレス', 'unit': 'kg', 'evaluation_direction': 'asc'},
        {'name': 'squat', 'display_name': 'スクワット', 'unit': 'kg', 'evaluation_direction': 'asc'}
    ]

    for type_data in types:
        if not MeasurementType.query.filter_by(name=type_data['name']).first():
            new_type = MeasurementType(**type_data)
            db.session.add(new_type)

    db.session.commit()
    print("記録項目を登録しました。")


def create_default_roles():
    """デフォルトロールを作成する"""
    roles = ["member", "manager", "coach", "director", "administer"]
    created_count = 0

    for role_name in roles:
        existing_role = Role.query.filter_by(name=role_name).first()
        if not existing_role:
            new_role = Role(name=role_name)
            db.session.add(new_role)
            created_count += 1
            print(f"ロール '{role_name}' を作成しました")

    if created_count > 0:
        db.session.commit()
        print(f"デフォルトのロール {created_count}個を登録しました！")
    else:
        print("すべてのデフォルトロールは既に存在します")
