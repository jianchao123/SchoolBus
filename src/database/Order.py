# coding:utf-8
from datetime import datetime
from db import db


class Order(db.Model):
    __tablename__ = 'order'

    id = db.Column(db.BigInteger, primary_key=True)
    stu_no = db.Column(db.String(32))   # 身份证
    stu_id = db.Column(db.Integer)      # 学生id
    stu_name = db.Column(db.String(16)) # 学生名字
    school_id = db.Column(db.Integer)   # 学校id
    school_name = db.Column(db.String(16))
    order_type = db.Column(db.Integer)  # 订单类型 1 上学上车 2上学下车 3 放学上车 4 放学下车
    create_time = db.Column(db.DateTime, default=datetime.now)
    up_location = db.Column(db.String(64))  # 位置
    gps = db.Column(db.String(32))      # 经纬度 逗号分割
    car_id = db.Column(db.Integer)      # 车辆Id
    license_plate_number = db.Column(db.String(16)) # 车牌
    device_id = db.Column(db.Integer)
    fid = db.Column(db.Integer)
    cur_timestamp = db.Column(db.String(16))

