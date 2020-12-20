# coding:utf-8
import json
import requests
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from database.db import db
from database.Student import Student
from ext import conf


class WxCallbackService(object):

    @staticmethod
    def save_mobile(mobile, code):
        db.session.commit()
        students = db.session.query(Student).filter(
            or_(Student.mobile_1 == mobile, Student.mobile_2 == mobile)).all()
        if not students:
            return -10  # 没有找到学生

        url = "https://api.weixin.qq.com/sns/oauth2/access_token?" \
              "appid={}&secret={}&code={}&grant_type=authorization_code"
        res = requests.get(url.format(conf.config['MP_APP_ID'],
                                      conf.config['MP_APP_SECRET'], code))
        d = json.loads(res.content)
        open_id = d['open_id']
        for row in students:
            if row.mobile_1 == mobile:
                row.open_id_1 = open_id
            if row.mobile_2 == mobile:
                row.open_id_2 = open_id
        try:
            db.session.commit()
            return {'id': 1}
        except SQLAlchemyError:
            import traceback
            print traceback.format_exc()
            db.session.rollback()
            return -2
        finally:
            db.session.close()