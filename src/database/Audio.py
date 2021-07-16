# coding:utf-8
from db import db


class Audio(db.Model):
    __tablename__ = 'audio'

    id = db.Column(db.BigInteger, primary_key=True)
    aac_url = db.Column(db.String(128))
    nickname = db.Column(db.String(32))
    stu_no = db.Column(db.String(32))
    status = db.Column(db.Integer)  # 1等待生成 2生成中 3生成成功 4生成失败
    face_id = db.Column(db.Integer)



