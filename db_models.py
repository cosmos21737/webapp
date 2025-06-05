from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from zoneinfo import ZoneInfo



db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.Enum('member', 'manager', 'coach', 'director', name='role_enum'), nullable=False)
    grade = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')), onupdate=datetime.now)

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
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(tz=ZoneInfo('Asia/Tokyo')), onupdate=datetime.now)

    user = db.relationship('User', foreign_keys=[user_id])  # 部員とのリレーション
    creator = db.relationship('User', foreign_keys=[created_by])  # 記録作成者とのリレーション

