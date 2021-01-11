# coding:utf-8
import json
import requests
from datetime import datetime
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from database.db import db
from database.Student import Student
from database.AlertInfo import AlertInfo
from database.Worker import Worker
from database.Car import Car
from database.Device import Device
from database.Order import Order
from utils.defines import duty
from ext import conf, cache
from utils import defines


class WxMPService(object):

    @staticmethod
    def get_open_id(code):
        """
        {u'access_token': u'40_LL5e4qeCM_GZwLQykM3M8BM3IXAGrViWuFu6t5RxyW6Dg2mUoWZRZGERWWVjUTNNlTrqSHCdxQELUt7JAoNLoWGcNDMVRt8DcSNDdJDJVvE',
        u'openid': u'opeBzwwl3Z34uyyZtnMIoAfF-qOc', u'expires_in': 7200,
        u'refresh_token': u'40_KJC73GIkm7xsDAYeKteMt-gzhL1Vk3tuCPdSnZS2uKOvhUnqimjb6eUkoAx0Bz1z7z4Va5wfrEE00wOMOhGTpwdLwYL76wbE4MPsrFuwp2A',
        u'scope': u'snsapi_base'}
        """
        url = "https://api.weixin.qq.com/sns/oauth2/access_token?" \
              "appid={}&secret={}&code={}&grant_type=authorization_code"
        res = requests.get(url.format(conf.config['MP_APP_ID'],
                                      conf.config['MP_APP_SECRET'], code))
        d = json.loads(res.content)
        print d
        open_id = d['openid']
        student = db.session.query(Student).filter(
            or_(Student.open_id_1 == open_id,
                Student.open_id_2 == open_id)).first()
        worker = db.session.query(Worker).filter(
            Worker.open_id == open_id).first()
        is_binding = 0
        if student or worker:
            is_binding = 1
        return {'openid': open_id, 'is_binding': is_binding}

    @staticmethod
    def get_role(open_id):
        db.session.commit()
        student = db.session.query(Student).filter(
            or_(Student.open_id_1 == open_id,
                Student.open_id_2 == open_id)).first()
        worker = db.session.query(Worker).filter(
            Worker.open_id == open_id).first()
        d = {
            'parents': 0,
            'driver': 0,
            'zgy': 0
        }
        if student:
            d['parents'] = 1
            d['mobile'] = student.mobile_1 if student.mobile_1 else student.mobile_2
            d['mobile'] = student.mobile_2 if student.mobile_2 else student.mobile_1
        if worker and worker.duty_id == 1:
            d['driver'] = 1
            d['mobile'] = worker.mobile
        if worker and worker.duty_id == 2:
            d['zgy'] = 1
            d['mobile'] = worker.mobile

        return d

    @staticmethod
    def save_mobile(mobile, open_id):
        db.session.commit()
        students = db.session.query(Student).filter(
            or_(Student.mobile_1 == mobile, Student.mobile_2 == mobile)).all()
        workers = db.session.query(Worker).filter(Worker.mobile == mobile).all()
        if not students and not workers:
            return -10
        print students, workers
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
        take_bus_time = order.create_time.strftime('%Y-%m-%d %H:%M:%S')
        d = {
            'id': order.id,
            'gps': order.gps,
            'time': take_bus_time,
            'url': conf.config['REALTIME_FACE_IMG'].format(
                fid=order.fid, timestamp=order.cur_timestamp)
        }
        return d

    @staticmethod
    def alert_info_by_id(periods):
        db.session.commit()

        alert_info = db.session.query(AlertInfo).filter(
            AlertInfo.periods == periods).first()
        d = {}
        if alert_info:
            d = {
                'id': alert_info.id,
                'numbers': alert_info.people_number,
                'alert_info': alert_info.people_info,
                'license_plate_number': alert_info.license_plate_number,
                'time': alert_info.alert_start_time.strftime('%Y-%m-%d %H:%M:%S'),
                'gps': alert_info.gps,
                'worker_info': u'{}(驾驶员);{}(照管员)'.format(
                    alert_info.worker_name_1, alert_info.worker_name_2),
                'status': alert_info.status
            }
        return d

    @staticmethod
    def cancel_alert(open_id, periods, cancel_type_id, cancel_reason):
        db.session.commit()
        # 查询工作人员手机号
        worker = db.session.query(Worker).filter(
            Worker.open_id == open_id).first()
        if not worker:
            return -10  # 跳转到绑定手机号页面

        if worker.status != 1:
            return -11
        alert_info = db.session.query(AlertInfo).filter(
            AlertInfo.periods == periods).first()
        if cancel_type_id == 1:
            alert_info.cancel_reason = cancel_reason
        alert_info.cancel_type_id = cancel_type_id
        alert_info.cancel_time = datetime.now()
        alert_info.cancel_worker_name = worker.nickname
        alert_info.cancel_worker_id = worker.id
        alert_info.status = 2
        try:
            db.session.commit()
            return {'id': alert_info.id}
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def cancel_binding(open_id):
        """解除绑定"""
        db.session.commit()
        student = db.session.query(Student).filter(
            or_(Student.open_id_1 == open_id,
                Student.open_id_2 == open_id)).first()
        worker = db.session.query(Worker).filter(
            Worker.open_id == open_id).first()
        if student:
            student.open_id_1 = None
            student.open_id_2 = None
        if worker:
            worker.open_id = None
        try:
            db.session.commit()
            return {'id': 0}
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def bus_where(open_id):
        """
        校车在那儿
        """
        db.session.commit()

        # 判断身份
        print open_id
        is_parents = db.session.query(Student).filter(
            or_(Student.open_id_1 == open_id,
                Student.open_id_2 == open_id)).first()
        is_staff = db.session.query(Worker).filter(
            Worker.open_id == open_id).first()

        d = {
            'd': -10,
            'nickname': None,
            'order_type': None,
            'create_time': None,
            'license_plate_number': None,
            'gps': None,
            'staff': None,
            'oss_url': None
        }
        print is_staff, is_parents
        if is_parents and is_staff:
            d['d'] = 0
            WxMPService.parents_data(d, open_id)
        elif is_parents:
            d['d'] = 0
            WxMPService.parents_data(d, open_id)
        elif is_staff:
            d['d'] = 0
            WxMPService.staff_data(d, open_id)
        print d
        return d

    @staticmethod
    def staff_data(d, open_id):
        worker = db.session.query(Worker).filter(
            Worker.open_id == open_id).first()
        if worker:
            device = db.session.query(Device).join(
                Car, Car.id == Device.car_id).filter(
                Car.id == worker.car_id).first()
            device_gps = cache.hget(
                defines.RedisKey.DEVICE_CUR_GPS, device.device_name)

            results = db.session.query(Worker).filter(
                Worker.car_id == worker.car_id).all()
            string = ''
            for row in results:
                string += '{} ({} {})|'.format(row.nickname,
                                                duty[row.duty_id],
                                                row.mobile)

            d['gps'] = device_gps
            d['staff'] = string

    @staticmethod
    def parents_data(d, open_id):
        student = db.session.query(Student).filter(
            or_(Student.open_id_1 == open_id,
                Student.open_id_2 == open_id)).first()
        if student:
            # 最近一条数据
            order = db.session.query(Order).filter(
                Order.stu_id == student.id).order_by(
                Order.id.desc()).first()

            if order:
                d['nickname'] = order.stu_name.encode('utf8')
                d['order_type'] = order.order_type
                d['create_time'] = order.create_time.strftime(
                    '%Y-%m-%d %H:%M:%S')

                results = db.session.query(Worker).filter(
                    Worker.car_id == student.car_id).all()
                string = ''
                for row in results:
                    string += '{} ({} {})|'.format(
                        row.nickname, duty[row.duty_id], row.mobile)
                d['staff'] = string
                d['oss_url'] = conf.config['REALTIME_FACE_IMG'].format(
                    fid=order.fid, timestamp=order.cur_timestamp)
                d[
                    'license_plate_number'] = order.license_plate_number.encode(
                    'utf8')
                d['gps'] = order.gps
                d['staff'] = '驾驶员 ({} {}),照管员 ({} {})'.format(
                    order.driver_name, order.driver_mobile, order.zgy_name, order.zgy_mobile)
