# coding:utf-8
from db import db


class Worker(db.Model):
    __tablename__ = 'worker'

    id = db.Column(db.BigInteger, primary_key=True)
    emp_no = db.Column(db.String(16))
    nickname = db.Column(db.String(16))
    gender = db.Column(db.Integer)  # 1男 2女
    mobile = db.Column(db.String(16))
    remarks = db.Column(db.String(16))
    company_name = db.Column(db.String(16))
    department_name = db.Column(db.String(16))
    duty_id = db.Column(db.Integer)     # 职务id  1驾驶员 2照管员
    car_id = db.Column(db.Integer)
    license_plate_number = db.Column(db.String(16))
    status = db.Column(db.Integer)      # 1有效 10删除
    open_id = db.Column(db.String(32))
