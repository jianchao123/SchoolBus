# coding:utf-8
from db import db


class Feature(db.Model):
    __tablename__ = 'feature'

    id = db.Column(db.BigInteger, primary_key=True)
    oss_url = db.Column(db.String(128))
    feature = db.Column(db.Text())
    feature_crc = db.Column(db.Numeric(11, 6))
    mfr_id = db.Column(db.Integer)
    face_id = db.Column(db.Integer)
    status = db.Column(db.Integer)      # -1未绑定人脸 1等待生成 2生成中 3生成成功 4生成失败



