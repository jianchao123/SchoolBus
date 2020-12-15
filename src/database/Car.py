# coding:utf-8

from db import db


class Car(db.Model):
    __tablename__ = 'car'

    id = db.Column(db.BigInteger, primary_key=True)
    code = db.Column(db.String(16))
    license_plate_number = db.Column(db.String(16))
    capacity = db.Column(db.Integer)
    device_iid = db.Column(db.String(16))
    worker_1_id = db.Column(db.Integer)
    worker_1_nickname = db.Column(db.String(32))
    worker_1_duty_name = db.Column(db.Integer)
    worker_2_id = db.Column(db.Integer)
    worker_2_nickname = db.Column(db.String(32))
    worker_2_duty_name = db.Column(db.Integer)
    company_name = db.Column(db.String(16))     # 车辆所属公司
    status = db.Column(db.Integer)              # 1有效
