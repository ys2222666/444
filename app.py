# app.py
import os
import sys
import uuid  # 添加uuid导入
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 先创建app实例
app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-key-12345-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化扩展
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录以访问此页面。'


# 定义模型（修复UUID生成）
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # 修复这里
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # 修复这里
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    full_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    bio = db.Column(db.Text)

    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    location_visible = db.Column(db.Boolean, default=True)

    phone = db.Column(db.String(20))
    wechat = db.Column(db.String(50))
    contact_visible = db.Column(db.Boolean, default=False)

    profile_visible = db.Column(db.Boolean, default=True)
    virtual_partner_preference = db.Column(db.Text)

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self, include_private=False):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name or '未设置',
            'age': self.age or '未设置',
            'gender': self.gender or '未设置',
            'bio': self.bio or '暂无简介',
        }

        if include_private or self.profile_visible:
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
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))  # 修复这里
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    matched_user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    status = db.Column(db.String(20), default='pending')
    contact_exchanged = db.Column(db.Boolean, default=False)
    contact_exchange_requested = db.Column(db.Boolean, default=False)

    is_virtual_partner = db.Column(db.Boolean, default=False)
    virtual_partner_start = db.Column(db.DateTime)
    virtual_partner_end = db.Column(db.DateTime)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# 工具函数
def validate_email(email):
    import re
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    import re
    if not password or len(password) < 8:
        return False
    if not re.search(r'[A-Za-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    return True


def calculate_distance(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, atan2
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf')

    R = 6371
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad

    a = sin(dlat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def find_potential_matches(user, virtual_partner=False, max_results=20):
    """简化版匹配算法"""
    try:
        # 获取所有可见用户
        other_profiles = UserProfile.query.filter(
            UserProfile.user_id != user.id,
            UserProfile.profile_visible == True
        ).limit(max_results).all()

        matches = []
        for profile in other_profiles:
            match_data = profile.to_dict()
            match_data['match_score'] = 50  # 基础分数

            # 简单计算距离
            if (user.profile.latitude and user.profile.longitude and
                    profile.latitude and profile.longitude):
                distance = calculate_distance(
                    user.profile.latitude, user.profile.longitude,
                    profile.latitude, profile.longitude
                )
                match_data['distance'] = round(distance, 2)

            matches.append(match_data)

        return matches
    except Exception as e:
        print(f"匹配算法错误: {e}")
        return []


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, user_id)


# 创建数据库表
def create_tables():
    with app.app_context():
        try:
            db.create_all()
            print("✅ 数据库表创建成功！")

            # 创建测试用户
            if User.query.count() == 0:
                create_test_users()

        except Exception as e:
            print(f"❌ 数据库创建失败: {e}")


def create_test_users():
    """创建测试用户"""
    try:
        # 测试用户1
        user1 = User(
            username="demo",
            email="demo@example.com",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(user1)
        db.session.commit()  # 先提交获取ID

        profile1 = UserProfile(
            user_id=user1.id,
            full_name="演示用户",
            age=25,
            gender="男",
            bio="这是一个演示用户账号",
            latitude=39.9042,
            longitude=116.4074
        )
        db.session.add(profile1)

        # 测试用户2
        user2 = User(
            username="test",
            email="test@example.com",
            password_hash=generate_password_hash("password123")
        )
        db.session.add(user2)
        db.session.commit()  # 先提交获取ID

        profile2 = UserProfile(
            user_id=user2.id,
            full_name="测试用户",
            age=23,
            gender="女",
            bio="喜欢旅行和阅读",
            latitude=39.9163,
            longitude=116.3972
        )
        db.session.add(profile2)

        db.session.commit()
        print("✅ 测试用户创建成功！")

    except Exception as e:
        db.session.rollback()
        print(f"❌ 创建测试用户失败: {e}")


# 路由定义
@app.route('/')
def index():
    return redirect(url_for('home'))


@app.route('/home')
def home():
    return render_template('home.html')

# 添加缺失的路由
@app.route('/messages')
@login_required
def messages():
    """消息页面"""
    return render_template('messages.html')

@app.route('/settings')
@login_required
def settings():
    """设置页面"""
    return render_template('settings.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if not username or not password:
            flash('请输入用户名和密码', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash('登录成功！', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('用户名或密码错误', 'error')

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not all([username, email, password, confirm_password]):
            flash('请填写所有必填字段', 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('两次输入的密码不一致', 'error')
            return render_template('register.html')

        if not validate_email(email):
            flash('邮箱格式不正确', 'error')
            return render_template('register.html')

        if not validate_password(password):
            flash('密码必须包含字母和数字，且长度至少8位', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('用户名已存在', 'error')
            return render_template('register.html')

        if User.query.filter_by(email=email).first():
            flash('邮箱已被注册', 'error')
            return render_template('register.html')

        try:
            new_user = User(
                username=username,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(new_user)
            db.session.commit()  # 先提交获取ID

            profile = UserProfile(user_id=new_user.id)
            db.session.add(profile)
            db.session.commit()

            flash('注册成功，请登录', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('注册失败，请稍后重试', 'error')
            print(f"注册错误: {e}")

    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('您已成功退出登录', 'success')
    return redirect(url_for('home'))


@app.route('/dashboard')
@login_required
def dashboard():
    # 确保用户有个人资料
    if not hasattr(current_user, 'profile'):
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    pending_requests = 0  # 简化版本
    return render_template('dashboard.html', user=current_user, pending_requests=pending_requests)


@app.route('/nearby')
@login_required
def nearby_people():
    user_profile = current_user.profile

    if not user_profile.latitude or not user_profile.longitude:
        flash('请先设置您的位置信息', 'warning')
        return redirect(url_for('edit_profile'))

    try:
        all_profiles = UserProfile.query.filter(
            UserProfile.user_id != current_user.id,
            UserProfile.profile_visible == True,
            UserProfile.location_visible == True
        ).all()

        nearby_users = []
        for profile in all_profiles:
            if profile.latitude and profile.longitude:
                distance = calculate_distance(
                    user_profile.latitude, user_profile.longitude,
                    profile.latitude, profile.longitude
                )

                if distance <= 50:
                    user_data = profile.to_dict()
                    user_data['distance'] = round(distance, 2)
                    nearby_users.append(user_data)

        nearby_users.sort(key=lambda x: x['distance'])
        return render_template('nearby.html', nearby_users=nearby_users)
    except Exception as e:
        flash('获取附近用户失败', 'error')
        print(f"附近用户错误: {e}")
        return render_template('nearby.html', nearby_users=[])


@app.route('/matching')
@login_required
def matching():
    try:
        potential_matches = find_potential_matches(current_user)
        return render_template('matching.html', potential_matches=potential_matches)
    except Exception as e:
        flash('匹配功能暂时不可用', 'error')
        print(f"匹配错误: {e}")
        return render_template('matching.html', potential_matches=[])


@app.route('/send_match_request/<user_id>', methods=['POST'])
@login_required
def send_match_request(user_id):
    try:
        return jsonify({'success': True, 'message': '匹配请求已发送（演示功能）'})
    except Exception as e:
        return jsonify({'success': False, 'message': '发送失败'})


@app.route('/virtual_partner')
@login_required
def virtual_partner():
    return render_template('virtual_partner.html', current_partner=None, recommendations=[])


@app.route('/profile')
@login_required
def profile():
    # 确保有个人资料
    if not hasattr(current_user, 'profile'):
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    return render_template('profile.html', profile=current_user.profile)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    # 确保有个人资料
    if not hasattr(current_user, 'profile'):
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()

    profile = current_user.profile

    if request.method == 'POST':
        try:
            profile.full_name = request.form.get('full_name', '').strip() or None
            profile.bio = request.form.get('bio', '').strip() or None
            profile.gender = request.form.get('gender', '').strip() or None

            age_str = request.form.get('age', '').strip()
            profile.age = int(age_str) if age_str and age_str.isdigit() else None

            lat_str = request.form.get('latitude', '').strip()
            lon_str = request.form.get('longitude', '').strip()
            profile.latitude = float(lat_str) if lat_str else None
            profile.longitude = float(lon_str) if lon_str else None

            profile.phone = request.form.get('phone', '').strip() or None
            profile.wechat = request.form.get('wechat', '').strip() or None

            profile.profile_visible = 'profile_visible' in request.form
            profile.location_visible = 'location_visible' in request.form
            profile.contact_visible = 'contact_visible' in request.form

            db.session.commit()
            flash('个人资料已更新', 'success')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash('更新失败，请检查输入数据', 'error')
            print(f"更新资料错误: {e}")

    return render_template('edit_profile.html', profile=profile)


# 错误处理
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500


if __name__ == '__main__':
    create_tables()

    print("=" * 50)
    print("🎉 交友平台启动成功！")
    print("📍 访问地址: http://127.0.0.1:5000")
    print("👤 测试账号: demo / password123")
    print("👤 测试账号: test / password123")
    print("=" * 50)

    app.run(debug=True, host='0.0.0.0', port=5000)