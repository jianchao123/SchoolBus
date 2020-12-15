# coding:utf-8
from db import db


class Device(db.Model):
    __tablename__ = 'device'

    id = db.Column(db.BigInteger, primary_key=True)
    device_name = db.Column(db.String(16))
    mac = db.Column(db.String(128))
    product_key = db.Column(db.String(128))
    device_secret = db.Column(db.String(128))
    version_no = db.Column(db.String(32))
    device_iid = db.Column(db.String(16))
    is_open = db.Column(db.Integer)     # 是否开机 1是 0否
    imei = db.Column(db.String(32))
    car_id = db.Column(db.Integer)      # 车辆id
    license_plate_number = db.Column(db.String(16))
    status = db.Column(db.Integer)      # 1已创建虚拟设备 2已关联车辆 3已设置工作模式 4已设置oss信息 5已初始化人员
    sound_volume = db.Column(db.Integer)
    device_type = db.Column(db.Integer)  # 1刷脸 2生成特征值