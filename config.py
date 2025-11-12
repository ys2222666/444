# config.py
import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-12345-change-in-production'

    # 修复数据库URI配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              f"sqlite:///{os.path.join(basedir, 'dating_app.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # 设置为True可以查看SQL语句，调试用