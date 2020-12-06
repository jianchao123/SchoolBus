# coding:utf-8
import oss2
import random
from urllib2 import urlopen
import time
import json
import xlrd
from datetime import datetime
from datetime import timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import aliased
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from database.db import db
from database.Order import Order
from utils import defines
from utils import tools
from ext import cache


class OrderService(object):

    @staticmethod
    def order_list(school_id, query_str, order_type,
                   start_date, end_date, page, size):
        db.session.commit()

        offset = (page - 1) * size
        query = db.session.query(Order)
        if school_id:
            query = query.filter(Order.school_id == school_id)
        if order_type:
            query = query.filter(Order.order_type == order_type)
        if query_str:
            query_str = '%{keyword}%'.format(keyword=query_str)
            query = query.filter(or_(Order.stu_name.like(query_str),
                Order.passenger_name.like(query_str)))
        if start_date and end_date:
            end_date = end_date + timedelta(days=1)
            query = query.filter(or_(Order.create_time > start_date,
                                     Order.create_time < end_date))
        count = query.count()
        results = query.offset(offset).limit(size).all()

        data = []
        for row in results:
            data.append({
                'id': row.id,
                'stu_no': row.stu_no,
                'stu_id': row.stu_id,
                'stu_name': row.stu_name,
                'school_id': row.school_id,
                'school_name': row.school_name,
                'order_type': row.order_type,
                'create_time': row.create_time,
                'up_location': row.up_location,
                'gps': row.gps,
                'car_id': row.car_id,
                'license_plate_number': row.license_plate_number,
                'device_id': row.device_id
            })
        return {'results': data, 'count': count}



class UserProfileService(object):
    TOKEN_ID_KEY = 'hash:token.id:{}'
    INVALID_USER_ID = -1
    USER_OPERATIONS = 'user:operations:{}'

    @staticmethod
    def token_to_id(token):
        """
        根据用户token获取用户id

        args:
            token: token字符串

        return:
            int. UserId
        """
        user_id = cache.get(UserProfileService.TOKEN_ID_KEY.format(token))
        return int(user_id) if user_id else UserProfileService.INVALID_USER_ID

    @staticmethod
    def get_user_by_username(username):
        """获取用户"""
        db.session.commit()
        try:
            user = db.session.query(AdminUser). \
                filter(AdminUser.username == username).one()
            return dict(id=user.id, username=user.username,
                        password=user.password)
        except (NoResultFound, MultipleResultsFound):
            pass
        return None

    @staticmethod
    def login(user_id, token):
        cache.set(UserProfileService.TOKEN_ID_KEY.format(token), user_id)
        cache.expire(UserProfileService.TOKEN_ID_KEY.format(token), 60 * 60 * 8)

    @staticmethod
    def modify_pwd(user_id, password_raw):
        """修改密码"""
        db.session.commit()

        try:
            user = db.session.query(AdminUser).filter(
                AdminUser.id == user_id).first()
            user.password = tools.md5_encrypt(password_raw)
            db.session.add(user)
            db.session.commit()
        except:
            db.session.rollback()
        finally:
            db.session.close()
        return True
