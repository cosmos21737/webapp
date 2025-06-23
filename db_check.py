from db_models import db, User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# DBファイルのパス
DB_PATH = "instance/baseball_team.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
session = Session()

ADMIN_ROLES = ['admin', 'administer']

def print_admin_info():
    users = session.query(User).all()
    admins = [u for u in users if any(role in ADMIN_ROLES for role in u.get_role_names())]
    if not admins:
        print("管理者ユーザーが見つかりません。")
        return
    for user in admins:
        print(f"ID: {user.user_id}")
        print(f"ユーザー名: {user.name}")
        print(f"パスワードハッシュ: {user.password_hash}")
        print(f"ロール: {user.get_role_names()}")
        print(f"is_active: {user.is_active}")
        print("-" * 40)

if __name__ == "__main__":
    print_admin_info() 