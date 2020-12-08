# coding:utf-8
from datetime import datetime
from db import db


class Student(db.Model):
    __tablename__ = 'student'

    id = db.Column(db.BigInteger, primary_key=True)
    stu_no = db.Column(db.String(16))   # 身证号
    nickname = db.Column(db.String(16))
    gender = db.Column(db.Integer)
    parents_1 = db.Column(db.String(16))
    mobile_1 = db.Column(db.String(16))
    parents_2 = db.Column(db.String(16))
    mobile_2 = db.Column(db.String(16))
    address = db.Column(db.String(32))
    remarks = db.Column(db.String(32))
    school_id = db.Column(db.Integer)
    grade_id = db.Column(db.Integer)    # 前端硬编码
    class_id = db.Column(db.Integer)    # 前端硬编码
    create_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    car_id = db.Column(db.Integer)      # 车辆id
    license_plate_number = db.Column(db.String(16))
    status = db.Column(db.Integer)      # 状态 1有效 10删除