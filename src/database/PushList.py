# coding:utf-8
from db import db


class PushList(db.Model):
    __tablename__ = 'push_list'

    id = db.Column(db.BigInteger, primary_key=True)
    stu_id = db.Column(db.Integer)
    stu_no = db.Column(db.String(32))
    school_id = db.Column(db.Integer)
    school_name = db.Column(db.String(16))
    pay_mobile = db.Column(db.String(16))   # 缴费手机号
    nickname = db.Column(db.String(16))     # 昵称
    oss_url = db.Column(db.String(128))     # 头像
    end_date = db.Column(db.Date)           # 截至日期
    status = db.Column(db.Integer)          # 1有效 2过期
