# coding:utf-8
from datetime import datetime
from db import db


class AlertInfo(db.Model):
    __tablename__ = 'alert_info'

    id = db.Column(db.BigInteger, primary_key=True)
    car_id = db.Column(db.Integer)
    license_plate_number = db.Column(db.String(16)) # 车牌
    worker_id_1 = db.Column(db.Integer)         # 驾驶员
    worker_name_1 = db.Column(db.String(16))
    worker_id_2 = db.Column(db.Integer)         # 照管员
    worker_name_2 = db.Column(db.String(16))
    company_name = db.Column(db.String(16))     # 工作人员公司名字
    people_number = db.Column(db.Integer)       # 报警人员数量
    people_info = db.Column(db.String(128))     # 报警人员信息
    first_alert = db.Column(db.Integer)     # 第一次报警 1是 0否
    second_alert = db.Column(db.Integer)    # 第二次报警 1是 0否
    alert_start_time = db.Column(db.DateTime, default=datetime.now) # 报警开始时间
    alert_location = db.Column(db.String(16))   # 报警定位
    status = db.Column(db.Integer)          # 1 正在报警 2已解除
    cancel_info = db.Column(db.String(128)) # 取消报警相关信息
