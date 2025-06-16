from flask import Flask
from flask_login import LoginManager
from flask_security import Security, SQLAlchemyUserDatastore
from flask_migrate import Migrate
from db_models import User, Role, db
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.members import members_bp
from blueprints.measurements import measurements_bp
from blueprints.profile import profile_bp

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
app.register_blueprint(members_bp, url_prefix='/members')
app.register_blueprint(measurements_bp, url_prefix='/measurements')
app.register_blueprint(profile_bp, url_prefix='/profile')

if __name__ == '__main__':
    app.run(debug=True)