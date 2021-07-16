# coding:utf-8
from db import db


class Manufacturer(db.Model):
    __tablename__ = 'manufacturer'

    id = db.Column(db.BigInteger, primary_key=True)
    name = db.Column(db.String(16))
    status = db.Column(db.Integer)     # 1启用 2禁用

