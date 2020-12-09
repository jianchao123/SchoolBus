# coding:utf-8
from datetime import datetime
from db import db


class ExportTask(db.Model):
    __tablename__ = 'export_task'

    id = db.Column(db.BigInteger, primary_key=True)
    status = db.Column(db.Integer)                # 1:处理中 2:已完成 10:删除
    task_name = db.Column(db.String(256))
    zip_url = db.Column(db.String(256))
    task_type = db.Column(db.Integer)             # 1 乘车记录 2 报警记录
    create_time = db.Column(db.DateTime, default=datetime.now)
