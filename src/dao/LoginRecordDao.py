# coding:utf-8
from database.db import db


class LoginRecordDao(object):

    @staticmethod
    def insert_login_record(user_id, token, duration,
                            start_timestamp, end_timestamp):
        cursor = None
        try:
            sql = "INSERT INTO `login_record`(`login_time`,`user_id`,`token`," \
                  "`start_timestamp`,`duration`,`end_timestamp`) " \
                  "VALUES(now(),:user_id,:token,:start_timestamp," \
                  ":duration,:end_timestamp)"
            params = {"user_id": user_id, "token": token,
                      "start_timestamp": start_timestamp,
                      "duration": duration, "end_timestamp": end_timestamp}
            cursor = db.session.execute(sql, params=params)
            db.session.commit()
            return cursor.lastrowid
        except:
            db.session.rollback()
            return -2
        finally:
            if cursor:
                cursor.close()
            db.session.close()
