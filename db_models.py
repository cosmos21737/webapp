import sqlite3
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import event, create_engine

db = SQLAlchemy()
engine = create_engine('sqlite:///your_database.db')


@event.listens_for(engine, "connect")
def enable_extensions(dbapi_conn, connection_record):
    if isinstance(dbapi_conn, sqlite3.Connection):
        try:
            dbapi_conn.enable_load_extension(True)
            dbapi_conn.load_extension('sqlite3-stddev')
        except:
            pass


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
    team_status = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')),
                           onupdate=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))

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

    def has_any_role(self, *roles):
        return any(role.name in roles for role in self.roles)


# **測定記録モデル**
class MeasurementType(db.Model):
    """測定項目の種類を管理するテーブル"""
    __tablename__ = 'measurement_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # プログラム内で使用する識別子 (例: 'run_50m')
    display_name = db.Column(db.String(100), nullable=False)  # 表示用名称 (例: '50m走')
    unit = db.Column(db.String(20))  # 単位 (例: '秒', 'km/h', 'm')
    evaluation_direction = db.Column(                            # 評価方向
        db.Enum('asc', 'desc', name='evaluation_direction_enum'),
        nullable=False,
        default='asc'
    )
    description = db.Column(db.Text)  # 説明文 (任意)


class MeasurementRecord(db.Model):
    """測定記録の基本情報を管理するテーブル"""
    __tablename__ = 'measurement_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    measurement_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum('draft', 'pending_coach', 'approved', 'rejected', name='status_enum'),
                       nullable=False, default='draft')
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')),
                           onupdate=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))
    comment = db.Column(db.String(1000))

    # リレーション
    user = db.relationship('User', foreign_keys=[user_id])
    creator = db.relationship('User', foreign_keys=[created_by])
    values = db.relationship('MeasurementValue', back_populates='record', cascade='all, delete-orphan')


class MeasurementValue(db.Model):
    """個々の測定値を管理するテーブル"""
    __tablename__ = 'measurement_values'

    id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey('measurement_records.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('measurement_types.id', ondelete='CASCADE'), nullable=False)
    value = db.Column(db.Float, nullable=False)

    # リレーション
    record = db.relationship('MeasurementRecord', back_populates='values')
    type = db.relationship('MeasurementType')

    # 複合ユニーク制約（同じ記録で同じ測定タイプを重複させない）
    __table_args__ = (
        db.UniqueConstraint('record_id', 'type_id', name='_record_type_uc'),
    )