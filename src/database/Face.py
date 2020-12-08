# coding:utf-8
from datetime import datetime
from db import db


class Face(db.Model):
    __tablename__ = 'face'

    id = db.Column(db.BigInteger, primary_key=True)
    oss_url = db.Column(db.String(128))
    status = db.Column(db.Integer)          # 1没有人脸 2未处理 3处理中 4有效(处理完成) 5生成feature失败 6过期 10删除
    feature = db.Column(db.Text())
    nickname = db.Column(db.String(16))
    stu_id = db.Column(db.Integer)
    stu_no = db.Column(db.String(16))
    feature_crc = db.Column(db.Numeric(11, 6))
    update_time = db.Column(db.DateTime, default=datetime.now)
    acc_url = db.Column(db.String(128))
    end_timestamp = db.Column(db.String(16)) # 截至日期时间戳
