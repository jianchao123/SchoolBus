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
    first_alert = db.Column(db.Integer)         # 第一次报警 1是 0否
    second_alert = db.Column(db.Integer)        # 第二次报警 1是 0否
    alert_start_time = db.Column(db.DateTime, default=datetime.now) # 报警开始时间
    alert_second_time = db.Column(db.DateTime, default=datetime.now)
    alert_location = db.Column(db.String(16))   # 报警定位
    status = db.Column(db.Integer)              # 1 正在报警 2已解除 10删除
    cancel_worker_id = db.Column(db.Integer)    # 取消的工作人员id
    cancel_worker_name = db.Column(db.String(16))   # 工作人员名字
    cancel_type_id = db.Column(db.Integer)      # 取消类型 1其他 2无学生遗漏 3有学生遗漏
    cancel_time = db.Column(db.DateTime)        # 取消时间
    cancel_reason = db.Column(db.Integer)       # cancel_type_id=1时需要此项
    gps = db.Column(db.String(32))
    periods = db.Column(db.String(48))
    stu_ids = db.Column(db.String(32))