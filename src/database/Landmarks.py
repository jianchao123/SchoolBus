# coding:utf-8

from db import db


class Landmarks(db.Model):
    __tablename__ = 'landmarks'

    id = db.Column(db.BigInteger, primary_key=True)
    lng = db.Column(db.Numeric(11, 6))  # 经
    lat = db.Column(db.Numeric(11, 6))  # 纬
    address = db.Column(db.BigInteger, primary_key=True)


