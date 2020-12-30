# coding:utf-8

from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound
from database.AdminUser import AdminUser
from utils import tools
from ext import cache1
from database.db import db


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
        user_id = cache1.get(UserProfileService.TOKEN_ID_KEY.format(token))
        return int(user_id) if user_id else UserProfileService.INVALID_USER_ID

    @staticmethod
    def get_user_by_username(username):
        """获取用户"""

        db.session.commit()
        try:
            user = db.session.query(AdminUser). \
                filter(AdminUser.username == username).one()
            return dict(id=user.id, username=user.username,
                        passwd=user.passwd)
        except (NoResultFound, MultipleResultsFound):
            pass
        return None

    @staticmethod
    def login(user_id, token):
        cache1.set(UserProfileService.TOKEN_ID_KEY.format(token), user_id)
        cache1.expire(UserProfileService.TOKEN_ID_KEY.format(token), 60 * 60 * 8)

    @staticmethod
    def modify_pwd(user_id, passwd_raw):
        """修改密码"""
        db.session.commit()

        try:
            user = db.session.query(AdminUser).filter(
                AdminUser.id == user_id).first()
            user.passwd = tools.md5_encrypt(passwd_raw)
            db.session.add(user)
            db.session.commit()
        except:
            db.session.rollback()
        finally:
            db.session.close()
        return True
