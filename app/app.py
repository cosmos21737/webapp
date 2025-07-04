import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pathlib import Path
from dotenv import load_dotenv

from flask import Flask, g
from flask_login import LoginManager, current_user
from flask_security.core import Security
from flask_security.datastore import SQLAlchemyUserDatastore

from db_models import User, Role, db, MeasurementRecord, MeasurementType
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.records import records_bp
from blueprints.members import members_bp
from blueprints.measurements import measurements_bp
from blueprints.team import team_bp
from blueprints.profile import profile_bp
from blueprints.notice import notice_bp
from blueprints.news import news_bp
from blueprints.admin import admin_bp
from services.services import initialize_database

# Load environment variables
load_dotenv()

app = Flask(__name__)

# テスト用サイト用の強固なシークレットキー
app.secret_key = 'baseball_team_2024_secure_key_32chars_long_for_test'
app.config['SECRET_KEY'] = 'baseball_team_2024_secure_key_32chars_long_for_test'

# Database configuration - support both PostgreSQL and SQLite
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    # Convert postgres:// to postgresql:// for newer versions
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///baseball_team.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_PASSWORD_SALT'] = 'baseball_team_2024_salt_16chars'
app.config['SECURITY_ROLE_TABLE'] = 'roles'

def nl2br(value):
    from markupsafe import Markup, escape
    return Markup('<br>'.join(escape(value).split('\n')))
app.jinja_env.filters['nl2br'] = nl2br

db.init_app(app)
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Flask-Login のセットアップ
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # type: ignore
login_manager.init_app(app)  # ← ここで初期化

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Blueprint の登録
app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(records_bp, url_prefix='/records')
app.register_blueprint(members_bp, url_prefix='/members')
app.register_blueprint(measurements_bp, url_prefix='/measurements')
app.register_blueprint(team_bp, url_prefix='/team')
app.register_blueprint(profile_bp, url_prefix='/profile')
app.register_blueprint(notice_bp, url_prefix='/notice')
app.register_blueprint(news_bp, url_prefix='/news')
app.register_blueprint(admin_bp, url_prefix='/admin')


@app.context_processor
def inject_measurement_data():
    if not current_user.is_authenticated:
        return {}

    notice_cnt = 0
    if current_user.has_any_role("manager"):
        notice_cnt = MeasurementRecord.query.filter_by(created_by=current_user.user_id, status='rejected').count()
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
        initialize_database(app)

    print("アプリケーションを開始します...")
    app.run(debug=True)
