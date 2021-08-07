# coding:utf-8
from db import db


class Machine(db.Model):
    __tablename__ = 'machine'

    id = db.Column(db.BigInteger, primary_key=True)
    mac = db.Column(db.String(128))
    product_id = db.Column(db.Integer)
    product_key = db.Column(db.String(128))
    device_iid = db.Column(db.String(16))
