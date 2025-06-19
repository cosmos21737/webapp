from pathlib import Path

from flask import Flask
from flask_login import LoginManager, current_user
from flask_security import Security, SQLAlchemyUserDatastore
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash

from db_models import User, Role, db, MeasurementRecord
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.records import records_bp
from blueprints.members import members_bp
from blueprints.measurements import measurements_bp
from blueprints.team import team_bp
from blueprints.profile import profile_bp
from blueprints.notice import notice_bp

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッション用の秘密キー
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baseball_team.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_REGISTERABLE'] = True  # ユーザー登録を有効化
app.config['SECURITY_PASSWORD_SALT'] = 'random_salt'
app.config['SECURITY_ROLE_TABLE'] = 'roles'

db.init_app(app)
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)
migrate = Migrate(app, db)

# Flask-Login のセットアップ
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)  # ← ここで初期化


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Blueprint の登録
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(records_bp, url_prefix='/records')
app.register_blueprint(members_bp, url_prefix='/members')
app.register_blueprint(measurements_bp, url_prefix='/measurements')
app.register_blueprint(team_bp, url_prefix='/team')
app.register_blueprint(profile_bp, url_prefix='/profile')
app.register_blueprint(notice_bp, url_prefix='/notice')


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


def register_administer():
    """管理者ユーザーを登録する"""
    # 既存の管理者をチェック
    existing_admin = User.query.join(User.roles).filter(Role.name == "administer").first()
    if existing_admin:
        print("管理者は既に存在します")
        return True, "管理者は既に存在します"

    password = "password123"
    hashed_password = generate_password_hash(password)

    # administratorロールを取得
    admin_role = Role.query.filter_by(name="administer").first()
    if not admin_role:
        print("ロール 'administer' が見つかりません")
        return False, "ロールが存在しません"

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


def initialize_database():
    """データベースの初期化処理"""
    with app.app_context():
        # テーブルを作成
        db.create_all()
        print("データベーステーブルを作成しました")

        # デフォルトロールを作成
        create_default_roles()

        # 管理者を登録
        success, message = register_administer()
        if not success:
            print(f"管理者登録失敗: {message}")
        else:
            print(f"管理者登録成功: {message}")


if __name__ == '__main__':
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db_file = Path(app.instance_path) / "baseball_team.db"

    # データベースファイルの存在チェック
    if db_file.exists():
        print("データベースファイルは存在します")
        # 既存のデータベースでも初期データをチェック・作成
        with app.app_context():
            create_default_roles()  # 不足しているロールがあれば追加
            register_administer()  # 管理者が存在しなければ追加
    else:
        print("データベースファイルが見つかりません - 新規作成します")
        initialize_database()

    print("アプリケーションを開始します...")
    app.run(debug=True)
