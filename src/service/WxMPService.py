# coding:utf-8
import json
import requests
from datetime import datetime
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from database.db import db
from database.Student import Student
from database.Order import Order
from database.AlertInfo import AlertInfo
from database.Worker import Worker
from database.Car import Car
from ext import conf


class WxMPService(object):

    @staticmethod
    def save_mobile(mobile, code):
        db.session.commit()
        students = db.session.query(Student).filter(
            or_(Student.mobile_1 == mobile, Student.mobile_2 == mobile)).all()
        workers = db.session.query(Worker).filter(Worker.mobile == mobile).all()
        if not students and not workers:
            return -10

        url = "https://api.weixin.qq.com/sns/oauth2/access_token?" \
              "appid={}&secret={}&code={}&grant_type=authorization_code"
        res = requests.get(url.format(conf.config['MP_APP_ID'],
                                      conf.config['MP_APP_SECRET'], code))
        d = json.loads(res.content)
        open_id = d['open_id']
        # 保存到学生的家长字段
        for row in students:
            if row.mobile_1 == mobile:
                row.open_id_1 = open_id
            if row.mobile_2 == mobile:
                row.open_id_2 = open_id
        # 保存到工作人员
        for row in workers:
            row.open_id = open_id

        try:
            db.session.commit()
            return {'open_id': open_id}
        except SQLAlchemyError:
            import traceback
            print traceback.format_exc()
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def get_order_by_id(order_id):
        db.session.commit()

        order = db.session.query(Order).filter(
            Order.id == order_id).first()
        take_bus_time = datetime.fromtimestamp(
            order.cur_timestamp).strftime('%Y-%m-%d %H:%M:%S')
        d = {
            'id': order.id,
            'gps': order.gps,
            'time': take_bus_time,
            'url': conf.config['REALTIME_FACE_IMG'].format(
                order.fid, order.cur_timestamp)
        }
        return d

    @staticmethod
    def alert_info_by_id(alert_info_id):
        db.session.commit()

        alert_info = db.session.query(AlertInfo).filter(
            AlertInfo.id == alert_info_id).first()
        d = {
            'id': alert_info.id,
            'numbers': alert_info.people_number,
            'alert_info': alert_info.people_info,
            'license_plate_number': alert_info.license_plate_number,
            'time': alert_info.alert_start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'gps': alert_info.gps,
            'worker_info': '{}({})'.format(alert_info.worker_name_1,
                                           alert_info.worker_name_2)
        }
        return d

    @staticmethod
    def cancel_alert(open_id, alert_info_id, cancel_type_id, cancel_reason):
        db.session.commit()
        # 查询工作人员手机号
        worker = db.session.query(Worker).filter(
            Worker.open_id == open_id).first()
        if not worker:
            return -10  # 跳转到绑定手机号页面

        alert_info = db.session.query(AlertInfo).filter(
            AlertInfo.id == alert_info_id).first()
        if cancel_type_id == 1:
            alert_info.cancel_reason = cancel_reason
        alert_info.cancel_type_id = cancel_type_id
        alert_info.cancel_time = datetime.now()
        alert_info.cancel_worker_name = worker.nickname
        alert_info.cancel_worker_id = worker.id
        try:
            db.session.commit()
            return {'id': alert_info.id}
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def bus_where(open_id):
        db.session.commit()
        student = db.session.query(Student).filter(
            or_(Student.open_id_1 == open_id,
                Student.open_id_2 == open_id)).first()
        worker = db.session.query(Worker).filter(
            Worker.open_id == open_id).first()
        if not student and not worker:
            return -10  # 跳转到绑定手机号页面
        db.session.query(Car).filter(Car)
