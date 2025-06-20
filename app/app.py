from pathlib import Path

from flask import Flask
from flask_login import LoginManager, current_user
from flask_security import Security, SQLAlchemyUserDatastore
from werkzeug.security import generate_password_hash
from services import services

from db_models import User, Role, db, MeasurementRecord, MeasurementType
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.records import records_bp
from blueprints.members import members_bp
from blueprints.measurements import measurements_bp
from blueprints.team import team_bp
from blueprints.profile import profile_bp
from blueprints.notice import notice_bp
from blueprints.admin import admin_bp

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
app.register_blueprint(admin_bp, url_prefix='/admin')


@app.context_processor
def inject_measurement_data():
    if not current_user.is_authenticated:
        return {}

    notice_cnt = 0
    if current_user.has_any_role("manager"):
        notice_cnt = MeasurementRecord.query.filter_by(status='rejected').count()
    elif current_user.has_any_role("member"):
        notice_cnt = MeasurementRecord.query.filter_by(user_id=current_user.user_id, status='draft').count()
    elif current_user.has_any_role("coach"):
        notice_cnt = MeasurementRecord.query.filter_by(status='pending_coach').count()

    return {
        "notice_cnt": notice_cnt
    }


if __name__ == '__main__':
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    db_file = Path(app.instance_path) / "baseball_team.db"

    # データベースファイルの存在チェック
    if db_file.exists():
        print("データベースファイルは存在します")
    else:
        print("データベースファイルが見つかりません - 新規作成します")
        services.initialize_database()

    print("アプリケーションを開始します...")
    app.run(debug=True)
