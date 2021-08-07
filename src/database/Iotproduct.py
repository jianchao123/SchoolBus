# coding:utf-8
from db import db


class Iotproduct(db.Model):
    __tablename__ = 'iotproduct'

    id = db.Column(db.BigInteger, primary_key=True)
    product_key = db.Column(db.String(16))
    status = db.Column(db.Integer)      # 1启用中 2禁用中
    newdev_secret = db.Column(db.String(128))
    newdev_name = db.Column(db.String(16))
