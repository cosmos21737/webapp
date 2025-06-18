import pandas as pd
from flask import Flask
from flask_security import current_user
from werkzeug.security import generate_password_hash, check_password_hash
from db_models import db, User, Role, MeasurementRecord # ここで引用

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baseball_team.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def create_default_roles():
    roles = ["member", "manager", "coach", "director", "administer"]
    for role_name in roles:
        existing_role = Role.query.filter_by(name=role_name).first()
        if not existing_role:
            new_role = Role(name=role_name)
            db.session.add(new_role)
    db.session.commit()
    print("デフォルトのロールを登録しました！")



def add_user_interactive():
    """ ユーザーの入力を受け取り、データベースへ登録 """
    name = input("氏名を入力してください: ")
    password = input("パスワードを入力してください: ")
    role = input("役割を入力してください (member, manager, coach, director): ")
    grade_input = input("学年を入力してください（部員のみ、未入力なら空白）: ")
    grade = int(grade_input) if grade_input.isdigit() else None
    is_active = input("活動中ですか？ (True/False): ").lower() == 'true'

    hashed_password = generate_password_hash(password)

    new_user = User(name=name, password_hash=hashed_password, role=role, grade=grade, is_active=is_active)

    with app.app_context():
        db.session.add(new_user)
        db.session.commit()
        print(f"ユーザー {name} を追加しました！")


def import_user_csv(filename):
    """ CSVからデータをインポート """
    df = pd.read_csv(filename)

    with app.app_context():
        for _, row in df.iterrows():
            password = row['パスワード']
            hashed_password = generate_password_hash(password)  # 🔥 ハッシュ化
            new_user = User(
                name=row['氏名'],
                password_hash=hashed_password,
                grade=int(row['学年']) if pd.notna(row['学年']) else None,
                is_active=row['活動']
            )
            role_name = row['役割']  # CSV の "役割" カラム
            role = Role.query.filter_by(name=role_name).first()

            if role is None:
                print(f"ロール '{role_name}' がデータベースに存在しません")

            if role:
                new_user.roles.append(role)  # roles に追加

            db.session.add(new_user)
        db.session.commit()
        print(f"{len(df)} 件のユーザーを追加しました！")


def get_users():
    """ 登録済みユーザーをコンソールに表示 """
    with app.app_context():
        users = User.query.all()
        for user in users:
            print(
                f"ID: {user.user_id}, 氏名: {user.name}, 役割: {[role.name for role in user.roles]}, 学年: {user.grade}, 活動中: {user.is_active}")

def import_measurements_csv(filename):
    """ CSVファイルから測定記録データをインポート（名前と学年で検索） """
    df = pd.read_csv(filename, encoding="utf-8")  # 文字コードを指定して読み込む
    df.columns = df.columns.str.strip()  # カラム名の前後のスペースを削除

    print(df.columns)  # 読み込んだカラム名を表示して確認

    with app.app_context():
        for _, row in df.iterrows():
            # 名前と学年で `User` テーブルから `user_id` を検索
            user = User.query.filter_by(name=row['氏名'], grade=row['学年']).first()

            if user:  # 該当するユーザーが見つかった場合
                new_record = MeasurementRecord(
                    user_id=user.user_id,  # 取得した `user_id`
                    measurement_date=pd.to_datetime(row['測定日'], format='%Y/%m/%d').date(),
                    run_50m=row['50m走 [秒]'],
                    base_running=row['ベースランニング [秒]'],
                    long_throw=row['遠投 [m]'],
                    straight_speed=row['ストレート球速 [km/h]'],
                    hit_speed=row['打球速度 [km/h]'],
                    swing_speed=row['スイング速度 [km/h]'],
                    bench_press=row['ベンチプレス [kg]'],
                    squat=row['スクワット [kg]'],
                    status="draft",
                    created_by="test"  # 記録作成者を同じユーザーにする
                )
                db.session.add(new_record)
            else:
                print(f"⚠ ユーザーが見つかりません: {row['氏名']} (学年: {row['学年']})")

        db.session.commit()
        print(f"{len(df)} 件の測定記録データを追加しました！")




def get_measurements():
    """ 測定記録の一覧を表示 """
    with app.app_context():
        records = MeasurementRecord.query.all()
        for record in records:
            print(f"記録ID: {record.record_id}, ユーザーID: {record.user_id}, 測定日: {record.measurement_date}, 50m走: {record.run_50m}, ベースランニング: {record.base_running}, 遠投: {record.long_throw}, ストレート球速: {record.straight_speed}, 打球速度: {record.hit_speed}, スイング速度: {record.swing_speed}, ベンチプレス: {record.bench_press}, スクワット: {record.squat}, ステータス: {record.status}")



if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # データベース作成（初回のみ）
        create_default_roles()

        while True:
            print("\n=== ユーザー管理システム ===")
            print("1: 新規ユーザー追加（手入力）")
            print("2: ユーザー追加（CSV）")
            print("3: 測定記録追加（CSV）")
            print("4: ユーザー一覧表示")
            print("5: 測定記録一覧表示")
            print("6: 終了")
            choice = input("操作を選択してください: ")

            if choice == "1":
                add_user_interactive()
            elif choice == "2":
                filename = input("CSVファイル名を入力してください: ")
                import_user_csv(filename)
            elif choice == "3":
                filename = input("CSVファイル名を入力してください: ")
                import_measurements_csv(filename)
            elif choice == "4":
                get_users()
            elif choice == "5":
                get_measurements()
            elif choice == "6":
                print("終了します。")
                break
            else:
                print("無効な入力です。1, 2, 3, 4 のいずれかを選択してください。")

