import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from datetime import datetime
from zoneinfo import ZoneInfo

db = SQLAlchemy()

# **ロールモデル (Flask-Security 用)**
class Role(db.Model, RoleMixin):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

# **ユーザーロールの中間テーブル (多対多)**
class UserRoles(db.Model):
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

# **ユーザーモデル (Flask-Security 用)**
class User(db.Model, UserMixin):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))  # 追加
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    grade = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')), onupdate=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))

    # **Flask-Security のロール管理**
    roles = db.relationship('Role', secondary='user_roles', backref=db.backref('users', lazy='dynamic'))

    def get_id(self):
        return str(self.user_id)  # Flask-Login 用の get_id()

    # ユーザーの役割名リストを取得する便利メソッド
    def get_role_names(self):
        return [role.name for role in self.roles]

    # フォーマットされた登録日を取得
    def get_formatted_created_at(self):
        return self.created_at.strftime('%Y/%m/%d') if self.created_at else "不明"

    # ユーザーの学年表示用
    def get_grade_display(self):
        return f"{self.grade}年生" if self.grade else "未設定"

# **測定記録モデル**
class MeasurementRecord(db.Model):
    __tablename__ = 'measurement_records'

    record_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # 部員のユーザーID
    measurement_date = db.Column(db.Date, nullable=False)  # 測定日
    run_50m = db.Column(db.Float)  # 50m走
    base_running = db.Column(db.Float)  # ベースランニング
    long_throw = db.Column(db.Float)  # 遠投距離
    straight_speed = db.Column(db.Float)  # ストレート球速
    hit_speed = db.Column(db.Float)  # 打球速度
    swing_speed = db.Column(db.Float)  # スイング速度
    bench_press = db.Column(db.Float)  # ベンチプレス
    squat = db.Column(db.Float)  # スクワット
    status = db.Column(db.Enum('draft', 'pending_member', 'pending_coach', 'approved', name='status_enum'), nullable=False)  # 承認ステータス
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)  # 記録作成者のユーザーID
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')), onupdate=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))

    # **リレーション (Flask-Security に適合)**
    user = db.relationship('User', foreign_keys=[user_id])  # 部員とのリレーション
    creator = db.relationship('User', foreign_keys=[created_by])  # 記録作成者とのリレーション

