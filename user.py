from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import uuid

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联个人资料
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    # 发送的匹配请求
    sent_matches = db.relationship('Match', foreign_keys='Match.user_id', backref='sender', lazy='dynamic')
    # 接收的匹配请求
    received_matches = db.relationship('Match', foreign_keys='Match.matched_user_id', backref='receiver',
                                       lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    # 基本信息
    full_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    bio = db.Column(db.Text)

    # 地理位置
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_visible = db.Column(db.Boolean, default=True)

    # 联系信息
    phone = db.Column(db.String(20))
    wechat = db.Column(db.String(50))
    contact_visible = db.Column(db.Boolean, default=False)

    # 隐私设置
    profile_visible = db.Column(db.Boolean, default=True)

    # 虚拟恋人偏好
    virtual_partner_preference = db.Column(db.Text)  # JSON格式存储偏好设置

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_private=False):
        """将个人资料转换为字典，根据隐私设置决定是否显示敏感信息"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'age': self.age,
            'gender': self.gender,
            'bio': self.bio,
        }

        if include_private or self.profile_visible:
            # 只有在查看自己资料或对方开放资料时才显示完整信息
            if include_private or self.location_visible:
                data.update({
                    'latitude': self.latitude,
                    'longitude': self.longitude
                })

            if include_private or self.contact_visible:
                data.update({
                    'phone': self.phone,
                    'wechat': self.wechat
                })

        return data


class Match(db.Model):
    __tablename__ = 'matches'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)  # 发送者
    matched_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)  # 接收者

    # 匹配状态: pending, accepted, rejected, blocked
    status = db.Column(db.String(20), default='pending')

    # 联系方式交换
    contact_exchanged = db.Column(db.Boolean, default=False)
    contact_exchange_requested = db.Column(db.Boolean, default=False)

    # 虚拟恋人关系
    is_virtual_partner = db.Column(db.Boolean, default=False)
    virtual_partner_start = db.Column(db.DateTime)
    virtual_partner_end = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Match {self.user_id} -> {self.matched_user_id}: {self.status}>'