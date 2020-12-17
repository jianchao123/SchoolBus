# coding:utf-8
import xlrd
import time
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from database.db import db
from database.Car import Car
from database.Device import Device
from utils import defines
from msgqueue import producer
from ext import cache


class CarService(object):

    @staticmethod
    def car_list(query_str, device_status, page, size):
        db.session.commit()
        print query_str, device_status, page, size
        offset = (page - 1) * size
        query = db.session.query(Car)
        if query_str:
            query_str = '%{keyword}%'.format(keyword=query_str)

            results = db.session.query(Device).filter(
                Device.device_iid.like(query_str)).all()
            car_ids = [row.car_id for row in results]

            query = query.filter(or_(
                Car.id.in_(car_ids), Car.license_plate_number.like(query_str)))
        if device_status:
            results = db.session.query(Device).filter(
                Device.status == device_status).all()
            car_ids = [row.car_id for row in results]
            query = query.filter(Car.id.in_(car_ids))
        count = query.count()
        results = query.order_by(Car.id.desc()).offset(offset).limit(size).all()

        now = int(time.time())
        data = []
        for row in results:
            is_online = u"未绑定设备"
            device = db.session.query(Device).filter(
                Device.car_id == row.id).first()
            if device:
                device_timestamp = cache.hget(
                    defines.RedisKey.DEVICE_CUR_TIMESTAMP, device.device_name)
                if not device_timestamp or (now - int(device_timestamp) > 30):
                    is_online = u"离线"
                else:
                    is_online = u"在线"

            data.append({
                'id': row.id,
                'code': row.code,
                'license_plate_number': row.license_plate_number,
                'capacity': row.capacity,
                'device_iid': row.device_iid,
                'worker_1_id': row.worker_1_id,
                'worker_1_nickname': row.worker_1_nickname,
                'worker_1_duty_name': row.worker_1_duty_name,
                'worker_2_id': row.worker_2_id,
                'worker_2_nickname': row.worker_2_nickname,
                'worker_2_duty_name': row.worker_2_duty_name,
                'company_name': row.company_name,
                'status': row.status,
                'is_online': is_online
            })
        return {'results': data, 'count': count}

    @staticmethod
    def car_add(license_plate_number, capacity, company_name):
        """
        车辆编码 车牌号 载客量 公司

        """
        car = db.session.query(Car).filter(
            Car.license_plate_number == license_plate_number).first()
        if car:
            return -10  # 车牌已经存在

        car = Car()
        car.code = str(datetime.now().strftime('%Y%m%d%H%M%S%f'))
        car.license_plate_number = license_plate_number
        car.capacity = capacity
        car.device_iid = ''
        car.company_name = company_name
        car.status = 1   # 有效

        try:
            db.session.add(car)
            new_id = car.id
            db.session.commit()
            return {'id': new_id}
        except SQLAlchemyError:
            import traceback
            print traceback.format_exc()
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def car_update(pk, license_plate_number, capacity, company_name):
        """

        """
        car = db.session.query(Car).filter(
            Car.id == pk).first()
        if not car:
            return -1
        if license_plate_number:
            cnt = db.session.query(Car).filter(
                Car.id != pk,
                Car.license_plate_number == license_plate_number).count()
            if cnt:
                return -10  # 车牌已经存在
            # 是否绑定设备
            device = db.session.query(Device).filter(
                Device.car_id == car.id).first()
            if device:
                producer.update_chepai(device.device_name,
                                       device.license_plate_number,
                                       device.sound_volume)

        if company_name:
            car.company_name = company_name
        if capacity:
            car.capacity = capacity
        try:
            d = {'id': car.id}
            db.session.commit()
            return d
        except SQLAlchemyError:
            db.session.rollback()
            return -2
        finally:
            db.session.close()

    @staticmethod
    def batch_add_car(excel_file):
        """
        车牌 载客量 公司
        """
        db.session.commit()

        data = xlrd.open_workbook(file_contents=excel_file.read())
        table = data.sheet_by_index(0)

        if table.nrows > 10000:
            return {"c": 1, "msg": u"excel数据最大10000条"}

        chepai_list = []
        results = db.session.query(Car).filter(Car.status == 1).all()
        for row in results:
            chepai_list.append(row.license_plate_number)

        # 查询所有车辆
        car_dict = {}
        results = db.session.query(Car).all()
        for row in results:
            car_dict[row.license_plate_number] = row.id

        error_msg_list = []
        for index in range(1, table.nrows):
            is_err = 0

            row_data = table.row_values(index)
            license_plate_number = str(row_data[0]).strip()
            capacity = str(row_data[1]).strip()
            company_name = str(row_data[2]).strip()

            err_str = u"\n第{}行,".format(index + 1)
            # 先检查是否为空
            if not capacity:
                err_str += u"载客量为空,"
                is_err = 1
            if not company_name:
                err_str += u"公司名字为空,"
                is_err = 1
            if not license_plate_number:
                err_str += u"车牌号为空,"
                is_err = 1

            # 检查重复
            if license_plate_number in chepai_list:
                err_str += u"车牌{}重复".format(license_plate_number)
                is_err = 1
            else:
                chepai_list.append(license_plate_number)

            if err_str:
                err_str += "\n"

            if is_err:
                error_msg_list.append(err_str)
        if error_msg_list:
            return {"c": 1, "msg": "\n".join(error_msg_list)}

        if cache.get('batch_add_car'):
            return -10  # 导入车辆执行中

        cache.set('batch_add_car', 1)
        cache.expire('batch_add_car', 50)

        car_list = []
        for index in range(1, table.nrows):
            row_data = table.row_values(index)
            print row_data[1], type(row_data[1])
            license_plate_number = str(row_data[0]).strip()
            capacity = str(int(row_data[1])).strip()
            company_name = str(row_data[2]).strip()

            l = [license_plate_number, capacity, company_name]
            car_list.append(l)
        # 发送消息
        print car_list
        start = 0
        end = 1000
        send_list = car_list[start: end]
        while send_list:
            producer.batch_add_car(send_list)
            send_list = car_list[start + 1000: end + 1000]
        return {"c": 0, 'msg': ''}
