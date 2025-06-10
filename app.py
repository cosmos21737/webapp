from flask import Flask
from db_models import db
from blueprints.main import main_bp
from blueprints.auth import auth_bp
from blueprints.members import members_bp
from blueprints.measurements import measurements_bp

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッション用の秘密キー
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baseball_team.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

app.register_blueprint(main_bp)
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(members_bp, url_prefix='/members')
app.register_blueprint(measurements_bp, url_prefix='/measurements')

if __name__ == '__main__':
    app.run(debug=True)