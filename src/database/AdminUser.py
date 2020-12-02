# coding:utf-8

from db import db


class AdminUser(db.Model):
    __tablename__ = 'admin_user'

    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(16))
    passwd = db.Column(db.String(32))
