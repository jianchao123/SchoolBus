# coding:utf-8

from db import db


class Car(db.Model):
    __tablename__ = 'school'

    id = db.Column(db.BigInteger, primary_key=True)
    code = db.Column(db.String(16))
    license_plate_number = db.Column(db.String(16))
    capacity = db.Column(db.Integer)
    device_iid = db.Column(db.String(16))
    worker_str = db.Column(db.String(32))   # 该车辆的工作人员信息
    company_name = db.Column(db.String(16))
