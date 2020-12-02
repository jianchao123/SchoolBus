# coding:utf-8

from db import db


class School(db.Model):
    __tablename__ = 'school'

    id = db.Column(db.BigInteger, primary_key=True)
    school_name = db.Column(db.String(16))
