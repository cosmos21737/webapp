import statistics
from datetime import datetime
from zoneinfo import ZoneInfo

from werkzeug.security import generate_password_hash

from db_models import User, Role, db, MeasurementRecord, MeasurementType, MeasurementValue, News, AdminContact

from sqlalchemy import func


def create_record(user_id, measurement_date, created_by, values_dict, comment=None):
    """新しい測定記録を作成"""
    # すべての測定値が入力されているかチェック
    missing_values = []
    all_measurement_types = MeasurementType.query.all()
    
    for m_type in all_measurement_types:
        value = values_dict.get(m_type.name)
        if value is None:
            missing_values.append(m_type.display_name)
    
    if missing_values:
        raise ValueError(f"以下の測定値が入力されていません: {', '.join(missing_values)}")

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
    measurement_types = MeasurementType.query.order_by(MeasurementType.id).all()

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
    measurement_types = MeasurementType.query.order_by(MeasurementType.id).all()

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


def initialize_database(app):
    """データベースの初期化処理"""
    with app.app_context():
        db.drop_all()
        db.create_all()

        create_default_roles()
        register_administer()
        init_measurement_types()

        # サンプルのニュース記事を追加
        news1 = News(title='新しいシーズンが始まります！', content='春季大会に向けて、チーム一丸となって頑張りましょう。応援よろしくお願いします！')
        news2 = News(title='体力測定の結果を公開', content='先日行われた体力測定の結果が、各自のマイページから確認できるようになりました。')
        db.session.add(news1)
        db.session.add(news2)

        # 管理者連絡先を初期化
        contact = AdminContact(
            email="baseball_support@example.com",
            phone="090-1234-5678",
            note="システムに関するお問い合わせはこちらまでご連絡ください。"
        )
        db.session.add(contact)

        db.session.commit()
        print("データベースが初期化されました。")


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
        student_id="admin",
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
        # 走力
        {'name': 'run_50m', 'display_name': '50m走', 'category': '走力', 'unit': '秒', 'evaluation_direction': 'asc'},  # 速いほど良い→昇順
        {'name': 'base_running', 'display_name': 'ベースランニング', 'category': '走力', 'unit': '秒', 'evaluation_direction': 'asc'},
        # 肩力
        {'name': 'throw_distance', 'display_name': '遠投', 'category': '肩力', 'unit': 'm', 'evaluation_direction': 'desc'},
        {'name': 'pitch_speed', 'display_name': 'ストレート球速', 'category': '肩力', 'unit': 'km/h', 'evaluation_direction': 'desc'},
        # 打力
        {'name': 'hit_speed', 'display_name': '打球速度', 'category': '打力', 'unit': 'km/h', 'evaluation_direction': 'desc'},
        {'name': 'swing_speed', 'display_name': 'スイング速度', 'category': '打力', 'unit': 'km/h', 'evaluation_direction': 'desc'},
        # 筋力
        {'name': 'bench_press', 'display_name': 'ベンチプレス', 'category': '筋力', 'unit': 'kg', 'evaluation_direction': 'desc'},
        {'name': 'squat', 'display_name': 'スクワット', 'category': '筋力', 'unit': 'kg', 'evaluation_direction': 'desc'}
    ]

    for type_data in types:
        existing_type = MeasurementType.query.filter_by(name=type_data['name']).first()
        if not existing_type:
            new_type = MeasurementType(**type_data)
            db.session.add(new_type)
            print(f"測定タイプを作成: {type_data['display_name']} ({type_data['category']})")
        else:
            # 既存データのカテゴリを更新
            existing_type.category = type_data['category']
            print(f"測定タイプを更新: {type_data['display_name']} -> {type_data['category']}")

    db.session.commit()
    print("記録項目を登録しました。")


def create_default_roles():
    """デフォルトロールを作成する"""
    roles = [
        {"name": "member", "display_name": "部員"},
        {"name": "manager", "display_name": "マネージャー"},
        {"name": "coach", "display_name": "コーチ"},
        {"name": "director", "display_name": "監督"},
        {"name": "administer", "display_name": "管理者"},
        ]

    created_count = 0

    for role in roles:
        existing_role = Role.query.filter_by(name=role["name"]).first()
        if not existing_role:
            new_role = Role(name=role["name"], display_name=role["display_name"])
            db.session.add(new_role)
            created_count += 1
            print(f"ロール '{role["name"]}' を作成しました")

    if created_count > 0:
        db.session.commit()
        print(f"デフォルトのロール {created_count}個を登録しました！")
    else:
        print("すべてのデフォルトロールは既に存在します")


def calculate_category_evaluations(user_id):
    """カテゴリ別の偏差値平均を計算し、S/A/B/C評価を返す"""
    try:
        # 全測定項目のランキングを取得
        rankings = calculate_rankings(user_id)
        
        # カテゴリ別に偏差値をグループ化
        category_stddevs = {}
        measurement_types = MeasurementType.query.all()
        
        # display_nameからカテゴリへのマッピングを作成
        display_name_to_category = {mt.display_name: mt.category for mt in measurement_types}
        
        for metric_name, data in rankings.items():
            if isinstance(data, dict) and 'stddev' in data and data['stddev'] != "N/A" and data['stddev'] != "Error":
                try:
                    # display_nameからカテゴリを取得
                    category = display_name_to_category.get(metric_name)
                    if category:
                        if category not in category_stddevs:
                            category_stddevs[category] = []
                        category_stddevs[category].append(float(data['stddev']))
                except (ValueError, TypeError):
                    continue
        
        # カテゴリ別の評価を計算
        category_evaluations = {}
        for category, stddev_values in category_stddevs.items():
            if stddev_values:
                average_stddev = sum(stddev_values) / len(stddev_values)
                
                # S/A/B/C評価を判定
                if average_stddev >= 60:
                    grade = "S"
                    grade_color = "danger"  # 赤色
                elif average_stddev >= 52:
                    grade = "A"
                    grade_color = "warning"  # オレンジ色
                elif average_stddev >= 40:
                    grade = "B"
                    grade_color = "primary"  # 青色
                else:
                    grade = "C"
                    grade_color = "secondary"  # グレー色
                
                category_evaluations[category] = {
                    'average_stddev': round(average_stddev, 1),
                    'grade': grade,
                    'grade_color': grade_color,
                    'count': len(stddev_values)  # 評価に使用した測定項目数
                }
        
        return category_evaluations
        
    except Exception as e:
        print(f"Error in calculate_category_evaluations: {str(e)}")
        return {}


def calculate_overall_evaluation(user_id):
    """全測定項目の偏差値平均を計算し、S/A/B/C評価を返す"""
    try:
        # 全測定項目のランキングを取得
        rankings = calculate_rankings(user_id)
        
        # 偏差値のみを抽出
        stddev_values = []
        for metric, data in rankings.items():
            if isinstance(data, dict) and 'stddev' in data and data['stddev'] != "N/A" and data['stddev'] != "Error":
                try:
                    stddev_values.append(float(data['stddev']))
                except (ValueError, TypeError):
                    continue
        
        if not stddev_values:
            return {
                'average_stddev': "N/A",
                'grade': "N/A",
                'grade_color': "secondary"
            }
        
        # 偏差値の平均を計算
        average_stddev = sum(stddev_values) / len(stddev_values)
        
        # S/A/B/C評価を判定
        if average_stddev >= 60:
            grade = "S"
            grade_color = "danger"  # 赤色
        elif average_stddev >= 52:
            grade = "A"
            grade_color = "warning"  # オレンジ色
        elif average_stddev >= 40:
            grade = "B"
            grade_color = "primary"  # 青色
        else:
            grade = "C"
            grade_color = "secondary"  # グレー色
        
        return {
            'average_stddev': round(average_stddev, 1),
            'grade': grade,
            'grade_color': grade_color
        }
        
    except Exception as e:
        print(f"Error in calculate_overall_evaluation: {str(e)}")
        return {
            'average_stddev': "Error",
            'grade': "Error",
            'grade_color': "secondary"
        }


def get_record_category_evaluations(record_id):
    """特定の記録IDに対するカテゴリ評価を計算"""
    try:
        # 記録を取得
        record = MeasurementRecord.query.get(record_id)
        if not record:
            return {}
        
        # 記録の測定値を取得
        record_values = {}
        for value in record.values:
            measurement_type = MeasurementType.query.get(value.type_id)
            if measurement_type:
                record_values[measurement_type.display_name] = value.value
        
        if not record_values:
            return {}
        
        # カテゴリ別に偏差値を計算
        category_stddevs = {}
        measurement_types = MeasurementType.query.all()
        
        # display_nameからカテゴリへのマッピングを作成
        display_name_to_category = {mt.display_name: mt.category for mt in measurement_types}
        
        for metric_name, value in record_values.items():
            if value is not None:
                try:
                    # その測定項目の全ユーザーの値を取得して偏差値を計算
                    all_values = db.session.query(MeasurementValue.value).join(
                        MeasurementRecord,
                        MeasurementValue.record_id == MeasurementRecord.id
                    ).join(
                        MeasurementType,
                        MeasurementValue.type_id == MeasurementType.id
                    ).filter(
                        MeasurementRecord.status == 'approved',
                        MeasurementType.display_name == metric_name,
                        MeasurementValue.value.isnot(None)
                    ).all()
                    
                    if all_values:
                        values_list = [v[0] for v in all_values]
                        avg = sum(values_list) / len(values_list)
                        variance = sum((x - avg) ** 2 for x in values_list) / len(values_list)
                        stddev = variance ** 0.5
                        
                        if stddev != 0:
                            # 偏差値を計算
                            std_score = 50 + 10 * (value - avg) / stddev
                            
                            # カテゴリを取得
                            category = display_name_to_category.get(metric_name)
                            if category:
                                if category not in category_stddevs:
                                    category_stddevs[category] = []
                                category_stddevs[category].append(std_score)
                except (ValueError, TypeError, ZeroDivisionError):
                    continue
        
        # カテゴリ別の評価を計算
        category_evaluations = {}
        for category, stddev_values in category_stddevs.items():
            if stddev_values:
                average_stddev = sum(stddev_values) / len(stddev_values)
                
                # S/A/B/C評価を判定
                if average_stddev >= 60:
                    grade = "S"
                    grade_color = "danger"  # 赤色
                elif average_stddev >= 52:
                    grade = "A"
                    grade_color = "warning"  # オレンジ色
                elif average_stddev >= 40:
                    grade = "B"
                    grade_color = "primary"  # 青色
                else:
                    grade = "C"
                    grade_color = "secondary"  # グレー色
                
                category_evaluations[category] = {
                    'average_stddev': round(average_stddev, 1),
                    'grade': grade,
                    'grade_color': grade_color,
                    'count': len(stddev_values)  # 評価に使用した測定項目数
                }
        
        return category_evaluations
        
    except Exception as e:
        print(f"Error in get_record_category_evaluations: {str(e)}")
        return {}
