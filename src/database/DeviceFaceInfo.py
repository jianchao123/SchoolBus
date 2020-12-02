# coding:utf-8

from db import db


class DeviceFaceInfo(db.Model):
    __tablename__ = 'device_face_info'

    id = db.Column(db.BigInteger, primary_key=True)
    device_id = db.Column(db.Integer)
    info_str = db.Column(db.Text()) # 设备上人员信息
