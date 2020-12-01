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
from database.UserProfile import UserProfile
from database.Station import Station
from database.Face import Face
from database.Department import Department
from database.Enterprise import Enterprise
from database.UserRoleRelation import UserRoleRelation
from database.UserDepartmentRelation import UserDepartmentRelation
from database.Role import Role
from utils import defines
from utils import tools
from ext import cache


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
            user = db.session.query(UserProfile). \
                filter(UserProfile.username == username).one()
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
            user = db.session.query(UserProfile).filter(
                UserProfile.id == user_id).first()
            user.password = tools.md5_encrypt(password_raw)
            db.session.add(user)
            db.session.commit()
        except:
            db.session.rollback()
        finally:
            db.session.close()
        return True
