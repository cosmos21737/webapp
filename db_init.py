from flask import Flask
from db_models import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///baseball_team.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def create_database():
    with app.app_context():
        db.create_all()
        print("Database and tables created!")

if __name__ == "__main__":
    create_database()

