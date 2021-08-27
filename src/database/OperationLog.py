# coding:utf-8
from db import db
from datetime import datetime


class OperationLog(db.Model):
    __tablename__ = 'operation_log'

    id = db.Column(db.BigInteger, primary_key=True)
    create_time = db.Column(db.DateTime, default=datetime.now)
    username = db.Column(db.String(16))
    func_name = db.Column(db.String(32))
    func_param = db.Column(db.String(256))


