import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
import hashlib
import json
import os

# 页面设置
st.set_page_config(
    page_title="交友互动平台",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 数据存储（简化版，实际使用时可以连接数据库）
if 'users' not in st.session_state:
    st.session_state.users = {}
if 'profiles' not in st.session_state:
    st.session_state.profiles = {}
if 'matches' not in st.session_state:
    st.session_state.matches = []
if 'current_user' not in st.session_state:
    st.session_state.current_user = None


# 工具函数
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def validate_email(email):
    import re
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)


def create_test_data():
    """创建测试数据"""
    if not st.session_state.users:
        # 测试用户1
        user1_id = str(uuid.uuid4())
        st.session_state.users[user1_id] = {
            'id': user1_id,
            'username': 'demo',
            'email': 'demo@example.com',
            'password_hash': hash_password('password123'),
            'created_at': datetime.now()
        }
        st.session_state.profiles[user1_id] = {
            'user_id': user1_id,
            'full_name': '演示用户',
            'age': 25,
            'gender': '男',
            'bio': '喜欢运动、音乐和旅行，希望找到志同道合的朋友',
            'city': '北京',
            'interests': ['运动', '音乐', '旅行', '美食'],
            'latitude': 39.9042,
            'longitude': 116.4074
        }

        # 测试用户2
        user2_id = str(uuid.uuid4())
        st.session_state.users[user2_id] = {
            'id': user2_id,
            'username': 'test',
            'email': 'test@example.com',
            'password_hash': hash_password('password123'),
            'created_at': datetime.now()
        }
        st.session_state.profiles[user2_id] = {
            'user_id': user2_id,
            'full_name': '测试用户',
            'age': 23,
            'gender': '女',
            'bio': '热爱阅读和摄影，期待遇见有趣的灵魂',
            'city': '上海',
            'interests': ['阅读', '摄影', '电影', '咖啡'],
            'latitude': 31.2304,
            'longitude': 121.4737
        }


# 初始化测试数据
create_test_data()


# 认证函数
def login_user(username, password):
    for user_id, user in st.session_state.users.items():
        if user['username'] == username and user['password_hash'] == hash_password(password):
            st.session_state.current_user = user
            return True
    return False


def register_user(username, email, password):
    # 检查用户名是否已存在
    for user in st.session_state.users.values():
        if user['username'] == username:
            return False, "用户名已存在"
        if user['email'] == email:
            return False, "邮箱已被注册"

    if not validate_email(email):
        return False, "邮箱格式不正确"

    if len(password) < 6:
        return False, "密码长度至少6位"

    user_id = str(uuid.uuid4())
    st.session_state.users[user_id] = {
        'id': user_id,
        'username': username,
        'email': email,
        'password_hash': hash_password(password),
        'created_at': datetime.now()
    }

    # 创建默认个人资料
    st.session_state.profiles[user_id] = {
        'user_id': user_id,
        'full_name': '',
        'age': None,
        'gender': '',
        'bio': '',
        'city': '',
        'interests': [],
        'latitude': None,
        'longitude': None
    }

    return True, "注册成功"


# 匹配算法
def find_matches(current_user_id, max_results=10):
    current_profile = st.session_state.profiles.get(current_user_id, {})
    if not current_profile:
        return []

    matches = []
    for user_id, profile in st.session_state.profiles.items():
        if user_id == current_user_id:
            continue

        # 计算匹配分数
        score = 0

        # 年龄匹配（相差5岁内加分）
        if current_profile.get('age') and profile.get('age'):
            age_diff = abs(current_profile['age'] - profile['age'])
            if age_diff <= 5:
                score += 30
            elif age_diff <= 10:
                score += 15

        # 兴趣匹配
        current_interests = set(current_profile.get('interests', []))
        other_interests = set(profile.get('interests', []))
        common_interests = current_interests.intersection(other_interests)
        if common_interests:
            score += len(common_interests) * 10

        # 位置匹配（简化版）
        if (current_profile.get('city') and profile.get('city') and
                current_profile['city'] == profile['city']):
            score += 20

        if score > 0:
            match_data = profile.copy()
            match_data['match_score'] = score
            match_data['common_interests'] = list(common_interests)
            matches.append(match_data)

    # 按匹配分数排序
    matches.sort(key=lambda x: x['match_score'], reverse=True)
    return matches[:max_results]


# 主应用
def main():
    st.title("❤️ 交友互动平台")
    st.markdown("---")

    # 用户未登录时显示登录/注册
    if not st.session_state.current_user:
        show_auth_section()
    else:
        show_main_app()


def show_auth_section():
    """显示认证部分"""
    tab1, tab2 = st.tabs(["登录", "注册"])

    with tab1:
        st.subheader("用户登录")

        with st.form("login_form"):
            username = st.text_input("用户名")
            password = st.text_input("密码", type="password")
            login_btn = st.form_submit_button("登录")

            if login_btn:
                if login_user(username, password):
                    st.success("登录成功！")
                    st.rerun()
                else:
                    st.error("用户名或密码错误")

        st.info("测试账号: demo / password123")

    with tab2:
        st.subheader("用户注册")

        with st.form("register_form"):
            new_username = st.text_input("用户名")
            new_email = st.text_input("邮箱")
            new_password = st.text_input("密码", type="password")
            confirm_password = st.text_input("确认密码", type="password")
            register_btn = st.form_submit_button("注册")

            if register_btn:
                if new_password != confirm_password:
                    st.error("两次输入的密码不一致")
                else:
                    success, message = register_user(new_username, new_email, new_password)
                    if success:
                        st.success(message)
                        st.info("请使用新账号登录")
                    else:
                        st.error(message)


def show_main_app():
    """显示主应用"""
    current_user = st.session_state.current_user
    current_profile = st.session_state.profiles.get(current_user['id'], {})

    # 侧边栏
    with st.sidebar:
        st.header(f"欢迎，{current_profile.get('full_name', current_user['username'])}!")

        if st.button("🚪 退出登录"):
            st.session_state.current_user = None
            st.rerun()

        st.markdown("---")

        # 导航菜单
        menu_options = ["个人资料", "匹配推荐", "附近的人", "虚拟伴侣", "消息中心"]
        selected_menu = st.radio("导航菜单", menu_options)

    # 主内容区
    if selected_menu == "个人资料":
        show_profile_section(current_user, current_profile)
    elif selected_menu == "匹配推荐":
        show_matching_section(current_user)
    elif selected_menu == "附近的人":
        show_nearby_section(current_user)
    elif selected_menu == "虚拟伴侣":
        show_virtual_partner_section(current_user)
    elif selected_menu == "消息中心":
        show_messages_section(current_user)


def show_profile_section(current_user, current_profile):
    """显示个人资料部分"""
    st.header("👤 个人资料")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("基本信息")
        st.write(f"**用户名:** {current_user['username']}")
        st.write(f"**邮箱:** {current_user['email']}")
        st.write(f"**注册时间:** {current_user['created_at'].strftime('%Y-%m-%d')}")

    with col2:
        st.subheader("个人详情")

        with st.form("profile_form"):
            full_name = st.text_input("姓名", value=current_profile.get('full_name', ''))
            age = st.number_input("年龄", min_value=18, max_value=80,
                                  value=current_profile.get('age', 25))
            gender = st.selectbox("性别", ["", "男", "女", "其他"],
                                  index=["", "男", "女", "其他"].index(current_profile.get('gender', '')))
            city = st.text_input("所在城市", value=current_profile.get('city', ''))
            bio = st.text_area("个人简介", value=current_profile.get('bio', ''), height=100)

            interests_options = ["运动", "音乐", "阅读", "旅行", "电影", "美食", "摄影", "游戏",
                                 "编程", "艺术", "科技", "健身", "咖啡", "宠物", "购物"]
            interests = st.multiselect("兴趣爱好", interests_options,
                                       default=current_profile.get('interests', []))

            if st.form_submit_button("更新资料"):
                # 更新个人资料
                st.session_state.profiles[current_user['id']].update({
                    'full_name': full_name,
                    'age': age,
                    'gender': gender,
                    'city': city,
                    'bio': bio,
                    'interests': interests
                })
                st.success("个人资料已更新！")


def show_matching_section(current_user):
    """显示匹配推荐"""
    st.header("💕 匹配推荐")

    matches = find_matches(current_user['id'])

    if not matches:
        st.info("暂无匹配推荐，请完善您的个人资料和兴趣信息")
        return

    for i, match in enumerate(matches):
        with st.container():
            col1, col2, col3 = st.columns([1, 2, 1])

            with col1:
                st.markdown(f"### 👤 {match.get('full_name', '匿名用户')}")
                st.write(f"**年龄:** {match.get('age', '未设置')}")
                st.write(f"**性别:** {match.get('gender', '未设置')}")
                st.write(f"**城市:** {match.get('city', '未设置')}")

            with col2:
                st.write(f"**个人简介:** {match.get('bio', '暂无简介')}")
                if match.get('common_interests'):
                    st.write(f"**共同兴趣:** {', '.join(match['common_interests'])}")
                st.write(f"**匹配度:** {match['match_score']}%")

            with col3:
                if st.button(f"发送消息", key=f"msg_{i}"):
                    st.success(f"消息已发送给 {match.get('full_name', '该用户')}")

                if st.button(f"喜欢", key=f"like_{i}"):
                    st.success(f"已向 {match.get('full_name', '该用户')} 发送喜欢")

            st.markdown("---")


def show_nearby_section(current_user):
    """显示附近的人"""
    st.header("📍 附近的人")

    # 简化版附近的人功能
    current_profile = st.session_state.profiles.get(current_user['id'], {})

    if not current_profile.get('city'):
        st.warning("请先设置您所在的城市")
        return

    nearby_users = []
    for user_id, profile in st.session_state.profiles.items():
        if user_id != current_user['id'] and profile.get('city') == current_profile.get('city'):
            nearby_users.append(profile)

    if not nearby_users:
        st.info(f"在 {current_profile.get('city')} 暂无其他用户")
        return

    for i, user in enumerate(nearby_users):
        with st.container():
            col1, col2 = st.columns([1, 3])

            with col1:
                st.write(f"**{user.get('full_name', '匿名用户')}**")
                st.write(f"年龄: {user.get('age', '未设置')}")
                st.write(f"性别: {user.get('gender', '未设置')}")

            with col2:
                st.write(user.get('bio', '暂无简介'))
                interests = user.get('interests', [])
                if interests:
                    st.write(f"兴趣: {', '.join(interests)}")

            st.markdown("---")


def show_virtual_partner_section(current_user):
    """显示虚拟伴侣功能"""
    st.header("🤖 虚拟伴侣体验")

    st.info("""
    虚拟伴侣功能让您体验与AI伴侣的互动，帮助您：
    - 练习社交技巧
    - 了解自己的情感需求
    - 为真实交友做准备
    """)

    partner_types = {
        "聊天型": "擅长深度对话和情感交流",
        "活泼型": "热情开朗，话题丰富",
        "知性型": "知识渊博，善于思考",
        "温柔型": "体贴细心，善于倾听"
    }

    selected_type = st.selectbox("选择虚拟伴侣类型", list(partner_types.keys()))
    st.write(f"**特点:** {partner_types[selected_type]}")

    if st.button("开始虚拟伴侣体验"):
        st.session_state.virtual_partner = {
            'type': selected_type,
            'start_time': datetime.now(),
            'messages': []
        }
        st.success(f"已启动{selected_type}虚拟伴侣！")

        # 显示聊天界面
        st.subheader("💬 与虚拟伴侣聊天")

        # 初始化消息
        if not st.session_state.virtual_partner['messages']:
            welcome_messages = {
                "聊天型": "你好！我很期待我们的深度交流，你今天想聊些什么呢？",
                "活泼型": "嗨！今天天气真不错呢！你有什么有趣的事情想分享吗？😊",
                "知性型": "您好，很高兴与您交流。最近有阅读什么有趣的书籍吗？",
                "温柔型": "你好呀～希望我能成为你倾诉的对象，今天心情如何呢？"
            }
            st.session_state.virtual_partner['messages'].append({
                'sender': 'partner',
                'text': welcome_messages[selected_type],
                'time': datetime.now()
            })

        # 显示消息历史
        for msg in st.session_state.virtual_partner['messages']:
            if msg['sender'] == 'user':
                st.write(f"**你:** {msg['text']}")
            else:
                st.write(f"**虚拟伴侣:** {msg['text']}")

        # 输入新消息
        user_input = st.text_input("输入消息:", key="chat_input")
        if st.button("发送", key="send_msg"):
            if user_input:
                # 添加用户消息
                st.session_state.virtual_partner['messages'].append({
                    'sender': 'user',
                    'text': user_input,
                    'time': datetime.now()
                })

                # 生成虚拟伴侣回复（简化版）
                responses = {
                    "聊天型": [
                        "这个话题很有意思，能多分享你的想法吗？",
                        "我理解你的感受，这确实是个值得深思的问题。",
                        "从你的话语中我能感受到你的情感，谢谢你的分享。"
                    ],
                    "活泼型": [
                        "哇！这太有趣了！告诉我更多细节吧！🎉",
                        "哈哈，我喜欢这个话题！让我们继续聊下去！",
                        "你真有意思！和你聊天让我很开心！😄"
                    ],
                    "知性型": [
                        "从这个角度看问题很有见地，让我想到...",
                        "根据我的理解，这个问题还可以从多个维度分析。",
                        "你的观点引发了我的一些思考，谢谢分享。"
                    ],
                    "温柔型": [
                        "我明白你的心情，谢谢你愿意和我分享。",
                        "无论遇到什么，我都会在这里倾听和支持你。",
                        "你的感受很重要，我很关心你的想法。"
                    ]
                }

                import random
                response = random.choice(responses[selected_type])
                st.session_state.virtual_partner['messages'].append({
                    'sender': 'partner',
                    'text': response,
                    'time': datetime.now()
                })

                st.rerun()


def show_messages_section(current_user):
    """显示消息中心"""
    st.header("💌 消息中心")

    st.info("""
    这里是您的消息中心，可以：
    - 查看收到的匹配请求
    - 与匹配的用户聊天
    - 管理联系人
    """)

    # 显示匹配请求（简化版）
    st.subheader("匹配请求")
    if st.session_state.matches:
        for match in st.session_state.matches:
            st.write(f"来自 {match['from_user']} 的匹配请求")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("接受", key=f"accept_{match['id']}"):
                    st.success("已接受匹配请求")
            with col2:
                if st.button("拒绝", key=f"reject_{match['id']}"):
                    st.info("已拒绝匹配请求")
    else:
        st.write("暂无新的匹配请求")

    st.subheader("聊天对话")
    st.write("选择左侧的用户开始聊天...")


if __name__ == "__main__":
    main()